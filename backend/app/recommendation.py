"""
Recommendation Module (Placeholder)
====================================
This module will house the product recommendation engine.
Machine learning code will be added in a future phase.

Placeholder functions are provided so the import structure is ready.
"""


def get_recommendations(product_id: str, top_n: int = 5):
    """
    Placeholder: Returns recommended products for a given product.
    Will be implemented with collaborative filtering / content-based ML model.
    """
    return {
        "product_id": product_id,
        "recommendations": [],
        "message": "Recommendation engine not yet implemented.",
    }


def get_customer_recommendations(customer_id: str, top_n: int = 5):
    """
    Placeholder: Returns personalised recommendations for a customer.
    Will be implemented with customer purchase history analysis.
    """
    return {
        "customer_id": customer_id,
        "recommendations": [],
        "message": "Customer recommendation engine not yet implemented.",
    }
