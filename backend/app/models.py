"""
SQLAlchemy ORM Models
=====================
Defines ORM models for all 7 tables in the demand_sphere database.
Models map directly to existing database tables — no migrations needed.

Tables:
    - suppliers
    - products
    - customers
    - inventory
    - sales
    - forecastresults
    - users
"""

from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base


# ═══════════════════════════════════════════════════════════════════════════════
# Suppliers
# ═══════════════════════════════════════════════════════════════════════════════
class Supplier(Base):
    """Supplier information and contact details."""

    __tablename__ = "suppliers"

    SupplierID = Column(String(10), primary_key=True, index=True)
    SupplierName = Column(String(100), nullable=False)
    ContactPerson = Column(String(100), nullable=True)
    Phone = Column(String(20), nullable=True)
    Email = Column(String(100), nullable=True)
    City = Column(String(50), nullable=True)
    State = Column(String(50), nullable=True)

    # Relationships
    products = relationship("Product", back_populates="supplier")
    inventory_items = relationship("Inventory", back_populates="supplier")


# ═══════════════════════════════════════════════════════════════════════════════
# Products
# ═══════════════════════════════════════════════════════════════════════════════
class Product(Base):
    """Product catalog with pricing, categorization, and supplier linkage."""

    __tablename__ = "products"

    ProductID = Column(String(10), primary_key=True, index=True)
    SKU = Column(String(30), nullable=True)
    ProductName = Column(String(150), nullable=False)
    Category = Column(String(50), nullable=True)
    SubCategory = Column(String(50), nullable=True)
    Brand = Column(String(50), nullable=True)
    Color = Column(String(30), nullable=True)
    Size = Column(String(20), nullable=True)
    Fabric = Column(String(50), nullable=True)
    SeasonalDemandTag = Column(String(50), nullable=True)
    Gender = Column(String(20), nullable=True)
    Price = Column(Float, nullable=True)
    CostPrice = Column(Float, nullable=True)
    SupplierID = Column(
        String(10), ForeignKey("suppliers.SupplierID"), nullable=True
    )
    ProductStatus = Column(String(30), nullable=True)
    ImageURL = Column(String(255), nullable=True)
    ProfitMargin = Column(Float, nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="products")
    inventory = relationship("Inventory", back_populates="product", uselist=False)
    sales = relationship("Sale", back_populates="product")
    forecast_results = relationship("ForecastResult", back_populates="product")


# ═══════════════════════════════════════════════════════════════════════════════
# Customers
# ═══════════════════════════════════════════════════════════════════════════════
class Customer(Base):
    """Customer profiles with demographics and preferences."""

    __tablename__ = "customers"

    CustomerID = Column(String(10), primary_key=True, index=True)
    FullName = Column(String(100), nullable=False)
    Gender = Column(String(20), nullable=True)
    Age = Column(Integer, nullable=True)
    City = Column(String(100), nullable=True)
    State = Column(String(100), nullable=True)
    Membership = Column(String(30), nullable=True)
    JoinDate = Column(Date, nullable=True)
    PreferredCategory = Column(String(50), nullable=True)
    PreferredFabric = Column(String(50), nullable=True)
    PreferredPriceRange = Column(String(30), nullable=True)
    LoyaltyPoints = Column(Integer, default=0, nullable=True)
    CustomerTenureDays = Column(Integer, default=0, nullable=True)

    # Relationships
    sales = relationship("Sale", back_populates="customer")


# ═══════════════════════════════════════════════════════════════════════════════
# Inventory
# ═══════════════════════════════════════════════════════════════════════════════
class Inventory(Base):
    """Real-time inventory tracking per product with reorder management."""

    __tablename__ = "inventory"

    ProductID = Column(
        String(10),
        ForeignKey("products.ProductID"),
        primary_key=True,
        index=True,
    )
    Warehouse = Column(String(100), nullable=False)
    CurrentStock = Column(Integer, default=0, nullable=True)
    MinimumStock = Column(Integer, default=0, nullable=True)
    MaximumStock = Column(Integer, default=0, nullable=True)
    SafetyStock = Column(Integer, default=0, nullable=True)
    ReorderPoint = Column(Integer, default=0, nullable=True)
    LeadTimeDays = Column(Integer, default=0, nullable=True)
    SupplierID = Column(
        String(10), ForeignKey("suppliers.SupplierID"), nullable=True
    )
    LastRestocked = Column(Date, nullable=True)
    InventoryStatus = Column(String(30), nullable=True)
    StockUtilisation = Column(Float, nullable=True)
    DaysSinceRestock = Column(Integer, default=0, nullable=True)

    # Relationships
    product = relationship("Product", back_populates="inventory")
    supplier = relationship("Supplier", back_populates="inventory_items")


# ═══════════════════════════════════════════════════════════════════════════════
# Sales
# ═══════════════════════════════════════════════════════════════════════════════
class Sale(Base):
    """Individual sales transaction records."""

    __tablename__ = "sales"

    SaleID = Column(String(15), primary_key=True, index=True)
    InvoiceID = Column(String(20), nullable=True)
    CustomerID = Column(
        String(10), ForeignKey("customers.CustomerID"), nullable=False
    )
    ProductID = Column(
        String(10), ForeignKey("products.ProductID"), nullable=False
    )
    SubCategory = Column(String(50), nullable=True)
    SaleDate = Column(Date, nullable=True)
    Quantity = Column(Integer, nullable=True)
    MRP = Column(Float, nullable=True)
    DiscountPercent = Column(Float, default=0.0, nullable=True)
    FinalPrice = Column(Float, nullable=True)
    Festival = Column(String(50), nullable=True)
    Season = Column(String(30), nullable=True)
    DayOfWeek = Column(String(15), nullable=True)
    SaleMonth = Column(Integer, nullable=True)
    SaleYear = Column(Integer, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="sales")
    product = relationship("Product", back_populates="sales")


# ═══════════════════════════════════════════════════════════════════════════════
# ForecastResults
# ═══════════════════════════════════════════════════════════════════════════════
class ForecastResult(Base):
    """Demand forecast predictions per product."""

    __tablename__ = "forecastresults"

    ProductID = Column(
        String(10), ForeignKey("products.ProductID"), primary_key=True, nullable=False, index=True
    )
    YearMonth = Column(String(7), primary_key=True, nullable=False)
    Quantity = Column(Integer, nullable=True)
    Revenue = Column(Float, nullable=True)
    Category = Column(String(50), nullable=True)
    SubCategory = Column(String(50), nullable=True)
    Brand = Column(String(50), nullable=True)
    Price = Column(Float, nullable=True)
    Year = Column(Integer, nullable=True)
    Month = Column(Integer, nullable=True)
    Quarter = Column(Integer, nullable=True)
    Week = Column(Integer, nullable=True)
    Day = Column(Integer, nullable=True)
    AveragePrice = Column(Float, nullable=True)
    Season = Column(String(30), nullable=True)
    Festival = Column(String(50), nullable=True)
    TargetQuantity = Column(Integer, nullable=True)
    TargetRevenue = Column(Float, nullable=True)

    # Relationships
    product = relationship("Product", back_populates="forecast_results")


# ═══════════════════════════════════════════════════════════════════════════════
# Users
# ═══════════════════════════════════════════════════════════════════════════════
class User(Base):
    """Application users for dashboard access and authentication."""

    __tablename__ = "users"

    UserID = Column(String(10), primary_key=True, index=True)
    Username = Column(String(50), unique=True, nullable=True)
    Password = Column(String(255), nullable=True)
    FullName = Column(String(100), nullable=True)
    Role = Column(String(20), default="viewer", nullable=True)
    Email = Column(String(100), unique=True, nullable=True)
    CreatedAt = Column(DateTime, server_default=func.now(), nullable=True)

