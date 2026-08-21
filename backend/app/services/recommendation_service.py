"""
Recommendation Service (Self-Contained & Thread-Safe)
======================================================
Handles business logic for generating personalized product recommendations.
Performs hybrid scoring (Collaborative + Content-Based + Business Rules) using
numpy and pandas directly to bypass sklearn import hangs in Sandboxed environments.
"""

import logging
from typing import Dict, Any, List, Set
import numpy as np
import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import scipy.sparse

from app import models
from app.models_loader import load_recommendation_model

logger = logging.getLogger("recommendation_service")

# ═══════════════════════════════════════════════════════════════════════════════
# RETAIL BUSINESS RULES CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
COMPLEMENTARY_RULES: Dict[str, List[str]] = {
    "Shirts": ["Pants", "Belts", "Socks", "Towels"],
    "Pants": ["Shirts", "Belts", "Socks"],
    "Veshti": ["Towels", "Shirts", "Lungi"],
    "Political Veshti": ["Shirts", "Towels"],
    "Lungi": ["Towels", "Veshti"],
    "Sarees": ["Shree", "Puttu Vasti", "Belts"],
    "Shree": ["Sarees", "Puttu Vasti"],
    "Puttu Vasti": ["Sarees", "Shree"],
    "Kurtas": ["Pants", "Belts", "Dresses"],
    "Frocks": ["Belts", "Socks", "Baby Dresses"],
    "Dresses": ["Belts", "Socks", "Kurtas"],
    "School Uniforms": ["Socks", "Belts", "Towels"],
    "Baby Dresses": ["Gift Boxes", "Towels", "Socks"],
    "Gift Boxes": ["Baby Dresses", "Towels", "Bed Covers"],
    "IPL Jerseys": ["Towels", "Socks"],
    "Socks": ["Shirts", "Pants", "School Uniforms", "Belts"],
    "Belts": ["Shirts", "Pants", "School Uniforms", "Socks"],
    "Raincoats": ["Umbrellas"],
    "Umbrellas": ["Raincoats"],
    "Bedsheets": ["Pillow Covers", "Bed Covers", "Curtains"],
    "Bed Covers": ["Pillow Covers", "Bedsheets", "Curtains"],
    "Pillow Covers": ["Bedsheets", "Bed Covers", "Curtains"],
    "Curtains": ["Bedsheets", "Pillow Covers", "Bed Covers"],
    "Towels": ["Veshti", "Lungi", "Shirts", "Gift Boxes"],
}

SEASONAL_RULES: Dict[str, List[str]] = {
    "Pongal": ["Veshti", "Sarees", "Shree", "Towels", "Gift Boxes"],
    "Diwali": ["Sarees", "Kurtas", "Shree", "Gift Boxes", "Dresses"],
    "Summer": ["Lungi", "Towels", "Baby Dresses", "Frocks"],
    "Aadi Sale": ["Sarees", "Bed Covers", "Bedsheets", "Curtains"],
    "School Season": ["School Uniforms", "Socks", "Belts", "Towels"],
    "Wedding Season": ["Sarees", "Shree", "Puttu Vasti", "Veshti", "Shirts"],
    "Temple Festival": ["Veshti", "Sarees", "Shree", "Puttu Vasti"],
    "Independence Day": ["IPL Jerseys", "Political Veshti", "Shirts"],
    "All Season": [],
}


def _normalize_scores(scores_dict: Dict[str, float]) -> Dict[str, float]:
    """Helper to min-max normalize scores to range [0, 1]."""
    if not scores_dict:
        return {}
    vals = list(scores_dict.values())
    min_val = min(vals)
    max_val = max(vals)
    if max_val == min_val:
        return {k: 1.0 for k in scores_dict}
    return {k: (v - min_val) / (max_val - min_val) for k, v in scores_dict.items()}


def get_personalized_recommendations(db: Session, customer_id: str, top_n: int = 10) -> Dict[str, Any]:
    """
    Generates Top 10 personalized product recommendations for a customer.
    
    Logic:
        1. Verify customer exists in MySQL.
        2. Retrieve customer's purchase history from MySQL.
        3. If history exists, run our mathematically equivalent Hybrid (Collab + Content + Rules) calculations.
        4. If history is empty, run Preferred Category cold start fallback.
    """
    # 1. Verify customer exists in MySQL
    customer = db.query(models.Customer).filter(models.Customer.CustomerID == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found in the system."
        )

    # 2. Retrieve purchase history from MySQL
    db_sales = db.query(models.Sale).filter(models.Sale.CustomerID == customer_id).all()
    purchased_pids = [s.ProductID for s in db_sales]

    # Load all products from MySQL database
    db_products = db.query(models.Product).all()
    if not db_products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product catalogue is empty."
        )
    
    products_list = []
    for p in db_products:
        products_list.append({
            "ProductID": p.ProductID,
            "ProductName": p.ProductName,
            "Category": p.Category,
            "SubCategory": p.SubCategory,
            "Brand": p.Brand,
            "Price": p.Price,
            "Fabric": p.Fabric,
            "Color": p.Color,
            "Gender": p.Gender,
            "SeasonalDemandTag": p.SeasonalDemandTag
        })
    products_df = pd.DataFrame(products_list)

    # 3. Generate recommendations
    recommended_list = []
    if not purchased_pids:
        # COLD START FALLBACK: Pick popular products matching preferred category
        pref_cat = customer.PreferredCategory or "Men"
        logger.info(f"Cold-start triggered for customer '{customer_id}' using category '{pref_cat}'")
        
        # Select products in preferred category, ordered by price descending or other proxy
        candidates = products_df[products_df["Category"] == pref_cat].head(top_n)
        for _, row in candidates.iterrows():
            recommended_list.append({
                "ProductID": str(row["ProductID"]),
                "ProductName": str(row["ProductName"]),
                "Score": 0.85
            })
    else:
        # HYBRID ENGINE
        logger.info(f"Computing personalized recommendations for customer '{customer_id}'")
        rec_model = load_recommendation_model()

        required_keys = [
            "collab_item_similarity", "collab_interaction_matrix",
            "collab_index_maps", "content_similarity_matrix", "product_index_map"
        ]
        has_valid_model = rec_model and all(k in rec_model for k in required_keys)

        if not has_valid_model:
            logger.warning(f"Recommendation model empty or incomplete. Triggering cold-start fallback for customer '{customer_id}'.")
            pref_cat = customer.PreferredCategory or "Men"
            candidates = products_df[
                (products_df["Category"] == pref_cat) & 
                (~products_df["ProductID"].isin(purchased_pids))
            ].head(top_n)
            
            if candidates.empty:
                candidates = products_df[~products_df["ProductID"].isin(purchased_pids)].head(top_n)

            for _, row in candidates.iterrows():
                recommended_list.append({
                    "ProductID": str(row["ProductID"]),
                    "ProductName": str(row["ProductName"]),
                    "Score": 0.85
                })
        else:
            collab_sim = rec_model["collab_item_similarity"]
            interact_mat = rec_model["collab_interaction_matrix"]
            c2i = rec_model["collab_index_maps"].get("customer_to_idx", {})
            i2p = rec_model["collab_index_maps"].get("idx_to_product", {})
            p2i = rec_model["collab_index_maps"].get("product_to_idx", {})

            c_sim = rec_model["content_similarity_matrix"]
            c_p2i = rec_model["product_index_map"].get("product_id_to_index", {})
            c_i2p = rec_model["product_index_map"].get("index_to_product_id", {})

            collab_dict = {}
            content_dict = {}
            rule_scores = {}
            last_purchase_pid = None

            if customer_id in c2i:
                c_idx = c2i[customer_id]
                # Handle sparse or dense interaction matrix
                if scipy.sparse.issparse(interact_mat):
                    customer_vector = interact_mat[c_idx].toarray()[0]
                else:
                    customer_vector = interact_mat[c_idx]

                purchased_indices = np.where(customer_vector > 0)[0]

                if len(purchased_indices) > 0:
                    # 1. Collaborative Filtering Scores
                    collab_scores = collab_sim.dot(customer_vector)
                    collab_scores[purchased_indices] = 0.0  # Zero out purchased
                    
                    # Get top 50 collaborative candidates
                    top_collab_indices = np.argsort(collab_scores)[::-1][:50]
                    collab_dict = {
                        i2p[idx]: float(collab_scores[idx]) 
                        for idx in top_collab_indices if idx in i2p and collab_scores[idx] > 0
                    }

                    # 2. Content-Based Scores
                    content_scores = np.zeros(len(products_df))
                    for idx in purchased_indices:
                        if idx in i2p:
                            pid = i2p[idx]
                            if pid in c_p2i:
                                c_idx_p = c_p2i[pid]
                                content_scores += c_sim[c_idx_p] * customer_vector[idx]

                    # Zero out purchased in content index matching
                    purchased_content_indices = [c_p2i[i2p[idx]] for idx in purchased_indices if idx in i2p and i2p[idx] in c_p2i]
                    content_scores[purchased_content_indices] = 0.0
                    
                    top_content_indices = np.argsort(content_scores)[::-1][:50]
                    content_dict = {
                        c_i2p[idx]: float(content_scores[idx])
                        for idx in top_content_indices if idx in c_i2p and content_scores[idx] > 0
                    }

                    # 3. Last Purchase Business Rules
                    last_purchase_idx = purchased_indices[-1]
                    if last_purchase_idx in i2p:
                        last_purchase_pid = i2p[last_purchase_idx]

            # Extract last purchase characteristics
            if last_purchase_pid:
                source_row = products_df[products_df["ProductID"] == last_purchase_pid]
                if not source_row.empty:
                    source = source_row.iloc[0]
                    source_subcat = str(source.get("SubCategory", "Unknown"))
                    source_brand = str(source.get("Brand", "Unknown"))
                    source_gender = str(source.get("Gender", "Unknown"))
                    source_fabric = str(source.get("Fabric", "Unknown"))
                    source_seasonal = str(source.get("SeasonalDemandTag", ""))

                    # Build complementary subcategories
                    complements = set()
                    if source_subcat in COMPLEMENTARY_RULES:
                        complements.update(COMPLEMENTARY_RULES[source_subcat])
                    for k, v in COMPLEMENTARY_RULES.items():
                        if source_subcat in v and k != source_subcat:
                            complements.add(k)
                    complements.discard(source_subcat)

                    # Build seasonal subcategories
                    seasonal = set()
                    if source_seasonal and not pd.isna(source_seasonal):
                        festivals = [f.strip() for f in str(source_seasonal).split(",")]
                        for fest in festivals:
                            if fest in SEASONAL_RULES:
                                seasonal.update(SEASONAL_RULES[fest])

                    all_rule_subcats = complements | seasonal

                    # Filter candidate catalog products
                    candidates = products_df[
                        products_df["SubCategory"].isin(all_rule_subcats) & 
                        (products_df["ProductID"] != last_purchase_pid)
                    ]

                    # Score rule candidates
                    for _, row in candidates.iterrows():
                        cand_pid = str(row["ProductID"])
                        if cand_pid in purchased_pids:
                            continue
                        
                        cand_subcat = str(row["SubCategory"])
                        score = 0.8 if cand_subcat in complements else 0.5
                        
                        if str(row["Brand"]) == source_brand:
                            score += 0.10
                        if str(row["Gender"]) == source_gender:
                            score += 0.05
                        if str(row["Fabric"]) == source_fabric:
                            score += 0.03
                        
                        rule_scores[cand_pid] = score

            # Normalize score sets
            norm_collab = _normalize_scores(collab_dict)
            norm_content = _normalize_scores(content_dict)
            norm_rules = _normalize_scores(rule_scores)

            # Merge and compute final weighted scores
            all_candidate_pids = set(norm_collab.keys()) | set(norm_content.keys()) | set(norm_rules.keys())
            hybrid_scores = {}
            for pid in all_candidate_pids:
                if pid in purchased_pids:
                    continue
                
                s_collab = norm_collab.get(pid, 0.0)
                s_content = norm_content.get(pid, 0.0)
                s_rules = norm_rules.get(pid, 0.0)
                
                hybrid_scores[pid] = 0.4 * s_collab + 0.4 * s_content + 0.2 * s_rules

            # Sort and select Top-N
            sorted_pids = sorted(hybrid_scores.keys(), key=lambda x: hybrid_scores[x], reverse=True)[:top_n]
            
            for pid in sorted_pids:
                product_row = products_df[products_df["ProductID"] == pid]
                if not product_row.empty:
                    recommended_list.append({
                        "ProductID": pid,
                        "ProductName": str(product_row.iloc[0]["ProductName"]),
                        "Score": round(hybrid_scores[pid], 2)
                    })

            # If hybrid scoring produced fewer than top_n recommendations, fill with category items
            if len(recommended_list) < top_n:
                existing_pids = {r["ProductID"] for r in recommended_list} | set(purchased_pids)
                pref_cat = customer.PreferredCategory or "Men"
                fallback_candidates = products_df[
                    (products_df["Category"] == pref_cat) & 
                    (~products_df["ProductID"].isin(existing_pids))
                ].head(top_n - len(recommended_list))

                if len(fallback_candidates) < (top_n - len(recommended_list)):
                    fallback_candidates = products_df[~products_df["ProductID"].isin(existing_pids)].head(top_n - len(recommended_list))

                for _, row in fallback_candidates.iterrows():
                    recommended_list.append({
                        "ProductID": str(row["ProductID"]),
                        "ProductName": str(row["ProductName"]),
                        "Score": 0.70
                    })

    return {
        "customer_id": customer_id,
        "recommended_products": recommended_list
    }
