"""
==============================================================================
Collaborative Filtering Recommendation Engine
==============================================================================
Purpose:
    Recommends products based on CUSTOMER PURCHASE BEHAVIOUR, not product
    attributes.  If customers who bought Veshti also bought Lungi and
    Towel, then a new customer buying Veshti should also see Lungi and
    Towel as recommendations.

    This is the engine behind:
        Amazon  -> "Customers who bought this also bought..."
        Flipkart -> "Frequently bought together"
        Myntra  -> "People also bought"

How it works (high-level):
    1.  Build a Customer x Product interaction matrix from sales history.
    2.  Compute Item-Item similarity using cosine similarity on the
        TRANSPOSE of the interaction matrix (columns = products).
    3.  For a given product, find the most similar products based on
        overlapping purchase patterns.
    4.  For a given customer, aggregate scores from all products they've
        bought, weighted by their purchase history.

Why Item-Based (not User-Based):
    - Item similarities are more STABLE (product characteristics don't
      change; user tastes do).
    - SCALES better: 500 products vs 2000 customers -> smaller matrix.
    - Amazon uses Item-Based CF as their primary engine (published paper:
      "Item-to-Item Collaborative Filtering", Linden et al. 2003).

ML Concepts used:
    - Customer-Product interaction matrix (implicit feedback)
    - Item-Item Cosine Similarity
    - Weighted score aggregation
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
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix

# =============================================================================
# PATH SETUP
# =============================================================================
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =============================================================================
# CONSTANTS
# =============================================================================
# Input files
SALES_FILE: str = os.path.join(PROJECT_ROOT, "data", "processed", "sales_clean.csv")
PRODUCTS_FILE: str = os.path.join(PROJECT_ROOT, "data", "processed", "products_clean.csv")

# Output — pre-computed model artifacts
MODELS_DIR: str = os.path.join(PROJECT_ROOT, "backend", "models")
ITEM_SIMILARITY_FILE: str = os.path.join(MODELS_DIR, "collab_item_similarity.pkl")
INTERACTION_MATRIX_FILE: str = os.path.join(MODELS_DIR, "collab_interaction_matrix.pkl")
COLLAB_INDEX_FILE: str = os.path.join(MODELS_DIR, "collab_index_maps.pkl")

# Default number of recommendations
DEFAULT_TOP_N: int = 10

# Minimum number of purchases a product must have to be considered
# for similarity calculation.  Products with very few purchases
# produce noisy, unreliable similarity scores.
MIN_PRODUCT_PURCHASES: int = 5

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
# FUNCTION 1: load_sales_data()
# =============================================================================
def load_sales_data(file_path: str = SALES_FILE) -> pd.DataFrame:
    """
    Load the cleaned sales transactions dataset.

    Parameters
    ----------
    file_path : str
        Path to sales_clean.csv.

    Returns
    -------
    pd.DataFrame
        Sales data with CustomerID, ProductID, Quantity, FinalPrice, etc.
    """
    if not os.path.exists(file_path):
        logger.error(f"Sales file not found: {file_path}")
        raise FileNotFoundError(f"Sales file not found: {file_path}")

    df = pd.read_csv(file_path)
    logger.info(f"Loaded sales: {df.shape[0]:,} rows x {df.shape[1]} columns")
    return df


# =============================================================================
# FUNCTION 2: load_products_data()
# =============================================================================
def load_products_data(file_path: str = PRODUCTS_FILE) -> pd.DataFrame:
    """Load the cleaned products dataset for enriching recommendations."""
    if not os.path.exists(file_path):
        logger.error(f"Products file not found: {file_path}")
        raise FileNotFoundError(f"Products file not found: {file_path}")

    df = pd.read_csv(file_path)
    logger.info(f"Loaded products: {df.shape[0]} rows x {df.shape[1]} columns")
    return df


# =============================================================================
# FUNCTION 3: build_interaction_matrix()
# =============================================================================
def build_interaction_matrix(
    sales_df: pd.DataFrame,
) -> Tuple[np.ndarray, Dict[str, int], Dict[int, str], Dict[str, int], Dict[int, str]]:
    """
    Build the Customer x Product interaction matrix.

    What is an interaction matrix?
    ------------------------------
    A 2D table where:
        - Rows    = Customers  (2000 customers)
        - Columns = Products   (500 products)
        - Values  = Interaction strength

    Interaction Strength options:
        1. Binary (0/1)     : Did the customer buy this product? (simplest)
        2. Purchase count   : How many times did they buy it?
        3. Total quantity    : How many units total?
        4. Total spend      : How much money did they spend on it?

    We use PURCHASE COUNT as the interaction signal because:
        - It captures repeat purchases (a customer buying the same
          Veshti 3 times shows stronger preference than buying once).
        - It's more informative than binary (0/1).
        - It's more stable than spend (which is affected by price changes
          and discounts).

    Sparsity:
        Our matrix is 2000 x 500 = 1,000,000 cells.
        Only 48,638 cells have non-zero values.
        Sparsity = 95.14% — this is typical for retail data.

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales transactions with CustomerID and ProductID columns.

    Returns
    -------
    Tuple containing:
        - interaction_matrix (np.ndarray): shape (n_customers, n_products)
        - customer_to_idx (Dict): CustomerID -> row index
        - idx_to_customer (Dict): row index -> CustomerID
        - product_to_idx (Dict): ProductID -> column index
        - idx_to_product (Dict): column index -> ProductID
    """
    # -------------------------------------------------------------------------
    # Step 1: Aggregate purchase counts per (Customer, Product) pair
    # -------------------------------------------------------------------------
    # groupby().size() counts the number of transactions (rows)
    # for each unique (CustomerID, ProductID) combination.
    interaction = (
        sales_df
        .groupby(["CustomerID", "ProductID"])
        .size()
        .reset_index(name="purchase_count")
    )
    logger.info(
        f"Unique (customer, product) interactions: {len(interaction):,}"
    )

    # -------------------------------------------------------------------------
    # Step 2: Create index mappings
    # -------------------------------------------------------------------------
    # We need to map string IDs (like "C00001") to integer indices
    # (like 0) because numpy arrays use integer indexing.
    unique_customers = sorted(sales_df["CustomerID"].unique())
    unique_products = sorted(sales_df["ProductID"].unique())

    customer_to_idx: Dict[str, int] = {
        cid: idx for idx, cid in enumerate(unique_customers)
    }
    idx_to_customer: Dict[int, str] = {
        idx: cid for idx, cid in enumerate(unique_customers)
    }
    product_to_idx: Dict[str, int] = {
        pid: idx for idx, pid in enumerate(unique_products)
    }
    idx_to_product: Dict[int, str] = {
        idx: pid for idx, pid in enumerate(unique_products)
    }

    # -------------------------------------------------------------------------
    # Step 3: Build the matrix
    # -------------------------------------------------------------------------
    # Initialize a zero matrix of shape (n_customers, n_products)
    n_customers = len(unique_customers)
    n_products = len(unique_products)
    matrix = np.zeros((n_customers, n_products), dtype=np.float32)

    # Fill in the purchase counts
    for _, row in interaction.iterrows():
        c_idx = customer_to_idx[row["CustomerID"]]
        p_idx = product_to_idx[row["ProductID"]]
        matrix[c_idx, p_idx] = row["purchase_count"]

    # -------------------------------------------------------------------------
    # Step 4: Log statistics
    # -------------------------------------------------------------------------
    non_zero = np.count_nonzero(matrix)
    total_cells = n_customers * n_products
    sparsity = (1 - non_zero / total_cells) * 100

    logger.info(
        f"Interaction matrix: {n_customers} customers x {n_products} products"
    )
    logger.info(
        f"Non-zero entries: {non_zero:,} / {total_cells:,} "
        f"(sparsity: {sparsity:.2f}%)"
    )

    return matrix, customer_to_idx, idx_to_customer, product_to_idx, idx_to_product


# =============================================================================
# FUNCTION 4: compute_item_similarity()
# =============================================================================
def compute_item_similarity(
    interaction_matrix: np.ndarray,
    min_purchases: int = MIN_PRODUCT_PURCHASES,
) -> np.ndarray:
    """
    Compute Item-Item similarity using cosine similarity on purchase patterns.

    How Item-Item CF works:
    -----------------------
    Instead of comparing USERS (who are unpredictable), we compare PRODUCTS
    based on who bought them.

    Consider two products:
        Product A (Veshti):  bought by [C1, C2, C5, C8, C12, ...]
        Product B (Lungi):   bought by [C1, C2, C5, C9, C15, ...]
        Product C (Saree):   bought by [C3, C4, C6, C7, C10, ...]

    Veshti and Lungi have HIGH similarity (many overlapping customers).
    Veshti and Saree have LOW similarity (few overlapping customers).

    Mathematically:
        We take COLUMNS of the interaction matrix (each column = one
        product's purchase vector across all customers) and compute
        cosine similarity between every pair of columns.

    Why transpose?
        interaction_matrix shape = (customers, products)
        We need product-vs-product similarity, so we transpose to
        (products, customers) and compute cosine_similarity.

    Parameters
    ----------
    interaction_matrix : np.ndarray
        Shape (n_customers, n_products). Values = purchase counts.
    min_purchases : int
        Minimum purchases a product must have to be included.
        Products with fewer purchases get similarity = 0 (too noisy).

    Returns
    -------
    np.ndarray
        Item-item similarity matrix of shape (n_products, n_products).
    """
    # -------------------------------------------------------------------------
    # Step 1: Transpose — rows become products, columns become customers
    # -------------------------------------------------------------------------
    # Original:   matrix[customer_i][product_j] = purchase count
    # Transposed: matrix[product_j][customer_i] = purchase count
    product_vectors = interaction_matrix.T  # shape: (n_products, n_customers)

    # -------------------------------------------------------------------------
    # Step 2: Filter out low-purchase products
    # -------------------------------------------------------------------------
    # Products with very few purchases produce unreliable similarity scores.
    # A product bought by only 1 customer might show 1.0 similarity with
    # another product bought by that same single customer — this is noise,
    # not a real pattern.
    purchase_counts = (product_vectors > 0).sum(axis=1)  # purchases per product
    low_purchase_mask = purchase_counts < min_purchases
    low_count = int(low_purchase_mask.sum())
    if low_count > 0:
        logger.info(
            f"Masking {low_count} products with < {min_purchases} purchases"
        )

    # -------------------------------------------------------------------------
    # Step 3: Compute cosine similarity
    # -------------------------------------------------------------------------
    # cosine_similarity expects shape (n_samples, n_features).
    # Here: n_samples = n_products, n_features = n_customers.
    # Result: (n_products, n_products) matrix.
    item_similarity = cosine_similarity(product_vectors)

    # -------------------------------------------------------------------------
    # Step 4: Zero out the diagonal
    # -------------------------------------------------------------------------
    # A product is always 100% similar to itself — that's not useful.
    # Setting diagonal to 0 ensures we never recommend the same product.
    np.fill_diagonal(item_similarity, 0)

    # -------------------------------------------------------------------------
    # Step 5: Zero out low-purchase products
    # -------------------------------------------------------------------------
    # Set their similarity rows/columns to 0 so they don't pollute results.
    if low_count > 0:
        item_similarity[low_purchase_mask, :] = 0
        item_similarity[:, low_purchase_mask] = 0

    logger.info(
        f"Item similarity matrix: {item_similarity.shape[0]} x "
        f"{item_similarity.shape[1]}"
    )

    return item_similarity


# =============================================================================
# FUNCTION 5: get_similar_items()
# =============================================================================
def get_similar_items(
    product_id: str,
    item_similarity: np.ndarray,
    product_to_idx: Dict[str, int],
    idx_to_product: Dict[int, str],
    products_df: pd.DataFrame,
    top_n: int = DEFAULT_TOP_N,
) -> List[Dict]:
    """
    Given a product, return Top-N similar products based on collaborative
    filtering (shared purchase patterns).

    This answers: "Customers who bought product X also bought..."

    Algorithm:
        1. Look up the product's column index.
        2. Get the similarity row (scores against all other products).
        3. Sort by descending score.
        4. Return top N with metadata.

    Parameters
    ----------
    product_id : str
        Source product (e.g. "P0001").
    item_similarity : np.ndarray
        Pre-computed item-item similarity matrix.
    product_to_idx : Dict
        ProductID -> column index.
    idx_to_product : Dict
        Column index -> ProductID.
    products_df : pd.DataFrame
        Products table for enrichment.
    top_n : int
        Number of recommendations.

    Returns
    -------
    List[Dict]
        Recommended products with similarity scores.
    """
    if product_id not in product_to_idx:
        logger.warning(f"Product '{product_id}' not found in collaborative index")
        return []

    idx = product_to_idx[product_id]
    scores = item_similarity[idx]

    # Get indices sorted by descending score
    sorted_indices = np.argsort(scores)[::-1]

    results: List[Dict] = []
    for sim_idx in sorted_indices:
        if len(results) >= top_n:
            break
        score = float(scores[sim_idx])
        if score <= 0:
            break  # No more meaningful similarities

        rec_pid = idx_to_product[sim_idx]
        product_row = products_df[products_df["ProductID"] == rec_pid]
        if product_row.empty:
            continue

        row = product_row.iloc[0]
        results.append({
            "ProductID": rec_pid,
            "ProductName": str(row.get("ProductName", "Unknown")),
            "Category": str(row.get("Category", "Unknown")),
            "SubCategory": str(row.get("SubCategory", "Unknown")),
            "Brand": str(row.get("Brand", "Unknown")),
            "Price": float(row.get("Price", 0)),
            "SimilarityScore": round(score, 4),
        })

    logger.info(
        f"Collaborative (item-based): {len(results)} recs for '{product_id}'"
    )
    return results


# =============================================================================
# FUNCTION 6: recommend_for_customer()
# =============================================================================
def recommend_for_customer(
    customer_id: str,
    item_similarity: np.ndarray,
    interaction_matrix: np.ndarray,
    customer_to_idx: Dict[str, int],
    product_to_idx: Dict[str, int],
    idx_to_product: Dict[int, str],
    products_df: pd.DataFrame,
    top_n: int = DEFAULT_TOP_N,
) -> List[Dict]:
    """
    Recommend products for a specific customer based on their purchase history.

    Algorithm (Weighted Score Aggregation):
    ----------------------------------------
    For each candidate product C that the customer has NOT bought:

        score(C) = SUM over all products P that the customer HAS bought:
                       similarity(C, P) * interaction_strength(customer, P)

    In plain English:
        "If you bought Veshti (3 times) and Lungi is similar to Veshti
         (similarity 0.7), then Lungi gets a score of 3 * 0.7 = 2.1."

    The scores from ALL purchased products are summed for each candidate,
    then we return the highest-scoring candidates.

    Why this works:
        - Products similar to MULTIPLE purchased items get higher scores
          (they match the customer's overall taste, not just one purchase).
        - Products bought more frequently contribute more weight
          (repeat purchases signal stronger preference).

    Parameters
    ----------
    customer_id : str
        The customer to generate recommendations for.
    item_similarity : np.ndarray
        Pre-computed item-item similarity matrix.
    interaction_matrix : np.ndarray
        Customer x Product interaction matrix.
    customer_to_idx : Dict
        CustomerID -> row index.
    product_to_idx : Dict
        ProductID -> column index.
    idx_to_product : Dict
        Column index -> ProductID.
    products_df : pd.DataFrame
        Products table.
    top_n : int
        Number of recommendations.

    Returns
    -------
    List[Dict]
        Personalised product recommendations.
    """
    if customer_id not in customer_to_idx:
        logger.warning(f"Customer '{customer_id}' not found in interaction matrix")
        return []

    c_idx = customer_to_idx[customer_id]

    # -------------------------------------------------------------------------
    # Step 1: Get this customer's purchase vector
    # -------------------------------------------------------------------------
    # Shape: (n_products,)
    # Values: purchase count for each product (0 = never bought)
    customer_vector = interaction_matrix[c_idx]

    # -------------------------------------------------------------------------
    # Step 2: Compute scores for all products
    # -------------------------------------------------------------------------
    # Matrix multiplication: item_similarity @ customer_vector
    # For each product C:
    #   score(C) = sum(similarity(C, P) * customer_vector[P]) for all P
    #
    # This is the weighted aggregation formula in vectorised form.
    # Much faster than looping through products individually.
    scores = item_similarity.dot(customer_vector)

    # -------------------------------------------------------------------------
    # Step 3: Zero out already-purchased products
    # -------------------------------------------------------------------------
    # We don't want to recommend things the customer already bought.
    already_purchased = customer_vector > 0
    scores[already_purchased] = 0

    # -------------------------------------------------------------------------
    # Step 4: Get Top-N
    # -------------------------------------------------------------------------
    sorted_indices = np.argsort(scores)[::-1]

    results: List[Dict] = []
    for idx in sorted_indices:
        if len(results) >= top_n:
            break
        score = float(scores[idx])
        if score <= 0:
            break

        rec_pid = idx_to_product[idx]
        product_row = products_df[products_df["ProductID"] == rec_pid]
        if product_row.empty:
            continue

        row = product_row.iloc[0]
        results.append({
            "ProductID": rec_pid,
            "ProductName": str(row.get("ProductName", "Unknown")),
            "Category": str(row.get("Category", "Unknown")),
            "SubCategory": str(row.get("SubCategory", "Unknown")),
            "Brand": str(row.get("Brand", "Unknown")),
            "Price": float(row.get("Price", 0)),
            "CollabScore": round(score, 4),
        })

    logger.info(
        f"Collaborative (customer): {len(results)} recs for '{customer_id}'"
    )
    return results


# =============================================================================
# FUNCTION 7: save_collab_artifacts()
# =============================================================================
def save_collab_artifacts(
    item_similarity: np.ndarray,
    interaction_matrix: np.ndarray,
    customer_to_idx: Dict[str, int],
    idx_to_customer: Dict[int, str],
    product_to_idx: Dict[str, int],
    idx_to_product: Dict[int, str],
) -> None:
    """
    Save all collaborative filtering artifacts to disk.

    Saved artifacts:
        1. Item-item similarity matrix (500 x 500)
        2. Interaction matrix (2000 x 500) — for customer recommendations
        3. Index maps — for translating between IDs and matrix indices
    """
    os.makedirs(MODELS_DIR, exist_ok=True)

    with open(ITEM_SIMILARITY_FILE, "wb") as f:
        pickle.dump(item_similarity, f)
    logger.info(f"Saved item similarity -> {ITEM_SIMILARITY_FILE}")

    with open(INTERACTION_MATRIX_FILE, "wb") as f:
        pickle.dump(interaction_matrix, f)
    logger.info(f"Saved interaction matrix -> {INTERACTION_MATRIX_FILE}")

    with open(COLLAB_INDEX_FILE, "wb") as f:
        pickle.dump({
            "customer_to_idx": customer_to_idx,
            "idx_to_customer": idx_to_customer,
            "product_to_idx": product_to_idx,
            "idx_to_product": idx_to_product,
        }, f)
    logger.info(f"Saved index maps -> {COLLAB_INDEX_FILE}")


# =============================================================================
# FUNCTION 8: load_collab_artifacts()
# =============================================================================
def load_collab_artifacts() -> Tuple[
    np.ndarray, np.ndarray,
    Dict[str, int], Dict[int, str],
    Dict[str, int], Dict[int, str],
]:
    """
    Load pre-computed collaborative filtering artifacts from disk.

    Returns
    -------
    Tuple containing:
        - item_similarity (np.ndarray)
        - interaction_matrix (np.ndarray)
        - customer_to_idx, idx_to_customer
        - product_to_idx, idx_to_product
    """
    if not os.path.exists(ITEM_SIMILARITY_FILE):
        raise FileNotFoundError(
            f"Collaborative model not found at {ITEM_SIMILARITY_FILE}. "
            f"Run build_collaborative_model() first."
        )

    with open(ITEM_SIMILARITY_FILE, "rb") as f:
        item_similarity = pickle.load(f)

    with open(INTERACTION_MATRIX_FILE, "rb") as f:
        interaction_matrix = pickle.load(f)

    with open(COLLAB_INDEX_FILE, "rb") as f:
        maps = pickle.load(f)

    logger.info("Loaded pre-computed collaborative filtering artifacts")
    return (
        item_similarity,
        interaction_matrix,
        maps["customer_to_idx"],
        maps["idx_to_customer"],
        maps["product_to_idx"],
        maps["idx_to_product"],
    )


# =============================================================================
# FUNCTION 9: build_collaborative_model()  —  The Orchestrator
# =============================================================================
def build_collaborative_model() -> Tuple[
    np.ndarray, np.ndarray,
    Dict[str, int], Dict[int, str],
    Dict[str, int], Dict[int, str],
    pd.DataFrame,
]:
    """
    Build the complete collaborative filtering model.

    Pipeline:
        1. Load sales and products data
        2. Build customer-product interaction matrix
        3. Compute item-item similarity
        4. Save all artifacts to disk

    Returns
    -------
    Tuple with all model components for immediate use.
    """
    logger.info("=" * 60)
    logger.info("BUILDING COLLABORATIVE FILTERING MODEL")
    logger.info("=" * 60)

    # Step 1: Load data
    sales_df = load_sales_data()
    products_df = load_products_data()

    # Step 2: Build interaction matrix
    (
        interaction_matrix,
        customer_to_idx,
        idx_to_customer,
        product_to_idx,
        idx_to_product,
    ) = build_interaction_matrix(sales_df)

    # Step 3: Compute item-item similarity
    item_similarity = compute_item_similarity(interaction_matrix)

    # Step 4: Save artifacts
    save_collab_artifacts(
        item_similarity,
        interaction_matrix,
        customer_to_idx,
        idx_to_customer,
        product_to_idx,
        idx_to_product,
    )

    logger.info("Collaborative filtering model built and saved successfully")
    return (
        item_similarity,
        interaction_matrix,
        customer_to_idx,
        idx_to_customer,
        product_to_idx,
        idx_to_product,
        products_df,
    )


# =============================================================================
# MAIN ENTRY POINT  —  Build model + demo when run directly
# =============================================================================
if __name__ == "__main__":
    # Build the model
    (
        item_sim, interact_mat,
        c2i, i2c, p2i, i2p, products_df
    ) = build_collaborative_model()

    # =========================================================================
    # Demo 1: Item-based — "Customers who bought P0001 also bought..."
    # =========================================================================
    demo_pid = "P0001"
    print(f"\n{'='*60}")
    print(f"DEMO 1: Customers who bought {demo_pid} also bought...")
    source_row = products_df[products_df["ProductID"] == demo_pid]
    if not source_row.empty:
        print(f"  Source: {source_row.iloc[0]['ProductName']}")
    print(f"{'='*60}")

    item_recs = get_similar_items(
        product_id=demo_pid,
        item_similarity=item_sim,
        product_to_idx=p2i,
        idx_to_product=i2p,
        products_df=products_df,
        top_n=5,
    )
    for i, rec in enumerate(item_recs, 1):
        print(
            f"  {i}. {rec['ProductID']} | {rec['ProductName']:<35} | "
            f"{rec['Category']:<15} | Rs.{rec['Price']:>8,.0f} | "
            f"Score: {rec['SimilarityScore']:.4f}"
        )

    # =========================================================================
    # Demo 2: Customer-based — "Recommended for you, C00001"
    # =========================================================================
    demo_cid = "C00001"
    print(f"\n{'='*60}")
    print(f"DEMO 2: Recommended for customer {demo_cid}")
    print(f"{'='*60}")

    # Show what this customer has already bought
    customer_purchases = interact_mat[c2i[demo_cid]]
    purchased_pids = [i2p[i] for i in range(len(customer_purchases)) if customer_purchases[i] > 0]
    print(f"  Already purchased: {purchased_pids[:8]}{'...' if len(purchased_pids) > 8 else ''}")

    cust_recs = recommend_for_customer(
        customer_id=demo_cid,
        item_similarity=item_sim,
        interaction_matrix=interact_mat,
        customer_to_idx=c2i,
        product_to_idx=p2i,
        idx_to_product=i2p,
        products_df=products_df,
        top_n=5,
    )
    for i, rec in enumerate(cust_recs, 1):
        print(
            f"  {i}. {rec['ProductID']} | {rec['ProductName']:<35} | "
            f"{rec['Category']:<15} | Rs.{rec['Price']:>8,.0f} | "
            f"Score: {rec['CollabScore']:.4f}"
        )
