"""
Retail AI — FastAPI Application Entry Point
=============================================
Configures the FastAPI application with:
- CORS middleware for React frontend integration
- All API routers with /api/v1 prefix
- Health check endpoint
- Automatic Swagger documentation at /docs
"""

import os
import sys
from pathlib import Path

# Ensure the project root and backend root are in the python path for importing subpackages
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import (
    products,
    customers,
    sales,
    inventory,
    suppliers,
    forecast,
    users,
    recommendations,
    analytics,
    model_management,
)
"""
@app.get("/test")
def test():
    print("TEST ENDPOINT CALLED")
    return {"message": "Server is working"}
"""
# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load machine learning models during application startup
    print("========== PRE-LOADING MACHINE LEARNING MODELS ==========", flush=True)
    try:
        from app.models_loader import load_recommendation_model
        load_recommendation_model()
        print("========== ML MODELS LOADED SUCCESSFULLY ==========", flush=True)
    except Exception as e:
        print(f"!!! ML MODEL STARTUP LOAD FAILURE: {e} !!!", flush=True)
        
    # Start the automatic model retraining scheduler
    try:
        from app.model_management.scheduler import start_scheduler
        await start_scheduler()
    except Exception as e:
        print(f"!!! SCHEDULER STARTUP FAILURE: {e} !!!", flush=True)
        
    yield
    
    # Stop the automatic model retraining scheduler
    try:
        from app.model_management.scheduler import stop_scheduler
        await stop_scheduler()
    except Exception as e:
        print(f"!!! SCHEDULER SHUTDOWN FAILURE: {e} !!!", flush=True)

# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Retail AI — Product Recommendation System API",
    description=(
        "Production-ready REST API for the Retail Product Recommendation System.\n\n"
        "**Features:**\n"
        "- Full CRUD operations for Products, Customers, Sales, Inventory, Suppliers, Forecasts, and Users\n"
        "- Pagination and filtering on all list endpoints\n"
        "- Inventory health monitoring with low-stock and overstock alerts\n"
        "- MySQL database integration via SQLAlchemy ORM\n"
        "- CORS enabled for React frontend\n\n"
        "**Coming Soon:**\n"
        "- ML-powered product recommendations\n"
        "- Demand forecasting engine\n"
        "- JWT authentication"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)
print("========== FASTAPI SERVER STARTED ==========")

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register Routers
# ---------------------------------------------------------------------------
API_PREFIX = "/api/v1"

app.include_router(products.router, prefix=API_PREFIX)
app.include_router(customers.router, prefix=API_PREFIX)
app.include_router(sales.router, prefix=API_PREFIX)
app.include_router(inventory.router, prefix=API_PREFIX)
app.include_router(suppliers.router, prefix=API_PREFIX)
app.include_router(forecast.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(recommendations.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(model_management.router, prefix=API_PREFIX)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
def root():
    """Root endpoint — API health check."""
    return {
        "status": "healthy",
        "service": "Retail AI API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "database": "MySQL (retail_ai)",
        "api_version": "v1",
        "endpoints": {
            "products": f"{API_PREFIX}/products",
            "customers": f"{API_PREFIX}/customers",
            "sales": f"{API_PREFIX}/sales",
            "inventory": f"{API_PREFIX}/inventory",
            "suppliers": f"{API_PREFIX}/suppliers",
            "forecast": f"{API_PREFIX}/forecast",
            "users": f"{API_PREFIX}/users",
        },
    }
