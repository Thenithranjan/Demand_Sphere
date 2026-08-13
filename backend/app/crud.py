"""
CRUD Operations Module
======================
Database Create, Read, Update, Delete functions for all tables.
Each function accepts a SQLAlchemy Session and returns ORM model instances.
Pagination is supported via skip/limit parameters.
"""

from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models, schemas
from .auth import get_password_hash


# ═══════════════════════════════════════════════════════════════════════════════
# Products CRUD
# ═══════════════════════════════════════════════════════════════════════════════
def get_product(db: Session, product_id: str):
    """Retrieve a single product by ProductID."""
    return db.query(models.Product).filter(
        models.Product.ProductID == product_id
    ).first()


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    status: Optional[str] = None,
):
    """Retrieve products with optional filtering and pagination."""
    query = db.query(models.Product)
    if category:
        query = query.filter(models.Product.Category == category)
    if brand:
        query = query.filter(models.Product.Brand == brand)
    if status:
        query = query.filter(models.Product.ProductStatus == status)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return total, items


def create_product(db: Session, product: schemas.ProductCreate):
    """Create a new product record and update database and CSV files."""
    # 1. Calculate ProfitMargin
    p_dict = product.model_dump()
    if p_dict.get("ProfitMargin") is None and p_dict.get("Price", 0) > 0:
        p_dict["ProfitMargin"] = round(((p_dict["Price"] - p_dict.get("CostPrice", 0)) / p_dict["Price"]) * 100, 2)
        p_dict["ProfitMargin"] = max(0.0, p_dict["ProfitMargin"])
    
    db_product = models.Product(**p_dict)
    db.add(db_product)
    
    # 2. Automatically create matching inventory record
    # Calculate stock utilisation
    current_stock = 100
    max_stock = 200
    stock_util = round(current_stock / max_stock, 4) if max_stock > 0 else 0.0
    
    from datetime import date
    inv_dict = {
        "ProductID": p_dict["ProductID"],
        "Warehouse": "Chennai WH",
        "CurrentStock": current_stock,
        "MinimumStock": 20,
        "MaximumStock": max_stock,
        "SafetyStock": 30,
        "ReorderPoint": 50,
        "LeadTimeDays": 7,
        "SupplierID": p_dict["SupplierID"],
        "LastRestocked": date.today().isoformat(),
        "InventoryStatus": "Healthy",
        "StockUtilisation": stock_util,
        "DaysSinceRestock": 0
    }
    db_inventory = models.Inventory(**inv_dict)
    db.add(db_inventory)
    
    db.commit()
    db.refresh(db_product)
    
    # 3. Update products_clean.csv
    import os
    import pandas as pd
    from pathlib import Path
    
    try:
        project_root = Path(__file__).resolve().parent.parent.parent
        prod_csv_path = project_root / "data" / "processed" / "products_clean.csv"
        if prod_csv_path.exists():
            df_prod = pd.read_csv(prod_csv_path)
            new_row_prod = pd.DataFrame([p_dict])
            new_row_prod = new_row_prod.reindex(columns=df_prod.columns)
            df_prod = pd.concat([df_prod, new_row_prod], ignore_index=True)
            df_prod.to_csv(prod_csv_path, index=False)
            print(f"[INFO] Successfully added product {product.ProductID} to CSV", flush=True)
    except Exception as e:
        print(f"[ERROR] Failed to update products CSV: {e}", flush=True)
        
    # 4. Update inventory_clean.csv
    try:
        project_root = Path(__file__).resolve().parent.parent.parent
        inv_csv_path = project_root / "data" / "processed" / "inventory_clean.csv"
        if inv_csv_path.exists():
            df_inv = pd.read_csv(inv_csv_path)
            new_row_inv = pd.DataFrame([inv_dict])
            new_row_inv = new_row_inv.reindex(columns=df_inv.columns)
            df_inv = pd.concat([df_inv, new_row_inv], ignore_index=True)
            df_inv.to_csv(inv_csv_path, index=False)
            print(f"[INFO] Successfully added inventory for product {product.ProductID} to CSV", flush=True)
    except Exception as e:
        print(f"[ERROR] Failed to update inventory CSV: {e}", flush=True)
        
    return db_product


def update_product(db: Session, product_id: str, product: schemas.ProductUpdate):
    """Update an existing product and synchronize changes to inventory and CSV files."""
    db_product = get_product(db, product_id)
    if not db_product:
        return None
        
    update_data = product.model_dump(exclude_unset=True)
    
    # Recalculate ProfitMargin if Price or CostPrice is updated
    if "Price" in update_data or "CostPrice" in update_data:
        price = update_data.get("Price", db_product.Price)
        cost_price = update_data.get("CostPrice", db_product.CostPrice)
        if price > 0:
            update_data["ProfitMargin"] = max(0.0, round(((price - cost_price) / price) * 100, 2))
            
    for key, value in update_data.items():
        setattr(db_product, key, value)
        
    # Also check if SupplierID is updated, sync to inventory!
    if "SupplierID" in update_data:
        db_inventory = db.query(models.Inventory).filter(models.Inventory.ProductID == product_id).first()
        if db_inventory:
            db_inventory.SupplierID = update_data["SupplierID"]
            
    db.commit()
    db.refresh(db_product)
    
    # Update products_clean.csv
    import pandas as pd
    from pathlib import Path
    try:
        project_root = Path(__file__).resolve().parent.parent.parent
        prod_csv_path = project_root / "data" / "processed" / "products_clean.csv"
        if prod_csv_path.exists():
            df_prod = pd.read_csv(prod_csv_path)
            # Find the row
            idx = df_prod[df_prod["ProductID"] == product_id].index
            if not idx.empty:
                for key, val in update_data.items():
                    if key in df_prod.columns:
                        df_prod.loc[idx, key] = val
                df_prod.to_csv(prod_csv_path, index=False)
                print(f"[INFO] Successfully updated product {product_id} in CSV", flush=True)
    except Exception as e:
        print(f"[ERROR] Failed to update products CSV: {e}", flush=True)
        
    # Update inventory_clean.csv (for SupplierID)
    if "SupplierID" in update_data:
        try:
            inv_csv_path = project_root / "data" / "processed" / "inventory_clean.csv"
            if inv_csv_path.exists():
                df_inv = pd.read_csv(inv_csv_path)
                idx = df_inv[df_inv["ProductID"] == product_id].index
                if not idx.empty:
                    df_inv.loc[idx, "SupplierID"] = update_data["SupplierID"]
                    df_inv.to_csv(inv_csv_path, index=False)
                    print(f"[INFO] Successfully synced SupplierID for product {product_id} in inventory CSV", flush=True)
        except Exception as e:
            print(f"[ERROR] Failed to sync SupplierID in inventory CSV: {e}", flush=True)
            
    return db_product


def delete_product(db: Session, product_id: str):
    """Delete a product by ProductID."""
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    db.delete(db_product)
    db.commit()
    return db_product


# ═══════════════════════════════════════════════════════════════════════════════
# Customers CRUD
# ═══════════════════════════════════════════════════════════════════════════════
def get_customer(db: Session, customer_id: str):
    """Retrieve a single customer by CustomerID."""
    return db.query(models.Customer).filter(
        models.Customer.CustomerID == customer_id
    ).first()


def get_customers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    membership: Optional[str] = None,
    city: Optional[str] = None,
):
    """Retrieve customers with optional filtering and pagination."""
    query = db.query(models.Customer)
    if membership:
        query = query.filter(models.Customer.Membership == membership)
    if city:
        query = query.filter(models.Customer.City == city)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return total, items


def create_customer(db: Session, customer: schemas.CustomerCreate):
    """Create a new customer record."""
    db_customer = models.Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


def update_customer(
    db: Session, customer_id: str, customer: schemas.CustomerUpdate
):
    """Update an existing customer. Only non-None fields are updated."""
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        return None
    update_data = customer.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_customer, key, value)
    db.commit()
    db.refresh(db_customer)
    return db_customer


def delete_customer(db: Session, customer_id: str):
    """Delete a customer by CustomerID."""
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        return None
    db.delete(db_customer)
    db.commit()
    return db_customer


# ═══════════════════════════════════════════════════════════════════════════════
# Suppliers CRUD
# ═══════════════════════════════════════════════════════════════════════════════
def get_supplier(db: Session, supplier_id: str):
    """Retrieve a single supplier by SupplierID."""
    return db.query(models.Supplier).filter(
        models.Supplier.SupplierID == supplier_id
    ).first()


def get_suppliers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
):
    """Retrieve suppliers with optional filtering and pagination."""
    query = db.query(models.Supplier)
    # Note: The 'status' parameter is kept for backward-compatibility but ignored 
    # because the 'Status' column does not exist in the suppliers database table.
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return total, items


def create_supplier(db: Session, supplier: schemas.SupplierCreate):
    """Create a new supplier record."""
    db_supplier = models.Supplier(**supplier.model_dump())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


def update_supplier(
    db: Session, supplier_id: str, supplier: schemas.SupplierUpdate
):
    """Update an existing supplier. Only non-None fields are updated."""
    db_supplier = get_supplier(db, supplier_id)
    if not db_supplier:
        return None
    update_data = supplier.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_supplier, key, value)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


def delete_supplier(db: Session, supplier_id: str):
    """Delete a supplier by SupplierID."""
    db_supplier = get_supplier(db, supplier_id)
    if not db_supplier:
        return None
    db.delete(db_supplier)
    db.commit()
    return db_supplier


# ═══════════════════════════════════════════════════════════════════════════════
# Inventory CRUD
# ═══════════════════════════════════════════════════════════════════════════════
def get_inventory(db: Session, product_id: str):
    """Retrieve inventory record for a specific product."""
    return db.query(models.Inventory).filter(
        models.Inventory.ProductID == product_id
    ).first()


def get_all_inventory(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    warehouse: Optional[str] = None,
):
    """Retrieve all inventory records with optional filtering."""
    query = db.query(models.Inventory)
    if status:
        query = query.filter(models.Inventory.InventoryStatus == status)
    if warehouse:
        query = query.filter(models.Inventory.Warehouse == warehouse)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return total, items


def create_inventory(db: Session, inventory: schemas.InventoryCreate):
    """Create a new inventory record."""
    db_inventory = models.Inventory(**inventory.model_dump())
    db.add(db_inventory)
    db.commit()
    db.refresh(db_inventory)
    return db_inventory


def update_inventory(
    db: Session, product_id: str, inventory: schemas.InventoryUpdate
):
    """Update inventory for a product. Only non-None fields are updated."""
    db_inventory = get_inventory(db, product_id)
    if not db_inventory:
        return None
    update_data = inventory.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_inventory, key, value)
    db.commit()
    db.refresh(db_inventory)
    return db_inventory


def delete_inventory(db: Session, product_id: str):
    """Delete inventory record for a product."""
    db_inventory = get_inventory(db, product_id)
    if not db_inventory:
        return None
    db.delete(db_inventory)
    db.commit()
    return db_inventory


# ═══════════════════════════════════════════════════════════════════════════════
# Sales CRUD
# ═══════════════════════════════════════════════════════════════════════════════
def get_sale(db: Session, sale_id: str):
    """Retrieve a single sale by SaleID."""
    return db.query(models.Sale).filter(
        models.Sale.SaleID == sale_id
    ).first()


def get_sales(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    customer_id: Optional[str] = None,
    product_id: Optional[str] = None,
    festival: Optional[str] = None,
    season: Optional[str] = None,
):
    """Retrieve sales with optional filtering and pagination."""
    query = db.query(models.Sale)
    if customer_id:
        query = query.filter(models.Sale.CustomerID == customer_id)
    if product_id:
        query = query.filter(models.Sale.ProductID == product_id)
    if festival:
        query = query.filter(models.Sale.Festival == festival)
    if season:
        query = query.filter(models.Sale.Season == season)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return total, items


def create_sale(db: Session, sale: schemas.SaleCreate):
    """Create a new sale record."""
    db_sale = models.Sale(**sale.model_dump())
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale


def update_sale(db: Session, sale_id: str, sale: schemas.SaleUpdate):
    """Update an existing sale. Only non-None fields are updated."""
    db_sale = get_sale(db, sale_id)
    if not db_sale:
        return None
    update_data = sale.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sale, key, value)
    db.commit()
    db.refresh(db_sale)
    return db_sale


def delete_sale(db: Session, sale_id: str):
    """Delete a sale by SaleID."""
    db_sale = get_sale(db, sale_id)
    if not db_sale:
        return None
    db.delete(db_sale)
    db.commit()
    return db_sale


# ═══════════════════════════════════════════════════════════════════════════════
# ForecastResults CRUD
# ═══════════════════════════════════════════════════════════════════════════════
def get_forecast_result(db: Session, product_id: str, year_month: str):
    """Retrieve a single forecast result by ProductID and YearMonth."""
    return db.query(models.ForecastResult).filter(
        models.ForecastResult.ProductID == product_id,
        models.ForecastResult.YearMonth == year_month
    ).first()


def get_forecast_by_product(db: Session, product_id: str):
    """Retrieve all forecast results for a specific product."""
    return db.query(models.ForecastResult).filter(
        models.ForecastResult.ProductID == product_id
    ).all()


def get_forecast_results(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    demand_level: Optional[str] = None,
):
    """Retrieve forecast results with optional filtering and pagination."""
    query = db.query(models.ForecastResult)
    # Note: The 'demand_level' parameter is kept for backward-compatibility but ignored 
    # because the 'DemandLevel' column does not exist in the forecastresults database table.
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return total, items


def create_forecast_result(db: Session, forecast: schemas.ForecastResultCreate):
    """Create a new forecast result record."""
    db_forecast = models.ForecastResult(**forecast.model_dump())
    db.add(db_forecast)
    db.commit()
    db.refresh(db_forecast)
    return db_forecast


def update_forecast_result(
    db: Session, product_id: str, year_month: str, forecast: schemas.ForecastResultUpdate
):
    """Update a forecast result. Only non-None fields are updated."""
    db_forecast = get_forecast_result(db, product_id, year_month)
    if not db_forecast:
        return None
    update_data = forecast.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_forecast, key, value)
    db.commit()
    db.refresh(db_forecast)
    return db_forecast


def delete_forecast_result(db: Session, product_id: str, year_month: str):
    """Delete a forecast result by ProductID and YearMonth."""
    db_forecast = get_forecast_result(db, product_id, year_month)
    if not db_forecast:
        return None
    db.delete(db_forecast)
    db.commit()
    return db_forecast


# ═══════════════════════════════════════════════════════════════════════════════
# Users CRUD
# ═══════════════════════════════════════════════════════════════════════════════
def get_user(db: Session, user_id: str):
    """Retrieve a single user by UserID."""
    return db.query(models.User).filter(
        models.User.UserID == user_id
    ).first()


def get_user_by_username(db: Session, username: str):
    """Retrieve a user by username (for login)."""
    return db.query(models.User).filter(
        models.User.Username == username
    ).first()


def get_user_by_email(db: Session, email: str):
    """Retrieve a user by email."""
    return db.query(models.User).filter(
        models.User.Email == email
    ).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Retrieve all users with pagination."""
    query = db.query(models.User)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return total, items


def create_user(db: Session, user: schemas.UserCreate):
    """Create a new user with plain-text password."""
    db_user = models.User(
        UserID=user.UserID,
        Username=user.Username,
        Email=user.Email,
        Password=user.Password,
        FullName=user.FullName,
        Role=user.Role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: str, user: schemas.UserUpdate):
    """Update an existing user. Saves password in plain-text."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    update_data = user.model_dump(exclude_unset=True)
    if "Password" in update_data and update_data["Password"]:
        db_user.Password = update_data.pop("Password")
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: str):
    """Delete a user by UserID."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    db.delete(db_user)
    db.commit()
    return db_user
