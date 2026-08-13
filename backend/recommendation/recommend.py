"""
==============================================================================
API Wrapper / Interface Layer: recommend.py
==============================================================================
Purpose:
    Exposes a unified interface for the entire recommendation pipeline.
    This file acts as the single entry point for any external API or web
    interface (like a Flask/FastAPI backend) to fetch recommendations.

    All functions return clean, structured, JSON-friendly Python dictionaries
    or lists, ensuring they can be serialized easily over HTTP.

Functions:
    1. recommend_by_product(product_id)
       -> Hybrid recommendations when a user views a product page.
    2. recommend_for_customer(customer_id)
       -> Personalized hybrid recommendations for a returning customer.
    3. recommend_similar_products(product_name)
       -> Fuzzy searches for products matching the product_name and returns
          hybrid matches.
    4. recommend_cross_sell(product_id)
       -> Business rule-based cross-sell items to display on cart/checkout pages.
    5. recommend_new_customer(preferred_category)
       -> Popular/highly-rated products in a category to resolve the new customer
          cold-start issue.

ML Concepts:
    - Wrapper Pattern (Facade Design Pattern)
    - Cold-start resolution strategies
    - Fuzzy match/String similarity retrieval
==============================================================================
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Union, Optional

import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports from individual engines
from backend.recommendation.hybrid_model import (
    hybrid_recommend_by_product,
    hybrid_recommend_for_customer,
)
from backend.recommendation.business_rules import (
    get_rule_based_recommendations,
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
# DATA LOADING (Singleton pattern for pandas DataFrames)
# =============================================================================
_products_df: Optional[pd.DataFrame] = None
_sales_df: Optional[pd.DataFrame] = None

def get_products_df() -> pd.DataFrame:
    global _products_df
    if _products_df is None:
        if not os.path.exists(PRODUCTS_FILE):
            raise FileNotFoundError(f"Missing products data: {PRODUCTS_FILE}")
        _products_df = pd.read_csv(PRODUCTS_FILE)
    return _products_df

def get_sales_df() -> pd.DataFrame:
    global _sales_df
    if _sales_df is None:
        if not os.path.exists(SALES_FILE):
            raise FileNotFoundError(f"Missing sales data: {SALES_FILE}")
        _sales_df = pd.read_csv(SALES_FILE)
    return _sales_df

# =============================================================================
# 1. recommend_by_product
# =============================================================================
def recommend_by_product(product_id: str, top_n: int = 10) -> Dict[str, Any]:
    """
    Returns hybrid recommendations for a product. Used for product detail pages.

    Parameters
    ----------
    product_id : str
        The source product ID.
    top_n : int
        Number of recommendations.

    Returns
    -------
    Dict[str, Any]
        JSON-friendly dictionary containing query info and recommendations.
    """
    logger.info(f"recommend_by_product called for '{product_id}'")
    try:
        products_df = get_products_df()

        # Check if product exists
        if product_id not in products_df["ProductID"].values:
            return {
                "status": "error",
                "message": f"ProductID '{product_id}' does not exist in the catalogue.",
                "data": []
            }

        recs = hybrid_recommend_by_product(product_id, products_df, top_n=top_n)
        return {
            "status": "success",
            "query": {"product_id": product_id, "top_n": top_n},
            "data": recs
        }
    except Exception as e:
        logger.error(f"Error in recommend_by_product: {e}")
        return {"status": "error", "message": str(e), "data": []}

# =============================================================================
# 2. recommend_for_customer
# =============================================================================
def recommend_for_customer(customer_id: str, top_n: int = 10) -> Dict[str, Any]:
    """
    Returns personalized hybrid recommendations for a customer. Used for homepage feeds.

    Parameters
    ----------
    customer_id : str
        The customer ID.
    top_n : int
        Number of recommendations.

    Returns
    -------
    Dict[str, Any]
        JSON-friendly dictionary.
    """
    logger.info(f"recommend_for_customer called for '{customer_id}'")
    try:
        products_df = get_products_df()
        sales_df = get_sales_df()

        # If user does not exist in sales history, redirect them to new user cold-start
        # (Demographics profile could be fetched from customers database if available,
        # but here we default to fallback logic).
        if customer_id not in sales_df["CustomerID"].values:
            logger.info(f"New customer cold-start triggered for user '{customer_id}'")
            # Default fallback category is 'Men' (most common) or we pick popular overall
            fallback_recs = recommend_new_customer(preferred_category="Men", top_n=top_n)
            return {
                "status": "success",
                "mode": "cold_start_fallback",
                "query": {"customer_id": customer_id, "top_n": top_n},
                "data": fallback_recs["data"]
            }

        recs = hybrid_recommend_for_customer(customer_id, products_df, top_n=top_n)
        return {
            "status": "success",
            "mode": "personalized_hybrid",
            "query": {"customer_id": customer_id, "top_n": top_n},
            "data": recs
        }
    except Exception as e:
        logger.error(f"Error in recommend_for_customer: {e}")
        return {"status": "error", "message": str(e), "data": []}

# =============================================================================
# 3. recommend_similar_products
# =============================================================================
def recommend_similar_products(product_name: str, top_n: int = 10) -> Dict[str, Any]:
    """
    Looks up a product by name (fuzzy substring search) and returns similar items.
    Useful for search bar recommendations and auto-suggest blocks.

    Parameters
    ----------
    product_name : str
        Name query (e.g. "Veshti", "Raymond Shirt").
    top_n : int
        Number of recommendations.

    Returns
    -------
    Dict[str, Any]
        JSON-friendly dictionary.
    """
    logger.info(f"recommend_similar_products called for query: '{product_name}'")
    try:
        products_df = get_products_df()

        # Perform substring matching (case-insensitive) on ProductName
        matches = products_df[
            products_df["ProductName"].str.contains(product_name, case=False, na=False)
        ]

        if matches.empty:
            return {
                "status": "error",
                "message": f"No products matching name '{product_name}' were found.",
                "data": []
            }

        # Select the first match as the anchor product
        anchor_product = matches.iloc[0]
        anchor_id = anchor_product["ProductID"]
        anchor_full_name = anchor_product["ProductName"]

        logger.info(f"Fuzzy match resolved '{product_name}' -> '{anchor_full_name}' ({anchor_id})")

        recs = hybrid_recommend_by_product(anchor_id, products_df, top_n=top_n)
        return {
            "status": "success",
            "query": {
                "input_query": product_name,
                "resolved_product": anchor_full_name,
                "resolved_product_id": anchor_id,
                "top_n": top_n
            },
            "data": recs
        }
    except Exception as e:
        logger.error(f"Error in recommend_similar_products: {e}")
        return {"status": "error", "message": str(e), "data": []}

# =============================================================================
# 4. recommend_cross_sell
# =============================================================================
def recommend_cross_sell(product_id: str, top_n: int = 5) -> Dict[str, Any]:
    """
    Returns rule-based cross-sell recommendations. Used for cart/checkout pages.

    Parameters
    ----------
    product_id : str
        Source product.
    top_n : int
        Number of complementary items to return.

    Returns
    -------
    Dict[str, Any]
        JSON-friendly dictionary.
    """
    logger.info(f"recommend_cross_sell called for '{product_id}'")
    try:
        products_df = get_products_df()

        if product_id not in products_df["ProductID"].values:
            return {
                "status": "error",
                "message": f"ProductID '{product_id}' does not exist.",
                "data": []
            }

        recs = get_rule_based_recommendations(product_id, products_df, top_n=top_n)
        return {
            "status": "success",
            "query": {"product_id": product_id, "top_n": top_n},
            "data": recs
        }
    except Exception as e:
        logger.error(f"Error in recommend_cross_sell: {e}")
        return {"status": "error", "message": str(e), "data": []}

# =============================================================================
# 5. recommend_new_customer (Cold-start Resolver)
# =============================================================================
def recommend_new_customer(preferred_category: str, top_n: int = 10) -> Dict[str, Any]:
    """
    Resolves the new customer cold-start problem by suggesting popular products
    within their preferred Category.

    Popularity is calculated based on transaction counts in sales data.

    Parameters
    ----------
    preferred_category : str
        Category name (e.g. 'Men', 'Women', 'Kids', 'Home & Lifestyle', 'Accessories').
    top_n : int
        Number of recommendations.

    Returns
    -------
    Dict[str, Any]
        JSON-friendly dictionary.
    """
    logger.info(f"recommend_new_customer called for Category: '{preferred_category}'")
    try:
        products_df = get_products_df()
        sales_df = get_sales_df()

        # Clean/Normalize category name
        category_clean = preferred_category.strip().title()
        if category_clean == "Home & Lifestyle" or category_clean == "Home And Lifestyle":
            category_clean = "Home & Lifestyle"

        # Validate category
        valid_categories = products_df["Category"].unique()
        if category_clean not in valid_categories:
            return {
                "status": "error",
                "message": f"Invalid category '{preferred_category}'. Must be one of {list(valid_categories)}.",
                "data": []
            }

        # Calculate product popularity (sale transaction counts)
        popularity = sales_df["ProductID"].value_counts().reset_index(name="sales_count")

        # Filter products by category
        cat_products = products_df[products_df["Category"] == category_clean]

        # Merge with popularity score
        merged = pd.merge(cat_products, popularity, on="ProductID", how="left")
        merged["sales_count"] = merged["sales_count"].fillna(0)

        # Sort by popularity (sales count) descending
        popular_items = merged.sort_values("sales_count", ascending=False).head(top_n)

        results = []
        for _, row in popular_items.iterrows():
            results.append({
                "ProductID": str(row["ProductID"]),
                "ProductName": str(row["ProductName"]),
                "Category": str(row["Category"]),
                "SubCategory": str(row["SubCategory"]),
                "Brand": str(row["Brand"]),
                "Price": float(row["Price"]),
                "SalesCount": int(row["sales_count"]),
                "PopularityScore": round(float(row["sales_count"]) / popularity["sales_count"].max(), 4)
            })

        return {
            "status": "success",
            "query": {"preferred_category": category_clean, "top_n": top_n},
            "data": results
        }
    except Exception as e:
        logger.error(f"Error in recommend_new_customer: {e}")
        return {"status": "error", "message": str(e), "data": []}

# =============================================================================
# MAIN RUN (DEMO TESTING)
# =============================================================================
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TESTING Wrapper functions in recommend.py")
    print("=" * 80)

    # 1. Product detail page recommendation
    p_recs = recommend_by_product("P0001", top_n=3)
    print("\n[1] recommend_by_product('P0001'):")
    print(json.dumps(p_recs, indent=2)[:500] + "\n...\n")

    # 2. Personalized returning customer feed
    c_recs = recommend_for_customer("C00001", top_n=3)
    print("[2] recommend_for_customer('C00001'):")
    print(json.dumps(c_recs, indent=2)[:500] + "\n...\n")

    # 3. Fuzzy search match
    s_recs = recommend_similar_products("Veshti", top_n=3)
    print("[3] recommend_similar_products('Veshti'):")
    print(json.dumps(s_recs, indent=2)[:500] + "\n...\n")

    # 4. Cross-sell checkout
    x_recs = recommend_cross_sell("P0001", top_n=3)
    print("[4] recommend_cross_sell('P0001'):")
    print(json.dumps(x_recs, indent=2)[:500] + "\n...\n")

    # 5. Cold-start new customer profile
    n_recs = recommend_new_customer("Women", top_n=3)
    print("[5] recommend_new_customer('Women'):")
    print(json.dumps(n_recs, indent=2)[:500] + "\n...\n")
