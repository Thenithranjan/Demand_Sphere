"""
Pydantic Schemas
================
Request and response schemas for all API endpoints.
Uses Pydantic v2 with `model_config = ConfigDict(from_attributes=True)`
for seamless ORM ↔ JSON serialisation.

Naming Convention:
    - *Base    → shared fields
    - *Create  → fields required for POST
    - *Update  → fields for PUT (all optional)
    - *Response→ fields returned in API responses
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ═══════════════════════════════════════════════════════════════════════════════
# Supplier Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class SupplierBase(BaseModel):
    SupplierName: str
    ContactPerson: Optional[str] = None
    Phone: Optional[str] = None
    Email: Optional[str] = None
    City: Optional[str] = None
    State: Optional[str] = None


class SupplierCreate(SupplierBase):
    SupplierID: str


class SupplierUpdate(BaseModel):
    SupplierName: Optional[str] = None
    ContactPerson: Optional[str] = None
    Phone: Optional[str] = None
    Email: Optional[str] = None
    City: Optional[str] = None
    State: Optional[str] = None


class SupplierResponse(SupplierBase):
    SupplierID: str

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Product Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class ProductBase(BaseModel):
    SKU: str
    ProductName: str
    Category: str
    SubCategory: str
    Brand: str
    Color: Optional[str] = None
    Size: Optional[str] = None
    Fabric: Optional[str] = None
    SeasonalDemandTag: Optional[str] = None
    Gender: Optional[str] = None
    Price: float
    CostPrice: float
    SupplierID: str
    ProductStatus: Optional[str] = "Active"
    ImageURL: Optional[str] = None
    ProfitMargin: Optional[float] = None


class ProductCreate(ProductBase):
    ProductID: str


class ProductUpdate(BaseModel):
    SKU: Optional[str] = None
    ProductName: Optional[str] = None
    Category: Optional[str] = None
    SubCategory: Optional[str] = None
    Brand: Optional[str] = None
    Color: Optional[str] = None
    Size: Optional[str] = None
    Fabric: Optional[str] = None
    SeasonalDemandTag: Optional[str] = None
    Gender: Optional[str] = None
    Price: Optional[float] = None
    CostPrice: Optional[float] = None
    SupplierID: Optional[str] = None
    ProductStatus: Optional[str] = None
    ImageURL: Optional[str] = None
    ProfitMargin: Optional[float] = None


class ProductResponse(ProductBase):
    ProductID: str

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Customer Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class CustomerBase(BaseModel):
    FullName: str
    Gender: str
    Age: int
    City: Optional[str] = None
    State: Optional[str] = None
    Membership: Optional[str] = None
    JoinDate: Optional[date] = None
    PreferredCategory: Optional[str] = None
    PreferredFabric: Optional[str] = None
    PreferredPriceRange: Optional[str] = None
    LoyaltyPoints: Optional[int] = 0
    CustomerTenureDays: Optional[int] = 0


class CustomerCreate(CustomerBase):
    CustomerID: str


class CustomerUpdate(BaseModel):
    FullName: Optional[str] = None
    Gender: Optional[str] = None
    Age: Optional[int] = None
    City: Optional[str] = None
    State: Optional[str] = None
    Membership: Optional[str] = None
    JoinDate: Optional[date] = None
    PreferredCategory: Optional[str] = None
    PreferredFabric: Optional[str] = None
    PreferredPriceRange: Optional[str] = None
    LoyaltyPoints: Optional[int] = None
    CustomerTenureDays: Optional[int] = None


class CustomerResponse(CustomerBase):
    CustomerID: str

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Inventory Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class InventoryBase(BaseModel):
    Warehouse: Optional[str] = None
    CurrentStock: Optional[int] = 0
    MinimumStock: Optional[int] = 0
    MaximumStock: Optional[int] = 0
    SafetyStock: Optional[int] = 0
    ReorderPoint: Optional[int] = 0
    LeadTimeDays: Optional[int] = 0
    SupplierID: Optional[str] = None
    LastRestocked: Optional[date] = None
    InventoryStatus: Optional[str] = None
    StockUtilisation: Optional[float] = None
    DaysSinceRestock: Optional[int] = 0


class InventoryCreate(InventoryBase):
    ProductID: str


class InventoryUpdate(BaseModel):
    Warehouse: Optional[str] = None
    CurrentStock: Optional[int] = None
    MinimumStock: Optional[int] = None
    MaximumStock: Optional[int] = None
    SafetyStock: Optional[int] = None
    ReorderPoint: Optional[int] = None
    LeadTimeDays: Optional[int] = None
    SupplierID: Optional[str] = None
    LastRestocked: Optional[date] = None
    InventoryStatus: Optional[str] = None
    StockUtilisation: Optional[float] = None
    DaysSinceRestock: Optional[int] = None


class InventoryResponse(InventoryBase):
    ProductID: str

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Sales Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class SaleBase(BaseModel):
    InvoiceID: Optional[str] = None
    CustomerID: str
    ProductID: str
    SubCategory: Optional[str] = None
    SaleDate: date
    Quantity: int
    MRP: Optional[float] = None
    DiscountPercent: Optional[float] = 0.0
    FinalPrice: float
    Festival: Optional[str] = None
    Season: Optional[str] = None
    DayOfWeek: Optional[str] = None
    SaleMonth: Optional[int] = None
    SaleYear: Optional[int] = None


class SaleCreate(SaleBase):
    SaleID: str


class SaleUpdate(BaseModel):
    InvoiceID: Optional[str] = None
    CustomerID: Optional[str] = None
    ProductID: Optional[str] = None
    SubCategory: Optional[str] = None
    SaleDate: Optional[date] = None
    Quantity: Optional[int] = None
    MRP: Optional[float] = None
    DiscountPercent: Optional[float] = None
    FinalPrice: Optional[float] = None
    Festival: Optional[str] = None
    Season: Optional[str] = None
    DayOfWeek: Optional[str] = None
    SaleMonth: Optional[int] = None
    SaleYear: Optional[int] = None


class SaleResponse(SaleBase):
    SaleID: str

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ForecastResult Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class ForecastResultBase(BaseModel):
    ProductID: str
    YearMonth: str
    Quantity: Optional[int] = None
    Revenue: Optional[float] = None
    Category: Optional[str] = None
    SubCategory: Optional[str] = None
    Brand: Optional[str] = None
    Price: Optional[float] = None
    Year: Optional[int] = None
    Month: Optional[int] = None
    Quarter: Optional[int] = None
    Week: Optional[int] = None
    Day: Optional[int] = None
    AveragePrice: Optional[float] = None
    Season: Optional[str] = None
    Festival: Optional[str] = None
    TargetQuantity: Optional[int] = None
    TargetRevenue: Optional[float] = None


class ForecastResultCreate(ForecastResultBase):
    pass


class ForecastResultUpdate(BaseModel):
    ProductID: Optional[str] = None
    YearMonth: Optional[str] = None
    Quantity: Optional[int] = None
    Revenue: Optional[float] = None
    Category: Optional[str] = None
    SubCategory: Optional[str] = None
    Brand: Optional[str] = None
    Price: Optional[float] = None
    Year: Optional[int] = None
    Month: Optional[int] = None
    Quarter: Optional[int] = None
    Week: Optional[int] = None
    Day: Optional[int] = None
    AveragePrice: Optional[float] = None
    Season: Optional[str] = None
    Festival: Optional[str] = None
    TargetQuantity: Optional[int] = None
    TargetRevenue: Optional[float] = None


class ForecastResultResponse(ForecastResultBase):
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# User Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class UserBase(BaseModel):
    Username: Optional[str] = None
    Email: Optional[str] = None
    FullName: Optional[str] = None
    Role: Optional[str] = "viewer"


class UserCreate(UserBase):
    UserID: str
    Password: str  # Plain-text password; hashed before storage


class UserUpdate(BaseModel):
    Username: Optional[str] = None
    Email: Optional[str] = None
    FullName: Optional[str] = None
    Role: Optional[str] = None
    Password: Optional[str] = None  # If provided, re-hash before storage


class UserResponse(UserBase):
    UserID: str
    CreatedAt: Optional[datetime] = None
    Password: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    Username: str
    Password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ═══════════════════════════════════════════════════════════════════════════════
# Pagination Wrapper
# ═══════════════════════════════════════════════════════════════════════════════
class PaginatedResponse(BaseModel):
    """Generic wrapper for paginated list responses."""

    total: int
    page: int
    per_page: int
    items: list

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════════
# AI & Analytics Schemas
# ═══════════════════════════════════════════════════════════════════════════════
class RecommendedProduct(BaseModel):
    ProductID: str
    ProductName: str
    Score: float

class RecommendationResponse(BaseModel):
    customer_id: str
    recommended_products: list[RecommendedProduct]

class ForecastResponse(BaseModel):
    product_id: str
    next_month_quantity: int
    next_month_revenue: float
    next_quarter_quantity: int
    next_quarter_revenue: float
    confidence: float

class InventoryAlertResponse(BaseModel):
    ProductID: str
    ProductName: str
    Warehouse: str
    CurrentStock: int
    SafetyStock: int
    ReorderPoint: int
    ForecastDemand: int
    Recommendation: str

