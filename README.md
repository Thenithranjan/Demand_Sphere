# Demand Sphere — Retail AI Product Recommendation System

A full-stack, production-ready Retail AI platform for product recommendations, demand forecasting, inventory management, customer analytics, and MLOps model lifecycle management.

---

## Overview

**Demand Sphere** is an intelligent retail operations platform that combines machine learning with a modern web interface to help retail businesses make data-driven decisions. It provides AI-powered product recommendations, demand forecasting, inventory health monitoring, customer segmentation, and an automated ML model management system with versioning, retraining, and audit trails.

---

## Features

### AI Recommendation System
- Hybrid collaborative + content-based filtering
- Customer-specific product recommendations
- Similarity matrix built from sales transaction history
- TF-IDF product content embeddings

### Demand Forecasting
- XGBoost-based quantity and revenue forecasting
- Time-series feature engineering
- Product-level and category-level forecast views
- Forecast result export

### Inventory Management
- Real-time stock level tracking
- Low-stock and overstock alert generation
- Inventory decision support (reorder recommendations)
- Supplier management integration

### Customer Management
- Customer profile management
- Purchase history tracking
- Customer segmentation support

### Sales Analytics
- Sales transaction tracking
- Revenue, quantity, and category breakdowns
- Product performance analysis
- Recharts-powered interactive dashboards

### AI Model Management (MLOps)
- Model registry with version tracking (v1.x naming)
- Automatic scheduled model retraining
- Training history and audit trail logs
- Model metadata and dataset registry
- Training settings configuration
- Model versioning for both recommendation and forecast models

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend Framework** | React 19 + TypeScript |
| **Frontend Build Tool** | Vite 8 |
| **Frontend Styling** | Tailwind CSS v4 |
| **Frontend State** | TanStack React Query |
| **Frontend Routing** | React Router v7 |
| **Frontend Charts** | Recharts |
| **Frontend Animation** | Framer Motion |
| **Backend Framework** | FastAPI 0.115 |
| **Backend Server** | Uvicorn |
| **Database ORM** | SQLAlchemy 2.0 |
| **Database** | MySQL |
| **ML — Recommendation** | scikit-learn (collaborative filtering, TF-IDF) |
| **ML — Forecasting** | XGBoost |
| **Authentication** | JWT (python-jose + passlib/bcrypt) |
| **API Docs** | Swagger UI (/docs) + ReDoc (/redoc) |
| **Environment** | python-dotenv |

---

## Project Structure

```
Demand_Sphere/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point, CORS, routers
│   │   ├── models.py                # SQLAlchemy ORM models
│   │   ├── schemas.py               # Pydantic request/response schemas
│   │   ├── crud.py                  # Database CRUD operations
│   │   ├── database.py              # DB engine and session factory
│   │   ├── auth.py                  # JWT authentication
│   │   ├── models_loader.py         # ML model loader (at startup)
│   │   ├── model_management/        # MLOps — scheduler, retraining, versioning
│   │   ├── routers/                 # API route handlers
│   │   │   ├── products.py
│   │   │   ├── customers.py
│   │   │   ├── sales.py
│   │   │   ├── inventory.py
│   │   │   ├── suppliers.py
│   │   │   ├── forecast.py
│   │   │   ├── users.py
│   │   │   ├── recommendations.py
│   │   │   ├── analytics.py
│   │   │   └── model_management.py
│   │   └── services/                # Business logic services
│   ├── analytics/                   # Product & sales analysis scripts
│   ├── data_pipeline/               # Data cleaning and ETL scripts
│   ├── forecasting/                 # Forecasting training and evaluation
│   ├── inventory/                   # Inventory alert generation
│   ├── models/                      # ML model artifacts (git-ignored, see note)
│   │   ├── model_registry.json      # Model version registry
│   │   ├── model_metadata.json      # Active model metadata
│   │   ├── training_settings.json   # Retraining config
│   │   ├── training_logs.json       # Training run history
│   │   ├── audit_trail.json         # MLOps audit trail
│   │   └── dataset_registry.json    # Dataset version tracking
│   ├── recommendation/              # Recommendation engine training & eval
│   ├── utils/                       # Shared utilities
│   ├── requirements.txt
│   ├── .env.example                 # Environment variable template
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/              # Reusable UI components
│   │   ├── pages/                   # Dashboard, Products, Customers,
│   │   │                            #   Inventory, Forecast, Recommendations,
│   │   │                            #   Analytics, Model Management
│   │   ├── services/                # API service layer (axios)
│   │   └── ...
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── data/
│   ├── raw/                         # Source datasets (XLSX)
│   ├── processed/                   # Cleaned datasets (CSV)
│   └── backups/                     # Timestamped backup CSVs (git-ignored)
│
├── notebooks/                       # Jupyter notebooks for EDA
├── reports/                         # Validation and EDA reports
├── requirements.txt                 # Root-level Python dependencies
├── verify_mlops_lifecycle.py        # MLOps lifecycle verification script
├── .gitignore
└── README.md
```

> **Note on ML models:** Trained `.pkl` and `.joblib` model files are excluded from Git (total ~84 MB) to keep the repository lightweight. The model registry, metadata, and training configuration JSON files are tracked. Retrain models locally using the training scripts in `backend/forecasting/` and `backend/recommendation/`.

---

## Prerequisites

- **Python** 3.10+
- **Node.js** 18+ and **npm**
- **MySQL** 8.0+
- **Git**

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Thenithranjan/Demand_Sphere.git
cd Demand_Sphere
```

### 2. MySQL Database Setup

Create the database:

```sql
CREATE DATABASE retail_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Backend Setup

**Create and activate a virtual environment:**

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**Install dependencies:**

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Configure environment variables:**

```bash
cp .env.example .env
```

Edit `backend/.env` with your actual values:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_database_password
DB_NAME=retail_ai

SECRET_KEY=your_super_secret_key_here_change_this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

---

## Running the Application

### Start the Backend

From the `backend/` directory (with virtual environment activated):

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Base:** `http://localhost:8000`
- **Swagger Docs:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/health`

### Start the Frontend

From the `frontend/` directory:

```bash
npm run dev
```

The frontend will be available at: `http://localhost:5173`

---

## API Documentation

The FastAPI backend provides automatic interactive API documentation.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Detailed health status |
| `/api/v1/products` | GET/POST | Product management |
| `/api/v1/customers` | GET/POST | Customer management |
| `/api/v1/sales` | GET/POST | Sales transactions |
| `/api/v1/inventory` | GET/POST | Inventory management |
| `/api/v1/suppliers` | GET/POST | Supplier management |
| `/api/v1/forecast` | GET | Demand forecasts |
| `/api/v1/recommendations` | GET | Product recommendations |
| `/api/v1/analytics` | GET | Sales analytics |
| `/api/v1/model-management` | GET/POST | MLOps model management |

Full interactive documentation: **`http://localhost:8000/docs`**

---

## ML Model Training Workflow

### Train the Recommendation Model

```bash
cd backend
python -m recommendation.train
```

### Train the Forecast Model

```bash
cd backend
python -m forecasting.train
```

### Automatic Retraining

The backend scheduler (`app/model_management/scheduler.py`) automatically triggers model retraining on a configured schedule. Training history is logged in:

- `backend/models/training_logs.json`
- `backend/models/audit_trail.json`
- `backend/models/model_registry.json`

### Verify MLOps Lifecycle

```bash
python verify_mlops_lifecycle.py
```

---

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Overview KPIs and charts |
| Products | `/products` | Product catalog management |
| Customers | `/customers` | Customer management |
| Inventory | `/inventory` | Stock levels and alerts |
| Forecast | `/forecast` | Demand forecasting |
| Recommendations | `/recommendations` | AI product recommendations |
| Analytics | `/analytics` | Sales analytics dashboards |
| Model Management | `/model-management` | MLOps — model versions, retraining, logs |

---

## Data

Source datasets are located in `data/raw/` (textile retail domain):

| File | Description |
|------|-------------|
| `sales_transactions_50000_textile_dataset.xlsx` | 50,000 sales transactions |
| `customers_2000_textile_dataset.xlsx` | 2,000 customer records |
| `products_500_textile_dataset.xlsx` | 500 product catalog entries |
| `inventory_500_textile_dataset.xlsx` | Inventory levels |

Processed datasets and backup CSVs are generated by the data pipeline (`backend/data_pipeline/`) and are excluded from Git.

---

## Security Notes

- **Never** commit `.env` files or any file containing real credentials.
- Use `backend/.env.example` as a template — it contains only placeholders.
- JWT secrets should be strong random strings (min 32 characters).
- Database passwords should follow your organization's security policy.
- In production, restrict `CORS_ORIGINS` to your actual frontend domain.

---

## License

This project is for research and educational purposes.

---

*Demand Sphere — Powered by FastAPI, React, and XGBoost*
