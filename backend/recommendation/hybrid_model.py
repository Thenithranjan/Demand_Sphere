"""
==============================================================================
Hybrid Recommendation Engine
==============================================================================
Purpose:
    Combines Content-Based (40%), Collaborative Filtering (40%), and
    Business Rules (20%) into a unified recommendation list.

    This solves the limitations of individual algorithms:
    - Content-based keeps recommendations accurate to the product features.
    - Collaborative filtering brings in serendipitous customer buying patterns.
    - Business rules enforce domain constraints (like Shirt needing Pants).

Why this weighting (40/40/20) was chosen:
    - 40% Content-Based: Ensures high relevancy to what the user is viewing.
    - 40% Collaborative Filtering: Introduces personalization based on global
      purchase patterns.
    - 20% Business Rules: Acts as a safeguard/modulator to force critical
      complementary pairings (e.g., matching blouse for Saree) without letting
      them completely drown out ML predictions.

ML Concepts:
    - Hybrid systems (Weighted hybridization approach)
    - Min-Max Score Normalization
    - Scoring fusion
==============================================================================
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import pandas as pd
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import individual engines
from backend.recommendation.content_based import (
    load_model_artifacts as load_content_artifacts,
    get_similar_products,
)
from backend.recommendation.collaborative import (
    load_collab_artifacts,
    get_similar_items,
    recommend_for_customer,
)
from backend.recommendation.business_rules import (
    get_rule_based_recommendations,
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Constants
PRODUCTS_FILE: str = os.path.join(PROJECT_ROOT, "data", "processed", "products_clean.csv")
DEFAULT_TOP_N = 10

# Weights
WEIGHT_CONTENT = 0.40
WEIGHT_COLLAB = 0.40
WEIGHT_RULES = 0.20

# =============================================================================
# UTILITY: NORMALIZE SCORES
# =============================================================================
def normalize_scores(recommendations: List[Dict], score_key: str) -> Dict[str, float]:
    """
    Normalizes recommendation scores to [0, 1] using Min-Max scaling.

    If all scores are identical, sets them to 1.0. This makes scores from
    different models directly comparable.

    Parameters
    ----------
    recommendations : List[Dict]
        List of recommendations from a single engine.
    score_key : str
        The dictionary key containing the raw score.

    Returns
    -------
    Dict[str, float]
        Mapping of ProductID to normalized score [0.0, 1.0].
    """
    if not recommendations:
        return {}

    raw_scores = [float(rec[score_key]) for rec in recommendations]
    min_val = min(raw_scores)
    max_val = max(raw_scores)
    range_val = max_val - min_val

    normalized = {}
    for rec in recommendations:
        pid = rec["ProductID"]
        score = float(rec[score_key])
        if range_val > 0:
            normalized[pid] = (score - min_val) / range_val
        else:
            normalized[pid] = 1.0  # Fallback if all scores are identical

    return normalized

# =============================================================================
# HYBRID RECS BY PRODUCT
# =============================================================================
def hybrid_recommend_by_product(
    product_id: str,
    products_df: pd.DataFrame,
    top_n: int = DEFAULT_TOP_N,
) -> List[Dict]:
    """
    Generates hybrid recommendations when a user views a specific product.

    Weights:
        - 40% Content-based (similar features)
        - 40% Collaborative filtering (co-purchased products)
        - 20% Business rules (complementary products)

    Parameters
    ----------
    product_id : str
        The source product ID.
    products_df : pd.DataFrame
        Full products dataframe.
    top_n : int
        Number of recommendations to return.

    Returns
    -------
    List[Dict]
        Ranked hybrid recommendations.
    """
    # 1. Fetch recommendations from all 3 engines
    try:
        # Load content-based model
        c_sim, c_p2i, c_i2p = load_content_artifacts()
        content_recs = get_similar_products(
            product_id=product_id,
            similarity_matrix=c_sim,
            product_id_to_index=c_p2i,
            index_to_product_id=c_i2p,
            products_df=products_df,
            top_n=50,  # Get larger pool for fusion
        )
    except Exception as e:
        logger.warning(f"Failed to fetch content recommendations: {e}")
        content_recs = []

    try:
        # Load collaborative filtering model
        collab_sim, _, _, _, collab_p2i, collab_i2p = load_collab_artifacts()
        collab_recs = get_similar_items(
            product_id=product_id,
            item_similarity=collab_sim,
            product_to_idx=collab_p2i,
            idx_to_product=collab_i2p,
            products_df=products_df,
            top_n=50,
        )
    except Exception as e:
        logger.warning(f"Failed to fetch collaborative recommendations: {e}")
        collab_recs = []

    try:
        # Business rules complementary engine
        rules_recs = get_rule_based_recommendations(
            product_id=product_id,
            products_df=products_df,
            top_n=50,
        )
    except Exception as e:
        logger.warning(f"Failed to fetch rule-based recommendations: {e}")
        rules_recs = []

    # 2. Normalize scores from all engines
    norm_content = normalize_scores(content_recs, "SimilarityScore")
    norm_collab = normalize_scores(collab_recs, "SimilarityScore")
    norm_rules = normalize_scores(rules_recs, "RuleScore")

    # 3. Combine scores using weights
    all_product_ids = set(norm_content.keys()) | set(norm_collab.keys()) | set(norm_rules.keys())
    hybrid_scores: Dict[str, float] = {}

    for pid in all_product_ids:
        s_content = norm_content.get(pid, 0.0)
        s_collab = norm_collab.get(pid, 0.0)
        s_rules = norm_rules.get(pid, 0.0)

        # Weighted sum formula
        total_score = (
            WEIGHT_CONTENT * s_content +
            WEIGHT_COLLAB * s_collab +
            WEIGHT_RULES * s_rules
        )
        hybrid_scores[pid] = total_score

    # 4. Sort and build final metadata-enriched recommendations
    sorted_pids = sorted(hybrid_scores.keys(), key=lambda x: hybrid_scores[x], reverse=True)
    results: List[Dict] = []

    for pid in sorted_pids:
        if len(results) >= top_n:
            break

        product_row = products_df[products_df["ProductID"] == pid]
        if product_row.empty:
            continue

        row = product_row.iloc[0]
        results.append({
            "ProductID": pid,
            "ProductName": str(row.get("ProductName", "Unknown")),
            "Category": str(row.get("Category", "Unknown")),
            "SubCategory": str(row.get("SubCategory", "Unknown")),
            "Brand": str(row.get("Brand", "Unknown")),
            "Price": float(row.get("Price", 0.0)),
            "HybridScore": round(hybrid_scores[pid], 4),
            "Breakdown": {
                "Content": round(norm_content.get(pid, 0.0), 4),
                "Collab": round(norm_collab.get(pid, 0.0), 4),
                "Rules": round(norm_rules.get(pid, 0.0), 4),
            }
        })

    logger.info(f"Hybrid product recommendations computed: {len(results)} items")
    return results

# =============================================================================
# HYBRID RECS FOR CUSTOMER
# =============================================================================
def hybrid_recommend_for_customer(
    customer_id: str,
    products_df: pd.DataFrame,
    top_n: int = DEFAULT_TOP_N,
) -> List[Dict]:
    """
    Generates hybrid personalized recommendations for a customer.

    Combines:
        - 40% Customer-based Collaborative Filtering (global purchase trends)
        - 40% Customer-specific Content-based matching (based on products they bought)
        - 20% Business Rules based on their last purchase

    Parameters
    ----------
    customer_id : str
        The unique customer ID.
    products_df : pd.DataFrame
        Full products dataframe.
    top_n : int
        Number of recommendations to return.

    Returns
    -------
    List[Dict]
        Ranked hybrid recommendations.
    """
    # 1. Fetch personalized collaborative recommendations
    try:
        collab_sim, interact_mat, c2i, _, p2i, i2p = load_collab_artifacts()
        collab_recs = recommend_for_customer(
            customer_id=customer_id,
            item_similarity=collab_sim,
            interaction_matrix=interact_mat,
            customer_to_idx=c2i,
            product_to_idx=p2i,
            idx_to_product=i2p,
            products_df=products_df,
            top_n=50,
        )
    except Exception as e:
        logger.warning(f"Failed to fetch collab customer recommendations: {e}")
        collab_recs = []
        c2i, interact_mat, i2p = {}, None, {}

    # 2. Content-based personalization: Find similar items to their purchases
    content_recs = []
    last_purchase_pid = None
    if customer_id in c2i and interact_mat is not None:
        c_idx = c2i[customer_id]
        customer_vector = interact_mat[c_idx]
        purchased_indices = np.where(customer_vector > 0)[0]

        if len(purchased_indices) > 0:
            # Sort purchases by index or date to find the most recent/frequent
            # For simplicity, pick the last purchased product as the seed for content/rules
            last_purchase_idx = purchased_indices[-1]
            last_purchase_pid = i2p[last_purchase_idx]

            try:
                c_sim, c_p2i, c_i2p = load_content_artifacts()
                # Aggregate content similarity scores across all their purchased products
                # (similar to average profile method)
                profile_scores = np.zeros(len(products_df))
                for idx in purchased_indices:
                    profile_scores += c_sim[idx] * customer_vector[idx]

                # Zero out already purchased
                profile_scores[purchased_indices] = 0.0

                # Build content recommendations list
                sorted_profile_indices = np.argsort(profile_scores)[::-1]
                for p_idx in sorted_profile_indices[:50]:
                    score = profile_scores[p_idx]
                    if score <= 0:
                        break
                    content_recs.append({
                        "ProductID": c_i2p[p_idx],
                        "SimilarityScore": float(score),
                    })
            except Exception as e:
                logger.warning(f"Failed content-based user profiling: {e}")

    # 3. Business rules: Fetch complements for their last purchase
    rules_recs = []
    if last_purchase_pid:
        try:
            rules_recs = get_rule_based_recommendations(
                product_id=last_purchase_pid,
                products_df=products_df,
                top_n=50,
            )
        except Exception as e:
            logger.warning(f"Failed rule-based cross-sell recommendations: {e}")

    # 4. Normalize scores
    norm_content = normalize_scores(content_recs, "SimilarityScore")
    norm_collab = normalize_scores(collab_recs, "CollabScore")
    norm_rules = normalize_scores(rules_recs, "RuleScore")

    # 5. Combine scores
    all_product_ids = set(norm_content.keys()) | set(norm_collab.keys()) | set(norm_rules.keys())

    # Exclude already purchased items if collab engine missed any
    purchased_pids = set()
    if customer_id in c2i and interact_mat is not None:
        c_idx = c2i[customer_id]
        purchased_pids = {i2p[idx] for idx in np.where(interact_mat[c_idx] > 0)[0]}

    hybrid_scores: Dict[str, float] = {}
    for pid in all_product_ids:
        if pid in purchased_pids:
            continue

        s_content = norm_content.get(pid, 0.0)
        s_collab = norm_collab.get(pid, 0.0)
        s_rules = norm_rules.get(pid, 0.0)

        total_score = (
            WEIGHT_CONTENT * s_content +
            WEIGHT_COLLAB * s_collab +
            WEIGHT_RULES * s_rules
        )
        hybrid_scores[pid] = total_score

    # 6. Sort and enrich
    sorted_pids = sorted(hybrid_scores.keys(), key=lambda x: hybrid_scores[x], reverse=True)
    results: List[Dict] = []

    for pid in sorted_pids:
        if len(results) >= top_n:
            break

        product_row = products_df[products_df["ProductID"] == pid]
        if product_row.empty:
            continue

        row = product_row.iloc[0]
        results.append({
            "ProductID": pid,
            "ProductName": str(row.get("ProductName", "Unknown")),
            "Category": str(row.get("Category", "Unknown")),
            "SubCategory": str(row.get("SubCategory", "Unknown")),
            "Brand": str(row.get("Brand", "Unknown")),
            "Price": float(row.get("Price", 0.0)),
            "HybridScore": round(hybrid_scores[pid], 4),
            "Breakdown": {
                "Content": round(norm_content.get(pid, 0.0), 4),
                "Collab": round(norm_collab.get(pid, 0.0), 4),
                "Rules": round(norm_rules.get(pid, 0.0), 4),
            }
        })

    logger.info(f"Hybrid customer recommendations computed: {len(results)} items")
    return results

# =============================================================================
# MAIN RUN
# =============================================================================
if __name__ == "__main__":
    products_df = pd.read_csv(PRODUCTS_FILE)

    # Demo 1: Hybrid Recommendations for a specific Product (P0001)
    print("\n" + "=" * 80)
    print("DEMO 1: Hybrid Recommendations for Product P0001 (Veshti)")
    print("=" * 80)
    product_recs = hybrid_recommend_by_product("P0001", products_df, top_n=5)
    for i, rec in enumerate(product_recs, 1):
        print(
            f"{i}. {rec['ProductID']} | {rec['ProductName']:<35} | "
            f"Rs.{rec['Price']:>8,.0f} | Score: {rec['HybridScore']:.4f} | "
            f"Breakdown: Content={rec['Breakdown']['Content']:.2f}, "
            f"Collab={rec['Breakdown']['Collab']:.2f}, "
            f"Rules={rec['Breakdown']['Rules']:.2f}"
        )

    # Demo 2: Hybrid Recommendations for a specific Customer (C00001)
    print("\n" + "=" * 80)
    print("DEMO 2: Hybrid Personalised Recommendations for Customer C00001")
    print("=" * 80)
    customer_recs = hybrid_recommend_for_customer("C00001", products_df, top_n=5)
    for i, rec in enumerate(customer_recs, 1):
        print(
            f"{i}. {rec['ProductID']} | {rec['ProductName']:<35} | "
            f"Rs.{rec['Price']:>8,.0f} | Score: {rec['HybridScore']:.4f} | "
            f"Breakdown: Content={rec['Breakdown']['Content']:.2f}, "
            f"Collab={rec['Breakdown']['Collab']:.2f}, "
            f"Rules={rec['Breakdown']['Rules']:.2f}"
        )
