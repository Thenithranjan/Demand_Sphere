/**
 * TypeScript Interfaces — Demand Sphere Frontend
 * ============================================
 * Mirrors all Pydantic schemas from the FastAPI backend.
 * Every API response is strongly typed for compile-time safety.
 */

// ─── Pagination ──────────────────────────────────────────────────────────────
export interface PaginatedResponse<T> {
  total: number;
  page: number;
  per_page: number;
  items: T[];
}

// ─── Products ────────────────────────────────────────────────────────────────
export interface Product {
  ProductID: string;
  SKU: string;
  ProductName: string;
  Category: string;
  SubCategory: string;
  Brand: string;
  Color: string | null;
  Size: string | null;
  Fabric: string | null;
  SeasonalDemandTag: string | null;
  Gender: string | null;
  Price: number;
  CostPrice: number;
  SupplierID: string;
  ProductStatus: string | null;
  ImageURL: string | null;
  ProfitMargin: number | null;
}

export interface ProductCreate {
  ProductID: string;
  SKU: string;
  ProductName: string;
  Category: string;
  SubCategory: string;
  Brand: string;
  Color?: string;
  Size?: string;
  Fabric?: string;
  SeasonalDemandTag?: string;
  Gender?: string;
  Price: number;
  CostPrice: number;
  SupplierID: string;
  ProductStatus?: string;
  ImageURL?: string;
  ProfitMargin?: number;
}

export interface ProductUpdate {
  SKU?: string;
  ProductName?: string;
  Category?: string;
  SubCategory?: string;
  Brand?: string;
  Color?: string;
  Size?: string;
  Fabric?: string;
  SeasonalDemandTag?: string;
  Gender?: string;
  Price?: number;
  CostPrice?: number;
  SupplierID?: string;
  ProductStatus?: string;
  ImageURL?: string;
  ProfitMargin?: number;
}

// ─── Customers ───────────────────────────────────────────────────────────────
export interface Customer {
  CustomerID: string;
  FullName: string;
  Gender: string;
  Age: number;
  City: string | null;
  State: string | null;
  Membership: string | null;
  JoinDate: string | null;
  PreferredCategory: string | null;
  PreferredFabric: string | null;
  PreferredPriceRange: string | null;
  LoyaltyPoints: number | null;
  CustomerTenureDays: number | null;
}

export interface CustomerCreate {
  CustomerID: string;
  FullName: string;
  Gender: string;
  Age: number;
  City?: string;
  State?: string;
  Membership?: string;
  JoinDate?: string;
  PreferredCategory?: string;
  PreferredFabric?: string;
  PreferredPriceRange?: string;
  LoyaltyPoints?: number;
  CustomerTenureDays?: number;
}

export interface CustomerUpdate {
  FullName?: string;
  Gender?: string;
  Age?: number;
  City?: string;
  State?: string;
  Membership?: string;
  JoinDate?: string;
  PreferredCategory?: string;
  PreferredFabric?: string;
  PreferredPriceRange?: string;
  LoyaltyPoints?: number;
  CustomerTenureDays?: number;
}

// ─── Inventory ───────────────────────────────────────────────────────────────
export interface Inventory {
  ProductID: string;
  Warehouse: string | null;
  CurrentStock: number | null;
  MinimumStock: number | null;
  MaximumStock: number | null;
  SafetyStock: number | null;
  ReorderPoint: number | null;
  LeadTimeDays: number | null;
  SupplierID: string | null;
  LastRestocked: string | null;
  InventoryStatus: string | null;
  StockUtilisation: number | null;
  DaysSinceRestock: number | null;
}

export interface InventoryCreate {
  ProductID: string;
  Warehouse?: string;
  CurrentStock?: number;
  MinimumStock?: number;
  MaximumStock?: number;
  SafetyStock?: number;
  ReorderPoint?: number;
  LeadTimeDays?: number;
  SupplierID?: string;
  LastRestocked?: string;
  InventoryStatus?: string;
  StockUtilisation?: number;
  DaysSinceRestock?: number;
}

export interface InventoryUpdate {
  Warehouse?: string;
  CurrentStock?: number;
  MinimumStock?: number;
  MaximumStock?: number;
  SafetyStock?: number;
  ReorderPoint?: number;
  LeadTimeDays?: number;
  SupplierID?: string;
  LastRestocked?: string;
  InventoryStatus?: string;
  StockUtilisation?: number;
  DaysSinceRestock?: number;
}

// ─── Sales ───────────────────────────────────────────────────────────────────
export interface Sale {
  SaleID: string;
  InvoiceID: string | null;
  CustomerID: string;
  ProductID: string;
  SubCategory: string | null;
  SaleDate: string;
  Quantity: number;
  MRP: number | null;
  DiscountPercent: number | null;
  FinalPrice: number;
  Festival: string | null;
  Season: string | null;
  DayOfWeek: string | null;
  SaleMonth: number | null;
  SaleYear: number | null;
}

export interface SaleCreate {
  SaleID: string;
  InvoiceID?: string;
  CustomerID: string;
  ProductID: string;
  SubCategory?: string;
  SaleDate: string;
  Quantity: number;
  MRP?: number;
  DiscountPercent?: number;
  FinalPrice: number;
  Festival?: string;
  Season?: string;
  DayOfWeek?: string;
  SaleMonth?: number;
  SaleYear?: number;
}

// ─── Suppliers ───────────────────────────────────────────────────────────────
export interface Supplier {
  SupplierID: string;
  SupplierName: string;
  ContactPerson: string | null;
  Phone: string | null;
  Email: string | null;
  City: string | null;
  State: string | null;
}

export interface SupplierCreate {
  SupplierID: string;
  SupplierName: string;
  ContactPerson?: string;
  Phone?: string;
  Email?: string;
  City?: string;
  State?: string;
}

export interface SupplierUpdate {
  SupplierName?: string;
  ContactPerson?: string;
  Phone?: string;
  Email?: string;
  City?: string;
  State?: string;
}

// ─── Forecast Results ────────────────────────────────────────────────────────
export interface ForecastResult {
  ProductID: string;
  YearMonth: string;
  Quantity: number | null;
  Revenue: number | null;
  Category: string | null;
  SubCategory: string | null;
  Brand: string | null;
  Price: number | null;
  Year: number | null;
  Month: number | null;
  Quarter: number | null;
  Week: number | null;
  Day: number | null;
  AveragePrice: number | null;
  Season: string | null;
  Festival: string | null;
  TargetQuantity: number | null;
  TargetRevenue: number | null;
}

// ─── Users ───────────────────────────────────────────────────────────────────
export interface User {
  UserID: string;
  Username: string | null;
  Email: string | null;
  FullName: string | null;
  Role: string | null;
  CreatedAt: string | null;
  Password?: string | null;
}

export interface UserCreate {
  UserID: string;
  Username: string;
  Email: string;
  FullName: string;
  Role: string;
  Password: string;
}

export interface UserUpdate {
  Username?: string;
  Email?: string;
  FullName?: string;
  Role?: string;
  Password?: string;
}

// ─── AI & Analytics Response Types ───────────────────────────────────────────
export interface RecommendedProduct {
  ProductID: string;
  ProductName: string;
  Score: number;
}

export interface RecommendationResponse {
  customer_id: string;
  recommended_products: RecommendedProduct[];
}

export interface ForecastPrediction {
  product_id: string;
  next_month_quantity: number;
  next_month_revenue: number;
  next_quarter_quantity: number;
  next_quarter_revenue: number;
  confidence: number;
}

export interface InventoryAlert {
  ProductID: string;
  ProductName: string;
  Warehouse: string;
  CurrentStock: number;
  SafetyStock: number;
  ReorderPoint: number;
  ForecastDemand: number;
  Recommendation: string;
}

// ─── Analytics Dashboard Types ───────────────────────────────────────────────
export interface DashboardSummary {
  total_revenue: number;
  total_quantity_sold: number;
  average_order_value: number;
  average_profit_margin: number;
  average_stock_utilisation: number;
  inventory_turnover_ratio: number;
  top_products?: Array<{ ProductName: string; revenue: number }>;
  top_categories?: Array<{ Category: string; revenue: number }>;
}

export interface SalesAnalytics {
  monthly_sales_trend: Array<{
    month: string;
    total_quantity: number;
    total_revenue: number;
  }>;
  subcategory_sales: Array<{
    SubCategory: string;
    total_revenue: number;
    total_quantity: number;
  }>;
}

export interface CustomerAnalytics {
  best_customers: Array<{
    CustomerID: string;
    FullName: string;
    total_spent: number;
    total_orders: number;
  }>;
  membership_segments: Array<{
    Membership: string;
    count: number;
  }>;
}

export interface InventoryAnalytics {
  warehouse_metrics: Array<{
    Warehouse: string;
    total_stock: number;
    avg_utilisation: number;
    product_count: number;
  }>;
  stock_health_distribution: Array<{
    InventoryStatus: string;
    count: number;
  }>;
}

// ─── Auth Types ──────────────────────────────────────────────────────────────
export interface AuthUser {
  UserID: string;
  Username: string;
  FullName: string;
  Email: string;
  Role: string;
}

export type UserRole = 'Admin' | 'Manager' | 'Employee';

export interface UserLogin {
  Username: string;
  Password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}
