"""
Recommendations Router
======================
Exposes AI-powered product recommendation endpoints.
All recommendations are calculated dynamically in the Service Layer.
"""

import logging
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas
from app.services import recommendation_service

router = APIRouter(
    prefix="/recommendations",
    tags=["Personalized Recommendations"],
    responses={404: {"description": "Customer not found"}},
)

logger = logging.getLogger("recommendations_router")


@router.get(
    "/{customer_id}",
    response_model=schemas.RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Personalized Recommendations",
    description=(
        "Retrieves the Top 10 personalized product recommendations for a returning customer.\n\n"
        "**AI Pipeline Logic:**\n"
        "- Fetches customer purchase history dynamically from MySQL to filter out already bought items.\n"
        "- Combines Collaborative Filtering predictions (taste profile) and Content-Based profiling "
        "(attribute matching) with expert Retail Business Rules.\n"
        "- **Cold Start Fallback:** If the customer is new or has no purchase history, it falls back to the popular "
        "items in their preferred Category."
    ),
)
def get_recommendations_for_customer(
    customer_id: str,
    top_n: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    db: Session = Depends(get_db),
):
    """
    HTTP GET endpoint for retrieving personalized product recommendations.
    Defers business logic completely to the Service Layer.
    """
    return recommendation_service.get_personalized_recommendations(db, customer_id, top_n)
