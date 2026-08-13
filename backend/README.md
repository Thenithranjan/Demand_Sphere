# Retail AI — FastAPI Backend

Production-ready REST API for the **Retail Product Recommendation System**, built with FastAPI and connected to a MySQL database.

---

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── __init__.py          # App package
│   ├── main.py              # FastAPI app, CORS, router registration
│   ├── database.py          # SQLAlchemy engine & session config
│   ├── models.py            # ORM models (7 tables)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── crud.py              # CRUD operations for all tables
│   ├── auth.py              # Password hashing (bcrypt)
│   ├── recommendation.py    # Placeholder (ML — coming soon)
│   ├── forecast.py          # Placeholder (ML — coming soon)
│   ├── inventory.py         # Inventory alert helpers
│   └── routers/
│       ├── __init__.py
│       ├── products.py      # /api/v1/products
│       ├── customers.py     # /api/v1/customers
│       ├── sales.py         # /api/v1/sales
│       ├── inventory.py     # /api/v1/inventory
│       ├── suppliers.py     # /api/v1/suppliers
│       ├── forecast.py      # /api/v1/forecast
│       └── users.py         # /api/v1/users
├── .env                     # Environment variables (DB credentials)
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **MySQL Server** with `retail_ai` database created and populated
- **pip** (Python package manager)

### 1. Configure Environment

Edit the `.env` file with your MySQL credentials:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=retail_ai
SECRET_KEY=your-super-secret-key
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open API Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📡 API Endpoints

All endpoints are prefixed with `/api/v1`.

| Resource       | Endpoints                                         | Methods              |
|----------------|---------------------------------------------------|----------------------|
| **Products**   | `/api/v1/products`, `/api/v1/products/{id}`       | GET, POST, PUT, DELETE |
| **Customers**  | `/api/v1/customers`, `/api/v1/customers/{id}`     | GET, POST, PUT, DELETE |
| **Sales**      | `/api/v1/sales`, `/api/v1/sales/{id}`             | GET, POST, PUT, DELETE |
| **Inventory**  | `/api/v1/inventory`, `/api/v1/inventory/{id}`     | GET, POST, PUT, DELETE |
| **Suppliers**  | `/api/v1/suppliers`, `/api/v1/suppliers/{id}`     | GET, POST, PUT, DELETE |
| **Forecast**   | `/api/v1/forecast`, `/api/v1/forecast/{id}`       | GET, POST, PUT, DELETE |
| **Users**      | `/api/v1/users`, `/api/v1/users/{id}`             | GET, POST, PUT, DELETE |
| **Health**     | `/`, `/health`                                     | GET                  |

### Special Endpoints

| Endpoint                         | Description                              |
|----------------------------------|------------------------------------------|
| `GET /api/v1/inventory/summary`  | Inventory health summary                 |
| `GET /api/v1/inventory/low-stock`| Products below reorder point             |
| `GET /api/v1/inventory/overstock`| Products exceeding max stock             |
| `GET /api/v1/forecast/product/{id}` | All forecasts for a specific product  |

### Query Parameters

All list endpoints support pagination and filtering:

```
GET /api/v1/products?skip=0&limit=50&category=Men&brand=Ramraj Cotton
GET /api/v1/sales?customer_id=C00001&season=Summer
GET /api/v1/inventory?status=Reorder Required&warehouse=Chennai WH
```

---

## 🗄️ Database Tables

| Table             | Primary Key   | Relationships                                    |
|-------------------|---------------|--------------------------------------------------|
| **Products**      | ProductID     | → Suppliers, ← Inventory, ← Sales, ← Forecasts |
| **Customers**     | CustomerID    | ← Sales                                         |
| **Suppliers**     | SupplierID    | ← Products, ← Inventory                         |
| **Inventory**     | ProductID     | → Products, → Suppliers                         |
| **Sales**         | SaleID        | → Products, → Customers                         |
| **ForecastResults** | ForecastID  | → Products                                       |
| **Users**         | UserID        | Standalone                                       |

---

## 🔐 Security Notes

- Passwords are hashed using **bcrypt** before storage
- Password hashes are **never** exposed in API responses
- CORS is configured for specified origins only
- JWT authentication is planned for a future release

---

## 🛠️ Tech Stack

| Component      | Technology          |
|----------------|---------------------|
| Framework      | FastAPI 0.115       |
| ORM            | SQLAlchemy 2.0      |
| Database       | MySQL (pymysql)     |
| Validation     | Pydantic v2         |
| Authentication | passlib + bcrypt    |
| Server         | Uvicorn             |
