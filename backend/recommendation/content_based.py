"""
==============================================================================
Content-Based Recommendation Engine
==============================================================================
Purpose:
    Recommends similar products based on PRODUCT ATTRIBUTES (features),
    not user behaviour.  When a customer looks at a Cotton Veshti from
    Ramraj Cotton, this engine finds other products that share similar
    Category, Fabric, Brand, Gender, etc.

How it works (high-level):
    1.  Combine multiple text attributes into ONE feature string per product.
    2.  Convert those strings into numerical vectors using TF-IDF.
    3.  Measure the "angle" between every pair of vectors using Cosine
        Similarity — products pointing in the same direction are similar.
    4.  For any product, return the Top-N most similar products.

Real-world usage:
    Amazon  → "Products related to this item"
    Myntra  → "Similar products you may like"
    Netflix → "Because you watched X"

ML Concepts used:
    • TF-IDF Vectorizer  (Term Frequency – Inverse Document Frequency)
    • Cosine Similarity   (Angular distance between vectors)
==============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import os
import sys
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# =============================================================================
# PATH SETUP  —  ensures relative paths work from any working directory
# =============================================================================
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =============================================================================
# CONSTANTS
# =============================================================================
# Input
PRODUCTS_FILE: str = os.path.join(PROJECT_ROOT, "data", "processed", "products_clean.csv")

# Output  —  pre-computed similarity matrix saved here for fast loading
MODELS_DIR: str = os.path.join(PROJECT_ROOT, "backend", "models")
SIMILARITY_MATRIX_FILE: str = os.path.join(MODELS_DIR, "content_similarity_matrix.pkl")
TFIDF_MATRIX_FILE: str = os.path.join(MODELS_DIR, "tfidf_matrix.pkl")
PRODUCT_INDEX_FILE: str = os.path.join(MODELS_DIR, "product_index_map.pkl")

# Feature columns used to describe each product
# These are the TEXT attributes that define "what a product IS"
FEATURE_COLUMNS: List[str] = [
    "Category",
    "SubCategory",
    "Brand",
    "Fabric",
    "Color",
    "Gender",
    "SeasonalDemandTag",
]

# Price is numeric, so we convert it into a categorical "PriceRange" bin
# before merging with the text features.
PRICE_BINS: List[int] = [0, 500, 1000, 2000, 5000, 10000, 50000]
PRICE_LABELS: List[str] = [
    "Budget",
    "Economy",
    "Standard",
    "Premium",
    "Luxury",
    "Ultra-Luxury",
]

# TF-IDF hyper-parameters
# -----------------------------------------------------------------------
# max_features : cap vocabulary size to avoid memory blow-up on large
#                catalogues.  500 products × ~8 features → small vocab,
#                so 5000 is generous headroom.
# ngram_range  : (1, 2) captures both single words ("Cotton") and
#                bigrams ("Ramraj Cotton"), giving richer signal.
# stop_words   : removes English filler words ("the", "and", "of").
# -----------------------------------------------------------------------
MAX_FEATURES: int = 5000
NGRAM_RANGE: Tuple[int, int] = (1, 2)

# Default number of similar products to return
DEFAULT_TOP_N: int = 10

# =============================================================================
# LOGGING
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# =============================================================================
# FUNCTION 1: load_products()
# =============================================================================
def load_products(file_path: str = PRODUCTS_FILE) -> pd.DataFrame:
    """
    Load the cleaned products dataset.

    Parameters
    ----------
    file_path : str
        Absolute path to products_clean.csv.

    Returns
    -------
    pd.DataFrame
        Products table with all cleaned columns.

    Raises
    ------
    FileNotFoundError
        If the processed products file does not exist.
    """
    if not os.path.exists(file_path):
        logger.error(f"Products file not found: {file_path}")
        raise FileNotFoundError(f"Products file not found: {file_path}")

    df = pd.read_csv(file_path)
    logger.info(
        f"Loaded products: {df.shape[0]} rows × {df.shape[1]} columns"
    )
    return df


# =============================================================================
# FUNCTION 2: create_price_range()
# =============================================================================
def create_price_range(
    df: pd.DataFrame,
    bins: List[int] = PRICE_BINS,
    labels: List[str] = PRICE_LABELS,
) -> pd.DataFrame:
    """
    Convert the numeric Price column into a categorical PriceRange.

    Why?
    ----
    TF-IDF works on TEXT, not numbers.  A price of ₹1,500 is meaningless
    as a word, but "Standard" tells the model this product is mid-range.
    Binning converts continuous values into discrete categories that
    TF-IDF can handle.

    Parameters
    ----------
    df : pd.DataFrame
        Products dataframe with a 'Price' column.
    bins : List[int]
        Bin edges for pd.cut().
    labels : List[str]
        Human-readable label for each bin.

    Returns
    -------
    pd.DataFrame
        Same dataframe with a new 'PriceRange' column added.
    """
    df = df.copy()
    df["PriceRange"] = pd.cut(
        df["Price"], bins=bins, labels=labels, include_lowest=True
    )
    # pd.cut returns a Categorical; convert to str for TF-IDF
    df["PriceRange"] = df["PriceRange"].astype(str)
    logger.info("Created PriceRange column from Price bins")
    return df


# =============================================================================
# FUNCTION 3: build_feature_string()
# =============================================================================
def build_feature_string(
    df: pd.DataFrame,
    feature_cols: List[str] = FEATURE_COLUMNS,
) -> pd.Series:
    """
    Combine multiple text columns into ONE string per product.

    Example output for row 0:
        "Men Veshti Ramraj_Cotton Cotton Purple Men Pongal_Temple_Festival_Summer Standard"

    Why combine?
    ------------
    TF-IDF expects a single "document" per row.  By concatenating all
    relevant attributes, we create a mini-document that fully describes
    the product.  The TF-IDF vectorizer then converts this document into
    a numerical vector.

    Preprocessing steps:
    - fillna("Unknown")  →  avoid NaN breaking string concatenation
    - str.strip()        →  remove stray whitespace
    - replace spaces with underscores in multi-word values so that
      "Ramraj Cotton" becomes "Ramraj_Cotton" (treated as ONE token,
      not two separate words)

    Parameters
    ----------
    df : pd.DataFrame
        Products dataframe.
    feature_cols : List[str]
        Columns to concatenate.

    Returns
    -------
    pd.Series
        One combined string per product.
    """
    # Include PriceRange if it exists
    cols = feature_cols + (["PriceRange"] if "PriceRange" in df.columns else [])

    parts: List[pd.Series] = []
    for col in cols:
        if col in df.columns:
            # fillna → strip → underscores for multi-word tokens
            cleaned = (
                df[col]
                .fillna("Unknown")
                .astype(str)
                .str.strip()
                .str.replace(r"\s+", "_", regex=True)
            )
            parts.append(cleaned)
        else:
            logger.warning(f"Feature column '{col}' not found — skipping")

    # Join all parts with a single space separator
    combined = parts[0]
    for part in parts[1:]:
        combined = combined + " " + part

    logger.info(
        f"Built feature strings from {len(cols)} columns "
        f"(sample: '{combined.iloc[0][:80]}…')"
    )
    return combined


# =============================================================================
# FUNCTION 4: build_tfidf_matrix()
# =============================================================================
def build_tfidf_matrix(
    feature_strings: pd.Series,
    max_features: int = MAX_FEATURES,
    ngram_range: Tuple[int, int] = NGRAM_RANGE,
) -> Tuple[np.ndarray, TfidfVectorizer]:
    """
    Convert feature strings into a TF-IDF matrix.

    What is TF-IDF?
    ----------------
    Term Frequency–Inverse Document Frequency.

    • TF (Term Frequency):
      How often a word appears in THIS product's description.
      TF("Cotton", product_0) = count("Cotton" in product_0) / total_words_in_product_0

    • IDF (Inverse Document Frequency):
      How RARE a word is across ALL products.
      IDF("Cotton") = log(total_products / products_containing_"Cotton")

      Common words (e.g. "Men") get LOW IDF → less weight.
      Rare words (e.g. "Kanchipuram_Handloom") get HIGH IDF → more weight.

    • TF-IDF = TF × IDF
      A word is important if it appears often in ONE product (high TF)
      but rarely across ALL products (high IDF).

    Why TF-IDF and not simple one-hot encoding?
    --------------------------------------------
    One-hot treats every word equally.  TF-IDF gives MORE weight to
    distinctive words that differentiate products.  "Cotton" appears in
    many products (low IDF, low weight), but "Kanchipuram_Handloom"
    appears in few products (high IDF, high weight).

    Parameters
    ----------
    feature_strings : pd.Series
        Combined text feature per product.
    max_features : int
        Maximum vocabulary size.
    ngram_range : Tuple[int, int]
        (min_n, max_n) for n-gram extraction.

    Returns
    -------
    Tuple[np.ndarray, TfidfVectorizer]
        - Dense TF-IDF matrix of shape (n_products, n_features).
        - Fitted vectorizer (needed if we want to transform new products later).
    """
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        stop_words="english",
        # sublinear_tf=True applies 1 + log(TF) instead of raw TF.
        # This dampens the effect of a word appearing many times in
        # one product — prevents one attribute from dominating.
        sublinear_tf=True,
    )

    tfidf_matrix = vectorizer.fit_transform(feature_strings)
    logger.info(
        f"TF-IDF matrix: {tfidf_matrix.shape[0]} products × "
        f"{tfidf_matrix.shape[1]} features"
    )
    return tfidf_matrix, vectorizer


# =============================================================================
# FUNCTION 5: compute_similarity_matrix()
# =============================================================================
def compute_similarity_matrix(tfidf_matrix) -> np.ndarray:
    """
    Compute pairwise cosine similarity between ALL products.

    What is Cosine Similarity?
    --------------------------
    It measures the ANGLE between two vectors, ignoring their magnitude.

    Formula:
        cos(A, B) = (A · B) / (‖A‖ × ‖B‖)

    • Result is between 0 and 1 (for non-negative TF-IDF vectors).
    • 1.0 = vectors point in the same direction = identical features.
    • 0.0 = vectors are orthogonal = no features in common.

    Why cosine and not Euclidean distance?
    ---------------------------------------
    Euclidean distance is affected by the MAGNITUDE of vectors.
    If product A has a longer description than product B, Euclidean
    distance would say they're "far apart" even if their features
    are identical.  Cosine similarity only cares about the DIRECTION,
    making it robust to document length differences.

    Time complexity:
        O(n² × d)  where n = number of products, d = number of features.
        For 500 products × 500 features ≈ 125 million operations.
        In practice, this takes < 1 second because scikit-learn uses
        optimized BLAS routines under the hood.

    Space complexity:
        O(n²) for the similarity matrix.
        500 × 500 = 250,000 floats ≈ 2 MB.  Trivial.

    Parameters
    ----------
    tfidf_matrix : sparse matrix or np.ndarray
        TF-IDF matrix of shape (n_products, n_features).

    Returns
    -------
    np.ndarray
        Square similarity matrix of shape (n_products, n_products).
    """
    similarity = cosine_similarity(tfidf_matrix, tfidf_matrix)
    logger.info(
        f"Cosine similarity matrix: {similarity.shape[0]} × {similarity.shape[1]}"
    )
    return similarity


# =============================================================================
# FUNCTION 6: save_model_artifacts()
# =============================================================================
def save_model_artifacts(
    similarity_matrix: np.ndarray,
    tfidf_matrix,
    product_id_to_index: Dict[str, int],
    index_to_product_id: Dict[int, str],
) -> None:
    """
    Save pre-computed artifacts to disk so the API doesn't have to
    recompute them on every request.

    What is saved:
        1. Cosine similarity matrix   → instant Top-N lookups
        2. TF-IDF matrix              → for future new-product scoring
        3. ProductID ↔ index mapping   → translate between IDs and matrix rows

    Why pickle?
    -----------
    pickle serialises Python objects to binary.  It's fast, compact,
    and preserves numpy arrays / sparse matrices exactly.  For production,
    you might use joblib (better compression for large arrays).
    """
    os.makedirs(MODELS_DIR, exist_ok=True)

    with open(SIMILARITY_MATRIX_FILE, "wb") as f:
        pickle.dump(similarity_matrix, f)
    logger.info(f"Saved similarity matrix → {SIMILARITY_MATRIX_FILE}")

    with open(TFIDF_MATRIX_FILE, "wb") as f:
        pickle.dump(tfidf_matrix, f)
    logger.info(f"Saved TF-IDF matrix → {TFIDF_MATRIX_FILE}")

    with open(PRODUCT_INDEX_FILE, "wb") as f:
        pickle.dump(
            {
                "product_id_to_index": product_id_to_index,
                "index_to_product_id": index_to_product_id,
            },
            f,
        )
    logger.info(f"Saved product index map → {PRODUCT_INDEX_FILE}")


# =============================================================================
# FUNCTION 7: load_model_artifacts()
# =============================================================================
def load_model_artifacts() -> Tuple[np.ndarray, Dict[str, int], Dict[int, str]]:
    """
    Load pre-computed similarity matrix and index maps from disk.

    Returns
    -------
    Tuple containing:
        - similarity_matrix (np.ndarray)
        - product_id_to_index (Dict[str, int])
        - index_to_product_id (Dict[int, str])

    Raises
    ------
    FileNotFoundError
        If model artifacts have not been built yet.
    """
    if not os.path.exists(SIMILARITY_MATRIX_FILE):
        raise FileNotFoundError(
            f"Similarity matrix not found at {SIMILARITY_MATRIX_FILE}. "
            f"Run build_content_model() first."
        )

    with open(SIMILARITY_MATRIX_FILE, "rb") as f:
        similarity_matrix = pickle.load(f)

    with open(PRODUCT_INDEX_FILE, "rb") as f:
        maps = pickle.load(f)

    logger.info("Loaded pre-computed content-based model artifacts")
    return (
        similarity_matrix,
        maps["product_id_to_index"],
        maps["index_to_product_id"],
    )


# =============================================================================
# FUNCTION 8: get_similar_products()
# =============================================================================
def get_similar_products(
    product_id: str,
    similarity_matrix: np.ndarray,
    product_id_to_index: Dict[str, int],
    index_to_product_id: Dict[int, str],
    products_df: pd.DataFrame,
    top_n: int = DEFAULT_TOP_N,
    exclude_self: bool = True,
) -> List[Dict]:
    """
    Given a product ID, return the Top-N most similar products.

    Algorithm:
    1. Look up the row index for the given product_id.
    2. Retrieve the entire similarity row (scores against ALL products).
    3. Sort by descending similarity score.
    4. Return the top N results (excluding the product itself).

    Parameters
    ----------
    product_id : str
        The source product (e.g. "P0001").
    similarity_matrix : np.ndarray
        Pre-computed cosine similarity matrix.
    product_id_to_index : Dict[str, int]
        Maps ProductID → row index in the matrix.
    index_to_product_id : Dict[int, str]
        Maps row index → ProductID.
    products_df : pd.DataFrame
        Full products table (for enriching results with names, prices, etc.).
    top_n : int
        Number of recommendations to return.
    exclude_self : bool
        Whether to exclude the source product from results.

    Returns
    -------
    List[Dict]
        List of recommended products with similarity scores.
        Each dict contains: ProductID, ProductName, Category, Brand,
        Price, SimilarityScore.
    """
    if product_id not in product_id_to_index:
        logger.warning(f"Product '{product_id}' not found in index")
        return []

    # Step 1: Get row index
    idx = product_id_to_index[product_id]

    # Step 2: Get similarity scores for this product against all others
    scores = similarity_matrix[idx]

    # Step 3: Sort indices by descending score
    # argsort returns ascending order; we reverse it with [::-1]
    sorted_indices = np.argsort(scores)[::-1]

    # Step 4: Collect top N results
    results: List[Dict] = []
    for sim_idx in sorted_indices:
        if exclude_self and sim_idx == idx:
            continue
        if len(results) >= top_n:
            break

        rec_product_id = index_to_product_id[sim_idx]
        score = float(scores[sim_idx])

        # Enrich with product metadata
        product_row = products_df[products_df["ProductID"] == rec_product_id]
        if product_row.empty:
            continue

        row = product_row.iloc[0]
        results.append(
            {
                "ProductID": rec_product_id,
                "ProductName": str(row.get("ProductName", "Unknown")),
                "Category": str(row.get("Category", "Unknown")),
                "SubCategory": str(row.get("SubCategory", "Unknown")),
                "Brand": str(row.get("Brand", "Unknown")),
                "Fabric": str(row.get("Fabric", "Unknown")),
                "Price": float(row.get("Price", 0)),
                "SimilarityScore": round(score, 4),
            }
        )

    logger.info(
        f"Content-based: {len(results)} recommendations for '{product_id}'"
    )
    return results


# =============================================================================
# FUNCTION 9: build_content_model()  —  The Orchestrator
# =============================================================================
def build_content_model() -> Tuple[np.ndarray, Dict[str, int], Dict[int, str], pd.DataFrame]:
    """
    Build the complete content-based model from scratch.

    Pipeline:
        1. Load products
        2. Create PriceRange bins
        3. Build combined feature strings
        4. Fit TF-IDF vectorizer
        5. Compute cosine similarity matrix
        6. Save all artifacts to disk
        7. Return objects for immediate use

    Returns
    -------
    Tuple containing:
        - similarity_matrix
        - product_id_to_index
        - index_to_product_id
        - products_df
    """
    logger.info("=" * 60)
    logger.info("BUILDING CONTENT-BASED MODEL")
    logger.info("=" * 60)

    # Step 1: Load data
    products_df = load_products()

    # Step 2: Create PriceRange
    products_df = create_price_range(products_df)

    # Step 3: Build feature strings
    feature_strings = build_feature_string(products_df)

    # Step 4: TF-IDF
    tfidf_matrix, vectorizer = build_tfidf_matrix(feature_strings)

    # Step 5: Cosine similarity
    similarity_matrix = compute_similarity_matrix(tfidf_matrix)

    # Step 6: Build index maps
    # These maps let us translate between ProductID strings and
    # integer indices in the similarity matrix.
    product_ids = products_df["ProductID"].tolist()
    product_id_to_index: Dict[str, int] = {
        pid: idx for idx, pid in enumerate(product_ids)
    }
    index_to_product_id: Dict[int, str] = {
        idx: pid for idx, pid in enumerate(product_ids)
    }

    # Step 7: Save to disk
    save_model_artifacts(
        similarity_matrix, tfidf_matrix, product_id_to_index, index_to_product_id
    )

    logger.info("🎉 Content-based model built and saved successfully")
    return similarity_matrix, product_id_to_index, index_to_product_id, products_df


# =============================================================================
# MAIN ENTRY POINT  —  Build model when run directly
# =============================================================================
if __name__ == "__main__":
    # Build the model
    sim_matrix, pid_to_idx, idx_to_pid, df = build_content_model()

    # Demo: show Top 5 similar products for the first product
    demo_id = df["ProductID"].iloc[0]
    print(f"\n{'='*60}")
    print(f"DEMO: Top 5 products similar to {demo_id}")
    print(f"  Source: {df[df['ProductID']==demo_id].iloc[0]['ProductName']}")
    print(f"{'='*60}")

    similar = get_similar_products(
        product_id=demo_id,
        similarity_matrix=sim_matrix,
        product_id_to_index=pid_to_idx,
        index_to_product_id=idx_to_pid,
        products_df=df,
        top_n=5,
    )
    for i, rec in enumerate(similar, 1):
        print(
            f"  {i}. {rec['ProductID']} | {rec['ProductName']:<30} | "
            f"{rec['Category']:<15} | {rec['Brand']:<20} | "
            f"Rs.{rec['Price']:>8,.0f} | Score: {rec['SimilarityScore']:.4f}"
        )
