"""
==============================================================================
Business Rule-Based Recommendation Engine
==============================================================================
Purpose:
    Recommends COMPLEMENTARY products based on predefined textile retail
    domain rules.  These are NOT learned from data — they encode expert
    knowledge about what products go together in an Indian textile store.

    When a customer buys a Shirt, they NEED Pants, a Belt, and Socks.
    When a customer buys a Saree, they NEED a Blouse (Shree/Puttu Vasti).
    When it rains, Raincoat buyers also need Umbrellas.

    No ML algorithm can reliably discover these "obvious" associations
    from sparse data — so we hardcode them as business rules.

Real-world examples:
    Amazon   -> "Frequently bought together" (partial business rules)
    McDonald's -> "Would you like fries with that?" (classic cross-sell)
    Myntra   -> "Complete the look" (outfit-based rules)
    IKEA     -> "Customers also needed" (furniture + accessories)

Why business rules exist alongside ML:
    1. ML models may miss OBVIOUS pairings due to data sparsity
    2. Business teams want CONTROL over certain recommendations
    3. Rules can encode SEASONAL and FESTIVAL logic
    4. Rules are INSTANT — no training, no computation
    5. Rules handle NEW product categories before ML has enough data
==============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set

import pandas as pd

# =============================================================================
# PATH SETUP
# =============================================================================
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =============================================================================
# CONSTANTS
# =============================================================================
PRODUCTS_FILE: str = os.path.join(
    PROJECT_ROOT, "data", "processed", "products_clean.csv"
)

# Default number of recommendations
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
# CORE DATA STRUCTURE: COMPLEMENTARY PRODUCT RULES
# =============================================================================
# -------------------------------------------------------------------------
# Rule format:  "SubCategory" -> ["Complement1", "Complement2", ...]
#
# These rules encode DOMAIN EXPERTISE about Indian textile retail:
#   - What products are NEEDED together (functional complement)
#   - What products LOOK GOOD together (fashion complement)
#   - What products are SEASONALLY related
#
# The rules are BIDIRECTIONAL-aware but stored UNIDIRECTIONAL.
# The lookup function checks both directions.
#
# These rules are based on the 24 SubCategories in our dataset:
#   Men:        Veshti, Lungi, Political Veshti, Pants, Towels, Shirts
#   Women:      Kurtas, Shree, Frocks, Puttu Vasti, Sarees, Dresses
#   Home:       Bed Covers, Pillow Covers, Bedsheets, Curtains
#   Kids:       Baby Dresses, Gift Boxes, School Uniforms
#   Accessories: IPL Jerseys, Towels, Socks, Raincoats, Umbrellas, Belts
# -------------------------------------------------------------------------

COMPLEMENTARY_RULES: Dict[str, List[str]] = {
    # ==========================
    # MEN'S WEAR RULES
    # ==========================

    # Shirt -> Pants, Belt, Socks (formal/casual outfit)
    "Shirts": ["Pants", "Belts", "Socks", "Towels"],

    # Pants -> Shirt, Belt, Socks
    "Pants": ["Shirts", "Belts", "Socks"],

    # Veshti (traditional Tamil men's garment) -> Towel, Shirts
    # In South Indian textile stores, Veshti + Towel is the classic combo
    "Veshti": ["Towels", "Shirts", "Lungi"],

    # Political Veshti (used in political/formal events) -> Shirts, Towels
    "Political Veshti": ["Shirts", "Towels"],

    # Lungi (casual home wear) -> Towels, Veshti
    "Lungi": ["Towels", "Veshti"],

    # ==========================
    # WOMEN'S WEAR RULES
    # ==========================

    # Sarees -> Blouse piece (Shree/Puttu Vasti), Petticoat
    # In Tamil Nadu textile stores, Saree + Blouse material is the
    # most fundamental cross-sell pairing
    "Sarees": ["Shree", "Puttu Vasti", "Belts"],

    # Shree (blouse material) -> Sarees, Puttu Vasti
    "Shree": ["Sarees", "Puttu Vasti"],

    # Puttu Vasti (traditional blouse) -> Sarees
    "Puttu Vasti": ["Sarees", "Shree"],

    # Kurtas (women's) -> Pants, Dresses, Belts
    "Kurtas": ["Pants", "Belts", "Dresses"],

    # Frocks -> Belts, Socks (kids/women)
    "Frocks": ["Belts", "Socks", "Baby Dresses"],

    # Dresses -> Belts, Socks
    "Dresses": ["Belts", "Socks", "Kurtas"],

    # ==========================
    # KIDS' WEAR RULES
    # ==========================

    # School Uniforms -> Socks, Belts (mandatory school accessories)
    # Every parent buying school uniforms NEEDS socks and belts
    "School Uniforms": ["Socks", "Belts", "Towels"],

    # Baby Dresses -> Gift Boxes (baby shower / gifting)
    "Baby Dresses": ["Gift Boxes", "Towels", "Socks"],

    # Gift Boxes -> Baby Dresses, Towels (common gift items)
    "Gift Boxes": ["Baby Dresses", "Towels", "Bed Covers"],

    # ==========================
    # ACCESSORIES RULES
    # ==========================

    # IPL Jerseys -> Towels (sports merchandise combo)
    "IPL Jerseys": ["Towels", "Socks"],

    # Socks -> Shirts, Pants, School Uniforms, Belts
    "Socks": ["Shirts", "Pants", "School Uniforms", "Belts"],

    # Belts -> Shirts, Pants, School Uniforms
    "Belts": ["Shirts", "Pants", "School Uniforms", "Socks"],

    # Raincoats -> Umbrellas (monsoon combo — classic cross-sell)
    "Raincoats": ["Umbrellas"],

    # Umbrellas -> Raincoats
    "Umbrellas": ["Raincoats"],

    # ==========================
    # HOME & LIFESTYLE RULES
    # ==========================

    # Bedsheets -> Pillow Covers, Bed Covers, Curtains
    "Bedsheets": ["Pillow Covers", "Bed Covers", "Curtains"],

    # Bed Covers -> Pillow Covers, Bedsheets, Curtains
    "Bed Covers": ["Pillow Covers", "Bedsheets", "Curtains"],

    # Pillow Covers -> Bedsheets, Bed Covers, Curtains
    "Pillow Covers": ["Bedsheets", "Bed Covers", "Curtains"],

    # Curtains -> Bedsheets, Pillow Covers, Bed Covers
    "Curtains": ["Bedsheets", "Pillow Covers", "Bed Covers"],

    # ==========================
    # TOWELS (cross-category)
    # ==========================
    # Towels are universal — paired with many categories
    "Towels": ["Veshti", "Lungi", "Shirts", "Gift Boxes"],
}


# =============================================================================
# SEASONAL RULES
# =============================================================================
# These rules activate based on the SeasonalDemandTag of the source product.
# If a customer is buying a "Pongal" product, also show them other Pongal items.

SEASONAL_RULES: Dict[str, List[str]] = {
    "Pongal": ["Veshti", "Sarees", "Shree", "Towels", "Gift Boxes"],
    "Diwali": ["Sarees", "Kurtas", "Shree", "Gift Boxes", "Dresses"],
    "Summer": ["Lungi", "Towels", "Baby Dresses", "Frocks"],
    "Aadi Sale": ["Sarees", "Bed Covers", "Bedsheets", "Curtains"],
    "School Season": ["School Uniforms", "Socks", "Belts", "Towels"],
    "Wedding Season": ["Sarees", "Shree", "Puttu Vasti", "Veshti", "Shirts"],
    "Temple Festival": ["Veshti", "Sarees", "Shree", "Puttu Vasti"],
    "Independence Day": ["IPL Jerseys", "Political Veshti", "Shirts"],
    "All Season": [],  # No special seasonal push
}


# =============================================================================
# FUNCTION 1: load_products()
# =============================================================================
def load_products(file_path: str = PRODUCTS_FILE) -> pd.DataFrame:
    """Load the cleaned products dataset."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Products file not found: {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Loaded products: {df.shape[0]} rows x {df.shape[1]} columns")
    return df


# =============================================================================
# FUNCTION 2: get_complementary_subcategories()
# =============================================================================
def get_complementary_subcategories(
    subcategory: str,
    rules: Dict[str, List[str]] = COMPLEMENTARY_RULES,
) -> List[str]:
    """
    Given a SubCategory, return the list of complementary SubCategories.

    How it works:
        1. Direct lookup: Check if the subcategory has rules defined.
        2. Reverse lookup: Also check if OTHER subcategories list
           this one as a complement (bidirectional discovery).
        3. Deduplicate and return.

    Parameters
    ----------
    subcategory : str
        The source product's SubCategory (e.g. "Shirts").
    rules : Dict
        The complementary rules dictionary.

    Returns
    -------
    List[str]
        Complementary SubCategories (e.g. ["Pants", "Belts", "Socks"]).
    """
    complements: Set[str] = set()

    # Direct lookup
    if subcategory in rules:
        complements.update(rules[subcategory])

    # Reverse lookup — if "Pants" lists "Shirts" as complement,
    # then "Shirts" should also suggest "Pants"
    for source, targets in rules.items():
        if subcategory in targets and source != subcategory:
            complements.add(source)

    # Remove self-reference (shouldn't happen, but defensive coding)
    complements.discard(subcategory)

    return sorted(list(complements))


# =============================================================================
# FUNCTION 3: get_seasonal_subcategories()
# =============================================================================
def get_seasonal_subcategories(
    seasonal_tag: str,
    rules: Dict[str, List[str]] = SEASONAL_RULES,
) -> List[str]:
    """
    Given a product's SeasonalDemandTag, return seasonally relevant
    SubCategories.

    The SeasonalDemandTag field can contain MULTIPLE festivals:
        "Pongal, Temple Festival, Summer"

    We split by comma, look up each festival, and merge results.

    Parameters
    ----------
    seasonal_tag : str
        The product's SeasonalDemandTag (may be comma-separated).
    rules : Dict
        The seasonal rules dictionary.

    Returns
    -------
    List[str]
        Seasonally relevant SubCategories.
    """
    if not seasonal_tag or pd.isna(seasonal_tag):
        return []

    complements: Set[str] = set()

    # Split multi-festival tags: "Pongal, Temple Festival, Summer"
    festivals = [f.strip() for f in str(seasonal_tag).split(",")]

    for festival in festivals:
        if festival in rules:
            complements.update(rules[festival])

    return sorted(list(complements))


# =============================================================================
# FUNCTION 4: get_rule_based_recommendations()
# =============================================================================
def get_rule_based_recommendations(
    product_id: str,
    products_df: pd.DataFrame,
    top_n: int = DEFAULT_TOP_N,
    include_seasonal: bool = True,
) -> List[Dict]:
    """
    Generate recommendations using business rules for a given product.

    Algorithm:
        1. Look up the source product's SubCategory and SeasonalDemandTag.
        2. Get complementary SubCategories from rules.
        3. Optionally get seasonal SubCategories.
        4. Find products in those SubCategories from the catalogue.
        5. Score them based on rule priority and attribute matching.
        6. Return Top-N results.

    Scoring logic:
        - Complementary match:  base score = 0.8
        - Seasonal match:       base score = 0.5
        - Same Brand bonus:     +0.1 (customers prefer same brand)
        - Same Gender bonus:    +0.05 (gender-appropriate suggestions)
        - Same Fabric bonus:    +0.03 (fabric preference continuity)

    Why these scores?
        Business rules should have a STRONG baseline score (0.8)
        because they represent CERTAIN need (Shirt NEEDS Pants).
        Seasonal rules are softer (0.5) — nice to have, not essential.
        Brand/Gender/Fabric bonuses reward coherent recommendations.

    Parameters
    ----------
    product_id : str
        The source product ID.
    products_df : pd.DataFrame
        Full products catalogue.
    top_n : int
        Number of recommendations.
    include_seasonal : bool
        Whether to include seasonal rule matches.

    Returns
    -------
    List[Dict]
        Recommended complementary products with scores.
    """
    # -------------------------------------------------------------------------
    # Step 1: Find the source product
    # -------------------------------------------------------------------------
    source_row = products_df[products_df["ProductID"] == product_id]
    if source_row.empty:
        logger.warning(f"Product '{product_id}' not found in catalogue")
        return []

    source = source_row.iloc[0]
    source_subcat = str(source.get("SubCategory", "Unknown"))
    source_brand = str(source.get("Brand", "Unknown"))
    source_gender = str(source.get("Gender", "Unknown"))
    source_fabric = str(source.get("Fabric", "Unknown"))
    source_seasonal = str(source.get("SeasonalDemandTag", ""))

    # -------------------------------------------------------------------------
    # Step 2: Get complementary and seasonal SubCategories
    # -------------------------------------------------------------------------
    complement_subcats = get_complementary_subcategories(source_subcat)
    seasonal_subcats = (
        get_seasonal_subcategories(source_seasonal) if include_seasonal else []
    )

    # Combine — complementary gets priority
    all_target_subcats = set(complement_subcats) | set(seasonal_subcats)

    if not all_target_subcats:
        logger.info(f"No business rules defined for SubCategory '{source_subcat}'")
        return []

    # -------------------------------------------------------------------------
    # Step 3: Find candidate products in target SubCategories
    # -------------------------------------------------------------------------
    candidates = products_df[
        (products_df["SubCategory"].isin(all_target_subcats))
        & (products_df["ProductID"] != product_id)  # exclude self
    ].copy()

    if candidates.empty:
        logger.info(f"No candidate products found for rules of '{source_subcat}'")
        return []

    # -------------------------------------------------------------------------
    # Step 4: Score each candidate
    # -------------------------------------------------------------------------
    scores: List[float] = []

    for _, cand in candidates.iterrows():
        score = 0.0
        cand_subcat = str(cand.get("SubCategory", ""))

        # Base score: complementary (0.8) vs seasonal-only (0.5)
        if cand_subcat in complement_subcats:
            score = 0.8
        elif cand_subcat in seasonal_subcats:
            score = 0.5

        # Bonus: Same brand (+0.1)
        if str(cand.get("Brand", "")) == source_brand:
            score += 0.10

        # Bonus: Same gender (+0.05)
        if str(cand.get("Gender", "")) == source_gender:
            score += 0.05

        # Bonus: Same fabric (+0.03)
        if str(cand.get("Fabric", "")) == source_fabric:
            score += 0.03

        scores.append(score)

    candidates = candidates.copy()
    candidates["RuleScore"] = scores

    # -------------------------------------------------------------------------
    # Step 5: Sort by score (descending) and return Top-N
    # -------------------------------------------------------------------------
    candidates = candidates.sort_values("RuleScore", ascending=False).head(top_n)

    results: List[Dict] = []
    for _, row in candidates.iterrows():
        results.append({
            "ProductID": str(row["ProductID"]),
            "ProductName": str(row.get("ProductName", "Unknown")),
            "Category": str(row.get("Category", "Unknown")),
            "SubCategory": str(row.get("SubCategory", "Unknown")),
            "Brand": str(row.get("Brand", "Unknown")),
            "Price": float(row.get("Price", 0)),
            "RuleScore": round(float(row["RuleScore"]), 4),
            "RuleType": (
                "Complementary"
                if str(row.get("SubCategory", "")) in complement_subcats
                else "Seasonal"
            ),
        })

    logger.info(
        f"Business rules: {len(results)} recs for '{product_id}' "
        f"(SubCat: {source_subcat})"
    )
    return results


# =============================================================================
# FUNCTION 5: get_cross_sell_recommendations()
# =============================================================================
def get_cross_sell_recommendations(
    product_ids: List[str],
    products_df: pd.DataFrame,
    top_n: int = DEFAULT_TOP_N,
) -> List[Dict]:
    """
    Cross-sell recommendations for a BASKET of products (e.g. cart items).

    When a customer has multiple products in their cart, we find
    complementary products for ALL of them, deduplicate, and rank.

    This is like Flipkart's "Complete your order" section.

    Algorithm:
        1. For each product in the cart, get rule-based recommendations.
        2. Aggregate scores: if a product is recommended by multiple
           cart items, its scores are summed (stronger signal).
        3. Exclude products already in the cart.
        4. Return Top-N.

    Parameters
    ----------
    product_ids : List[str]
        List of ProductIDs in the customer's cart.
    products_df : pd.DataFrame
        Full products catalogue.
    top_n : int
        Number of recommendations.

    Returns
    -------
    List[Dict]
        Cross-sell recommendations ranked by aggregated score.
    """
    # Aggregate scores across all cart items
    score_map: Dict[str, float] = {}
    info_map: Dict[str, Dict] = {}

    for pid in product_ids:
        recs = get_rule_based_recommendations(pid, products_df, top_n=50)
        for rec in recs:
            rec_pid = rec["ProductID"]
            if rec_pid in product_ids:
                continue  # Skip items already in cart

            if rec_pid not in score_map:
                score_map[rec_pid] = 0.0
                info_map[rec_pid] = rec
            score_map[rec_pid] += rec["RuleScore"]

    # Sort by aggregated score
    sorted_pids = sorted(score_map.keys(), key=lambda x: score_map[x], reverse=True)

    results: List[Dict] = []
    for pid in sorted_pids[:top_n]:
        entry = info_map[pid].copy()
        entry["RuleScore"] = round(score_map[pid], 4)
        entry["RuleType"] = "CrossSell"
        results.append(entry)

    logger.info(
        f"Cross-sell: {len(results)} recs for cart of {len(product_ids)} items"
    )
    return results


# =============================================================================
# FUNCTION 6: get_all_rules_summary()
# =============================================================================
def get_all_rules_summary() -> Dict[str, Dict]:
    """
    Return a summary of all business rules for documentation/debugging.

    Returns
    -------
    Dict with:
        - complementary_rules: Dict of SubCategory -> complements
        - seasonal_rules: Dict of Season -> relevant SubCategories
        - total_complementary_rules: count
        - total_seasonal_rules: count
    """
    return {
        "complementary_rules": COMPLEMENTARY_RULES,
        "seasonal_rules": SEASONAL_RULES,
        "total_complementary_rules": len(COMPLEMENTARY_RULES),
        "total_seasonal_rules": len(SEASONAL_RULES),
        "total_subcategories_covered": len(COMPLEMENTARY_RULES),
    }


# =============================================================================
# MAIN ENTRY POINT  —  Demo when run directly
# =============================================================================
if __name__ == "__main__":
    products_df = load_products()

    # =========================================================================
    # Demo 1: Complementary products for a Shirt
    # =========================================================================
    # Find a Shirt product
    shirt_row = products_df[products_df["SubCategory"] == "Shirts"].iloc[0]
    shirt_id = shirt_row["ProductID"]

    print(f"\n{'='*65}")
    print(f"DEMO 1: Complementary products for {shirt_id}")
    print(f"  Source: {shirt_row['ProductName']} ({shirt_row['SubCategory']})")
    print(f"  Rule: Shirts -> {COMPLEMENTARY_RULES.get('Shirts', [])}")
    print(f"{'='*65}")

    recs = get_rule_based_recommendations(shirt_id, products_df, top_n=5)
    for i, rec in enumerate(recs, 1):
        print(
            f"  {i}. {rec['ProductID']} | {rec['ProductName']:<35} | "
            f"{rec['SubCategory']:<18} | Rs.{rec['Price']:>8,.0f} | "
            f"Score: {rec['RuleScore']:.2f} | {rec['RuleType']}"
        )

    # =========================================================================
    # Demo 2: Complementary products for a Saree
    # =========================================================================
    saree_row = products_df[products_df["SubCategory"] == "Sarees"].iloc[0]
    saree_id = saree_row["ProductID"]

    print(f"\n{'='*65}")
    print(f"DEMO 2: Complementary products for {saree_id}")
    print(f"  Source: {saree_row['ProductName']} ({saree_row['SubCategory']})")
    print(f"  Rule: Sarees -> {COMPLEMENTARY_RULES.get('Sarees', [])}")
    print(f"{'='*65}")

    recs = get_rule_based_recommendations(saree_id, products_df, top_n=5)
    for i, rec in enumerate(recs, 1):
        print(
            f"  {i}. {rec['ProductID']} | {rec['ProductName']:<35} | "
            f"{rec['SubCategory']:<18} | Rs.{rec['Price']:>8,.0f} | "
            f"Score: {rec['RuleScore']:.2f} | {rec['RuleType']}"
        )

    # =========================================================================
    # Demo 3: School Uniform cross-sell
    # =========================================================================
    uniform_row = products_df[products_df["SubCategory"] == "School Uniforms"].iloc[0]
    uniform_id = uniform_row["ProductID"]

    print(f"\n{'='*65}")
    print(f"DEMO 3: School Uniform -> Accessories")
    print(f"  Source: {uniform_row['ProductName']}")
    print(f"  Rule: School Uniforms -> {COMPLEMENTARY_RULES.get('School Uniforms', [])}")
    print(f"{'='*65}")

    recs = get_rule_based_recommendations(uniform_id, products_df, top_n=5)
    for i, rec in enumerate(recs, 1):
        print(
            f"  {i}. {rec['ProductID']} | {rec['ProductName']:<35} | "
            f"{rec['SubCategory']:<18} | Rs.{rec['Price']:>8,.0f} | "
            f"Score: {rec['RuleScore']:.2f} | {rec['RuleType']}"
        )

    # =========================================================================
    # Demo 4: Raincoat -> Umbrella
    # =========================================================================
    rain_row = products_df[products_df["SubCategory"] == "Raincoats"].iloc[0]
    rain_id = rain_row["ProductID"]

    print(f"\n{'='*65}")
    print(f"DEMO 4: Raincoat -> Umbrella (Monsoon combo)")
    print(f"  Source: {rain_row['ProductName']}")
    print(f"  Rule: Raincoats -> {COMPLEMENTARY_RULES.get('Raincoats', [])}")
    print(f"{'='*65}")

    recs = get_rule_based_recommendations(rain_id, products_df, top_n=5)
    for i, rec in enumerate(recs, 1):
        print(
            f"  {i}. {rec['ProductID']} | {rec['ProductName']:<35} | "
            f"{rec['SubCategory']:<18} | Rs.{rec['Price']:>8,.0f} | "
            f"Score: {rec['RuleScore']:.2f} | {rec['RuleType']}"
        )

    # =========================================================================
    # Demo 5: Cross-sell for a cart with Veshti + Saree
    # =========================================================================
    veshti_id = products_df[products_df["SubCategory"] == "Veshti"].iloc[0]["ProductID"]

    print(f"\n{'='*65}")
    print(f"DEMO 5: Cross-sell for cart [{veshti_id}, {saree_id}]")
    print(f"  Cart: Veshti + Saree")
    print(f"{'='*65}")

    cross_recs = get_cross_sell_recommendations(
        [veshti_id, saree_id], products_df, top_n=5
    )
    for i, rec in enumerate(cross_recs, 1):
        print(
            f"  {i}. {rec['ProductID']} | {rec['ProductName']:<35} | "
            f"{rec['SubCategory']:<18} | Rs.{rec['Price']:>8,.0f} | "
            f"Score: {rec['RuleScore']:.2f}"
        )
