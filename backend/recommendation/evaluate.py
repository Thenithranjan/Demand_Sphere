"""
==============================================================================
Recommendation Evaluation Layer: evaluate.py
==============================================================================
Purpose:
    Evaluates the recommendation system offline using key ranking and system
    metrics. This provides quantitative evidence of whether our hybrid engine
    performs better than simple popularity or individual algorithms.

Evaluation Workflow:
    1. Split sales transaction data randomly (80% train, 20% test).
    2. Build a collaborative filtering model using ONLY the train set
       (to prevent data leakage / evaluation contamination).
    3. Generate Top-K recommendations for a set of evaluation users.
    4. Compare recommendations against the users' test purchases (ground truth).
    5. Compute:
       - Precision@K
       - Recall@K
       - Catalog Coverage
       - Novelty (Self-Information)
       - Diversity (Intra-List Distance)

ML Concepts:
    - Offline evaluation protocol for ranking recommenders.
    - Information Retrieval metrics (Precision/Recall).
    - System metrics (Coverage, Novelty, Diversity).
    - Information Theory (Self-Information for Novelty).
==============================================================================
"""

import os
import sys
import logging
import math
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

import pandas as pd
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports from individual engines
from backend.recommendation.content_based import (
    load_model_artifacts as load_content_artifacts,
)
from backend.recommendation.collaborative import (
    build_interaction_matrix,
    compute_item_similarity,
    recommend_for_customer,
)
from backend.recommendation.hybrid_model import (
    hybrid_recommend_for_customer,
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Constants
PRODUCTS_FILE: str = os.path.join(PROJECT_ROOT, "data", "processed", "products_clean.csv")
SALES_FILE: str = os.path.join(PROJECT_ROOT, "data", "processed", "sales_clean.csv")

# =============================================================================
# EVALUATION CLASS
# =============================================================================
class RecommenderEvaluator:
    def __init__(self, train_ratio: float = 0.8, seed: int = 42):
        self.train_ratio = train_ratio
        self.seed = seed
        self.products_df = pd.read_csv(PRODUCTS_FILE)
        self.sales_df = pd.read_csv(SALES_FILE)

        # Precompute content similarity matrix for diversity calculation
        try:
            self.content_sim, _, _ = load_content_artifacts()
        except Exception as e:
            logger.warning(f"Could not load content similarity for diversity: {e}")
            self.content_sim = None

        # Build popularity frequencies for novelty calculation
        self.total_sales = len(self.sales_df)
        self.item_popularity = (
            self.sales_df["ProductID"].value_counts() / self.total_sales
        ).to_dict()

    def train_test_split(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Splits sales transactions randomly into train and test sets.
        """
        shuffled = self.sales_df.sample(frac=1.0, random_state=self.seed)
        split_idx = int(len(shuffled) * self.train_ratio)
        train_df = shuffled.iloc[:split_idx].copy()
        test_df = shuffled.iloc[split_idx:].copy()

        logger.info(
            f"Train/Test split: {len(train_df):,} train, {len(test_df):,} test records"
        )
        return train_df, test_df

    def build_eval_models(self, train_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, Dict, Dict, Dict, Dict]:
        """
        Builds the interaction matrix and similarity matrix using ONLY the train set.
        This prevents target leakage during evaluation.
        """
        logger.info("Building evaluation collaborative model from train transactions...")
        (
            interact_mat,
            c2i,
            i2c,
            p2i,
            i2p,
        ) = build_interaction_matrix(train_df)

        item_sim = compute_item_similarity(interact_mat)
        return item_sim, interact_mat, c2i, i2c, p2i, i2p

    # =========================================================================
    # METRICS IMPLEMENTATION
    # =========================================================================
    def calculate_precision_recall(
        self, recommendations: List[str], ground_truth: Set[str]
    ) -> Tuple[float, float]:
        """
        Computes Precision@K and Recall@K.

        Precision@K = (Recs in Ground Truth) / K
        Recall@K    = (Recs in Ground Truth) / Total Ground Truth Items
        """
        if not recommendations or not ground_truth:
            return 0.0, 0.0

        recs_set = set(recommendations)
        hits = len(recs_set & ground_truth)

        precision = hits / len(recommendations)
        recall = hits / len(ground_truth)

        return precision, recall

    def calculate_novelty(self, recommendations: List[str]) -> float:
        """
        Computes Novelty using Self-Information (Information Theory).

        Novelty(i) = -log2(P(i))
        Where P(i) is the probability of item i being purchased in the sales log.
        Popular items have high P(i) -> low novelty.
        Rare items have low P(i) -> high novelty.
        """
        if not recommendations:
            return 0.0

        novelty_sum = 0.0
        for pid in recommendations:
            prob = self.item_popularity.get(pid, 1.0 / self.total_sales)
            novelty_sum += -math.log2(prob)

        return novelty_sum / len(recommendations)

    def calculate_diversity(self, recommendations: List[str]) -> float:
        """
        Computes Diversity as Intra-List Distance (ILD).

        Diversity = Average (1 - content_similarity(i, j)) for all pairs (i, j).
        If similar items (e.g. all cotton shirts) are recommended, diversity is low (near 0).
        If different items (shirt, towel, saree) are recommended, diversity is high (near 1).
        """
        if not recommendations or len(recommendations) < 2 or self.content_sim is None:
            return 0.0

        # Translate ProductIDs to indexes using product catalogue ordering
        product_list = self.products_df["ProductID"].tolist()
        pid_to_idx = {pid: idx for idx, pid in enumerate(product_list)}

        sim_sum = 0.0
        pairs = 0

        for i in range(len(recommendations)):
            for j in range(i + 1, len(recommendations)):
                pid_i = recommendations[i]
                pid_j = recommendations[j]

                if pid_i in pid_to_idx and pid_j in pid_to_idx:
                    idx_i = pid_to_idx[pid_i]
                    idx_j = pid_to_idx[pid_j]
                    sim = self.content_sim[idx_i, idx_j]
                    # Distance is (1 - similarity)
                    sim_sum += (1.0 - sim)
                    pairs += 1

        return sim_sum / pairs if pairs > 0 else 0.0

    # =========================================================================
    # CORE EVALUATION LOOP
    # =========================================================================
    def evaluate(self, top_n: int = 10, sample_users: int = 100) -> Dict[str, Any]:
        """
        Orchestrates evaluation across a sample of customers.
        """
        train_df, test_df = self.train_test_split()
        item_sim, interact_mat, c2i, i2c, p2i, i2p = self.build_eval_models(train_df)

        # Get set of users present in both train and test sets
        eval_users = set(train_df["CustomerID"].unique()) & set(test_df["CustomerID"].unique())
        eval_users = sorted(list(eval_users))

        # Sample users to control compute footprint
        if len(eval_users) > sample_users:
            np.random.seed(self.seed)
            eval_users = np.random.choice(eval_users, size=sample_users, replace=False).tolist()

        logger.info(f"Evaluating models across {len(eval_users)} sampled test customers...")

        # Metrics accumulators
        precisions_collab = []
        recalls_collab = []
        novelties_collab = []
        diversities_collab = []

        precisions_hybrid = []
        recalls_hybrid = []
        novelties_hybrid = []
        diversities_hybrid = []

        unique_recs_collab: Set[str] = set()
        unique_recs_hybrid: Set[str] = set()

        for customer_id in eval_users:
            # 1. Get test set purchases as ground truth
            ground_truth = set(test_df[test_df["CustomerID"] == customer_id]["ProductID"].unique())
            if not ground_truth:
                continue

            # 2. Collaborative Filtering Recs
            collab_recs_raw = recommend_for_customer(
                customer_id=customer_id,
                item_similarity=item_sim,
                interaction_matrix=interact_mat,
                customer_to_idx=c2i,
                product_to_idx=p2i,
                idx_to_product=i2p,
                products_df=self.products_df,
                top_n=top_n,
            )
            collab_recs = [rec["ProductID"] for rec in collab_recs_raw]
            unique_recs_collab.update(collab_recs)

            p_col, r_col = self.calculate_precision_recall(collab_recs, ground_truth)
            precisions_collab.append(p_col)
            recalls_collab.append(r_col)
            novelties_collab.append(self.calculate_novelty(collab_recs))
            diversities_collab.append(self.calculate_diversity(collab_recs))

            # 3. Hybrid Model Recs
            hybrid_recs_raw = hybrid_recommend_for_customer(
                customer_id=customer_id,
                products_df=self.products_df,
                top_n=top_n,
            )
            hybrid_recs = [rec["ProductID"] for rec in hybrid_recs_raw]
            unique_recs_hybrid.update(hybrid_recs)

            p_hyb, r_hyb = self.calculate_precision_recall(hybrid_recs, ground_truth)
            precisions_hybrid.append(p_hyb)
            recalls_hybrid.append(r_hyb)
            novelties_hybrid.append(self.calculate_novelty(hybrid_recs))
            diversities_hybrid.append(self.calculate_diversity(hybrid_recs))

        # Catalog coverage calculations
        catalog_size = len(self.products_df)
        coverage_collab = len(unique_recs_collab) / catalog_size
        coverage_hybrid = len(unique_recs_hybrid) / catalog_size

        summary = {
            "top_k": top_n,
            "sample_users": len(eval_users),
            "collaborative_filtering": {
                "Precision@K": round(float(np.mean(precisions_collab)), 4),
                "Recall@K": round(float(np.mean(recalls_collab)), 4),
                "CatalogCoverage": round(coverage_collab, 4),
                "Novelty": round(float(np.mean(novelties_collab)), 4),
                "Diversity": round(float(np.mean(diversities_collab)), 4),
            },
            "hybrid_model": {
                "Precision@K": round(float(np.mean(precisions_hybrid)), 4),
                "Recall@K": round(float(np.mean(recalls_hybrid)), 4),
                "CatalogCoverage": round(coverage_hybrid, 4),
                "Novelty": round(float(np.mean(novelties_hybrid)), 4),
                "Diversity": round(float(np.mean(diversities_hybrid)), 4),
            }
        }

        return summary

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    evaluator = RecommenderEvaluator()
    summary = evaluator.evaluate(top_n=10, sample_users=150)

    print("\n" + "=" * 80)
    print("RECOMMANDATION SYSTEM EVALUATION RESULTS (K=10)")
    print("=" * 80)
    print(f"Sampled Users Evaluated: {summary['sample_users']}")
    print("-" * 80)

    metrics = ["Precision@K", "Recall@K", "CatalogCoverage", "Novelty", "Diversity"]
    print(f"{'Metric':<20} | {'Collaborative Filtering':<25} | {'Hybrid Model':<15}")
    print("-" * 80)
    for metric in metrics:
        collab_val = summary["collaborative_filtering"][metric]
        hybrid_val = summary["hybrid_model"][metric]
        print(f"{metric:<20} | {collab_val:<25} | {hybrid_val:<15}")
    print("=" * 80)
