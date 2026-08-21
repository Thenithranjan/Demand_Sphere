"""
Database Seeding Script
========================
Populates Supabase PostgreSQL database tables from processed CSV datasets
and inserts predefined brand suppliers, 10 staff users, and SQL views.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pandas as pd
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app import models

PROJECT_ROOT = backend_dir.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"

RAW_SUPPLIERS = [
    {"SupplierID": "SUP001", "SupplierName": "Ramraj Cotton", "ContactPerson": "Arun Kumar", "Phone": "9876543201", "Email": "sup001@retailai.com", "City": "Coimbatore", "State": "Tamil Nadu"},
    {"SupplierID": "SUP002", "SupplierName": "Raymond", "ContactPerson": "Vijay Sharma", "Phone": "9876543202", "Email": "sup002@retailai.com", "City": "Mumbai", "State": "Maharashtra"},
    {"SupplierID": "SUP003", "SupplierName": "Biba", "ContactPerson": "Priya Singh", "Phone": "9876543203", "Email": "sup003@retailai.com", "City": "New Delhi", "State": "Delhi"},
    {"SupplierID": "SUP004", "SupplierName": "Fabindia", "ContactPerson": "Rahul Verma", "Phone": "9876543204", "Email": "sup004@retailai.com", "City": "New Delhi", "State": "Delhi"},
    {"SupplierID": "SUP005", "SupplierName": "Westside", "ContactPerson": "Sneha Gupta", "Phone": "9876543205", "Email": "sup005@retailai.com", "City": "Bengaluru", "State": "Karnataka"},
    {"SupplierID": "SUP006", "SupplierName": "Uathayam", "ContactPerson": "Murugan", "Phone": "9876543206", "Email": "sup006@retailai.com", "City": "Erode", "State": "Tamil Nadu"},
    {"SupplierID": "SUP007", "SupplierName": "Prisma", "ContactPerson": "Karthik", "Phone": "9876543207", "Email": "sup007@retailai.com", "City": "Chennai", "State": "Tamil Nadu"},
    {"SupplierID": "SUP008", "SupplierName": "Guess", "ContactPerson": "Amit Verma", "Phone": "9876543208", "Email": "sup008@retailai.com", "City": "Hyderabad", "State": "Telangana"},
    {"SupplierID": "SUP009", "SupplierName": "Nandu Lungi", "ContactPerson": "Suresh", "Phone": "9876543209", "Email": "sup009@retailai.com", "City": "Salem", "State": "Tamil Nadu"},
    {"SupplierID": "SUP010", "SupplierName": "Peter England", "ContactPerson": "Rakesh", "Phone": "9876543210", "Email": "sup010@retailai.com", "City": "Bengaluru", "State": "Karnataka"},
    {"SupplierID": "SUP011", "SupplierName": "Louis Philippe", "ContactPerson": "Ajay Kumar", "Phone": "9876543211", "Email": "sup011@retailai.com", "City": "Chennai", "State": "Tamil Nadu"},
    {"SupplierID": "SUP012", "SupplierName": "Allen Solly", "ContactPerson": "Kiran Rao", "Phone": "9876543212", "Email": "sup012@retailai.com", "City": "Pune", "State": "Maharashtra"},
    {"SupplierID": "SUP013", "SupplierName": "Van Heusen", "ContactPerson": "Sanjay Patel", "Phone": "9876543213", "Email": "sup013@retailai.com", "City": "Ahmedabad", "State": "Gujarat"},
    {"SupplierID": "SUP014", "SupplierName": "Levi's", "ContactPerson": "Rohan Shah", "Phone": "9876543214", "Email": "sup014@retailai.com", "City": "Mumbai", "State": "Maharashtra"},
    {"SupplierID": "SUP015", "SupplierName": "Pepe Jeans", "ContactPerson": "Anita Das", "Phone": "9876543215", "Email": "sup015@retailai.com", "City": "Kolkata", "State": "West Bengal"},
    {"SupplierID": "SUP016", "SupplierName": "US Polo", "ContactPerson": "Deepak Singh", "Phone": "9876543216", "Email": "sup016@retailai.com", "City": "Lucknow", "State": "Uttar Pradesh"},
    {"SupplierID": "SUP017", "SupplierName": "Arrow", "ContactPerson": "Manoj Kumar", "Phone": "9876543217", "Email": "sup017@retailai.com", "City": "Jaipur", "State": "Rajasthan"},
    {"SupplierID": "SUP018", "SupplierName": "Nike", "ContactPerson": "Arvind Nair", "Phone": "9876543218", "Email": "sup018@retailai.com", "City": "Kochi", "State": "Kerala"},
    {"SupplierID": "SUP019", "SupplierName": "Adidas", "ContactPerson": "Hari Prasad", "Phone": "9876543219", "Email": "sup019@retailai.com", "City": "Hyderabad", "State": "Telangana"},
    {"SupplierID": "SUP020", "SupplierName": "Puma", "ContactPerson": "Mahesh Reddy", "Phone": "9876543220", "Email": "sup020@retailai.com", "City": "Visakhapatnam", "State": "Andhra Pradesh"},
    {"SupplierID": "SUP021", "SupplierName": "Campus", "ContactPerson": "Ravi Teja", "Phone": "9876543221", "Email": "sup021@retailai.com", "City": "Vijayawada", "State": "Andhra Pradesh"},
    {"SupplierID": "SUP022", "SupplierName": "Jockey", "ContactPerson": "Vinod Menon", "Phone": "9876543222", "Email": "sup022@retailai.com", "City": "Bengaluru", "State": "Karnataka"},
    {"SupplierID": "SUP023", "SupplierName": "Lux", "ContactPerson": "Gopal Iyer", "Phone": "9876543223", "Email": "sup023@retailai.com", "City": "Madurai", "State": "Tamil Nadu"},
    {"SupplierID": "SUP024", "SupplierName": "VIP", "ContactPerson": "Balaji Kumar", "Phone": "9876543224", "Email": "sup024@retailai.com", "City": "Tiruppur", "State": "Tamil Nadu"},
    {"SupplierID": "SUP025", "SupplierName": "Wildcraft", "ContactPerson": "Naveen Raj", "Phone": "9876543225", "Email": "sup025@retailai.com", "City": "Mysuru", "State": "Karnataka"},
]

RAW_USERS = [
    {"UserID": "U0001", "Username": "admin", "Password": "admin123", "FullName": "System Administrator", "Role": "Admin", "Email": "admin@retailai.com"},
    {"UserID": "U0002", "Username": "manager", "Password": "manager123", "FullName": "Store Manager", "Role": "Manager", "Email": "manager@retailai.com"},
    {"UserID": "U0003", "Username": "employee1", "Password": "employee123", "FullName": "Arun Kumar", "Role": "Employee", "Email": "employee1@retailai.com"},
    {"UserID": "U0004", "Username": "employee2", "Password": "employee123", "FullName": "Priya Sharma", "Role": "Employee", "Email": "employee2@retailai.com"},
    {"UserID": "U0005", "Username": "employee3", "Password": "employee123", "FullName": "Rahul Verma", "Role": "Employee", "Email": "employee3@retailai.com"},
    {"UserID": "U0006", "Username": "employee4", "Password": "employee123", "FullName": "Sneha Gupta", "Role": "Employee", "Email": "employee4@retailai.com"},
    {"UserID": "U0007", "Username": "employee5", "Password": "employee123", "FullName": "Karthik Raj", "Role": "Employee", "Email": "employee5@retailai.com"},
    {"UserID": "U0008", "Username": "employee6", "Password": "employee123", "FullName": "Divya Nair", "Role": "Employee", "Email": "employee6@retailai.com"},
    {"UserID": "U0009", "Username": "employee7", "Password": "employee123", "FullName": "Vignesh Kumar", "Role": "Employee", "Email": "employee7@retailai.com"},
    {"UserID": "U0010", "Username": "employee8", "Password": "employee123", "FullName": "Meena Krishnan", "Role": "Employee", "Email": "employee8@retailai.com"},
]


def seed():
    print("========== CREATING DATABASE TABLES ==========")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # 1. Seed Suppliers (Upsert brand suppliers)
        print("\n--- Seeding Suppliers ---")
        for s in RAW_SUPPLIERS:
            existing = db.query(models.Supplier).filter(models.Supplier.SupplierID == s["SupplierID"]).first()
            if existing:
                existing.SupplierName = s["SupplierName"]
                existing.ContactPerson = s["ContactPerson"]
                existing.Phone = s["Phone"]
                existing.Email = s["Email"]
                existing.City = s["City"]
                existing.State = s["State"]
            else:
                db.add(models.Supplier(**s))
        db.commit()
        print(f"Seeded/Updated {len(RAW_SUPPLIERS)} brand suppliers.")

        # 2. Products
        print("\n--- Seeding Products ---")
        if db.query(models.Product).count() == 0:
            df = pd.read_csv(DATA_DIR / "products_clean.csv")
            records = df.to_dict(orient="records")
            products = [
                models.Product(
                    ProductID=r["ProductID"],
                    SKU=r.get("SKU"),
                    ProductName=r["ProductName"],
                    Category=r.get("Category"),
                    SubCategory=r.get("SubCategory"),
                    Brand=r.get("Brand"),
                    Color=r.get("Color"),
                    Size=r.get("Size"),
                    Fabric=r.get("Fabric"),
                    SeasonalDemandTag=r.get("SeasonalDemandTag"),
                    Gender=r.get("Gender"),
                    Price=float(r["Price"]) if pd.notna(r.get("Price")) else 0.0,
                    CostPrice=float(r["CostPrice"]) if pd.notna(r.get("CostPrice")) else 0.0,
                    SupplierID=r.get("SupplierID"),
                    ProductStatus=r.get("ProductStatus"),
                    ImageURL=r.get("ImageURL"),
                    ProfitMargin=float(r["ProfitMargin"]) if pd.notna(r.get("ProfitMargin")) else 0.0,
                )
                for r in records
            ]
            db.bulk_save_objects(products)
            db.commit()
            print(f"Seeded {len(products)} products.")
        else:
            print("Products already exist.")

        # 3. Customers
        print("\n--- Seeding Customers ---")
        if db.query(models.Customer).count() == 0:
            df = pd.read_csv(DATA_DIR / "customers_clean.csv")
            records = df.to_dict(orient="records")
            customers = []
            for r in records:
                join_dt = None
                if pd.notna(r.get("JoinDate")):
                    try:
                        join_dt = datetime.strptime(str(r["JoinDate"]).split()[0], "%Y-%m-%d").date()
                    except Exception:
                        pass
                customers.append(
                    models.Customer(
                        CustomerID=r["CustomerID"],
                        FullName=r["FullName"],
                        Gender=r.get("Gender"),
                        Age=int(r["Age"]) if pd.notna(r.get("Age")) else None,
                        City=r.get("City"),
                        State=r.get("State"),
                        Membership=r.get("Membership"),
                        JoinDate=join_dt,
                        PreferredCategory=r.get("PreferredCategory"),
                        PreferredFabric=r.get("PreferredFabric"),
                        PreferredPriceRange=r.get("PreferredPriceRange"),
                        LoyaltyPoints=int(r["LoyaltyPoints"]) if pd.notna(r.get("LoyaltyPoints")) else 0,
                        CustomerTenureDays=int(r["CustomerTenureDays"]) if pd.notna(r.get("CustomerTenureDays")) else 0,
                    )
                )
            db.bulk_save_objects(customers)
            db.commit()
            print(f"Seeded {len(customers)} customers.")
        else:
            print("Customers already exist.")

        # 4. Inventory
        print("\n--- Seeding Inventory ---")
        if db.query(models.Inventory).count() == 0:
            df = pd.read_csv(DATA_DIR / "inventory_clean.csv")
            records = df.to_dict(orient="records")
            inventory_items = []
            for r in records:
                last_restocked = None
                if pd.notna(r.get("LastRestocked")):
                    try:
                        last_restocked = datetime.strptime(str(r["LastRestocked"]).split()[0], "%Y-%m-%d").date()
                    except Exception:
                        pass
                inventory_items.append(
                    models.Inventory(
                        ProductID=r["ProductID"],
                        Warehouse=r.get("Warehouse", "Central WH"),
                        CurrentStock=int(r["CurrentStock"]) if pd.notna(r.get("CurrentStock")) else 0,
                        MinimumStock=int(r["MinimumStock"]) if pd.notna(r.get("MinimumStock")) else 0,
                        MaximumStock=int(r["MaximumStock"]) if pd.notna(r.get("MaximumStock")) else 0,
                        SafetyStock=int(r["SafetyStock"]) if pd.notna(r.get("SafetyStock")) else 0,
                        ReorderPoint=int(r["ReorderPoint"]) if pd.notna(r.get("ReorderPoint")) else 0,
                        LeadTimeDays=int(r["LeadTimeDays"]) if pd.notna(r.get("LeadTimeDays")) else 0,
                        SupplierID=r.get("SupplierID"),
                        LastRestocked=last_restocked,
                        InventoryStatus=r.get("InventoryStatus"),
                        StockUtilisation=float(r["StockUtilisation"]) if pd.notna(r.get("StockUtilisation")) else 0.0,
                        DaysSinceRestock=int(r["DaysSinceRestock"]) if pd.notna(r.get("DaysSinceRestock")) else 0,
                    )
                )
            db.bulk_save_objects(inventory_items)
            db.commit()
            print(f"Seeded {len(inventory_items)} inventory records.")
        else:
            print("Inventory already exists.")

        # 5. Sales
        print("\n--- Seeding Sales ---")
        if db.query(models.Sale).count() == 0:
            df = pd.read_csv(DATA_DIR / "sales_clean.csv")
            records = df.to_dict(orient="records")
            batch_size = 5000
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                sales_batch = []
                for r in batch:
                    sale_dt = None
                    if pd.notna(r.get("SaleDate")):
                        try:
                            sale_dt = datetime.strptime(str(r["SaleDate"]).split()[0], "%Y-%m-%d").date()
                        except Exception:
                            pass
                    sales_batch.append(
                        models.Sale(
                            SaleID=r["SaleID"],
                            InvoiceID=r.get("InvoiceID"),
                            CustomerID=r["CustomerID"],
                            ProductID=r["ProductID"],
                            SubCategory=r.get("SubCategory"),
                            SaleDate=sale_dt,
                            Quantity=int(r["Quantity"]) if pd.notna(r.get("Quantity")) else 1,
                            MRP=float(r["MRP"]) if pd.notna(r.get("MRP")) else 0.0,
                            DiscountPercent=float(r["DiscountPercent"]) if pd.notna(r.get("DiscountPercent")) else 0.0,
                            FinalPrice=float(r["FinalPrice"]) if pd.notna(r.get("FinalPrice")) else 0.0,
                            Festival=r.get("Festival"),
                            Season=r.get("Season"),
                            DayOfWeek=r.get("DayOfWeek"),
                            SaleMonth=int(r["SaleMonth"]) if pd.notna(r.get("SaleMonth")) else None,
                            SaleYear=int(r["SaleYear"]) if pd.notna(r.get("SaleYear")) else None,
                        )
                    )
                db.bulk_save_objects(sales_batch)
                db.commit()
                print(f"Seeded sales batch {i} to {i + len(batch)}.")
            print("Sales seeding complete.")
        else:
            print("Sales already exist.")

        # 6. Forecast Results
        print("\n--- Seeding Forecast Results ---")
        if db.query(models.ForecastResult).count() == 0:
            df = pd.read_csv(DATA_DIR / "forecast_results.csv")
            records = df.to_dict(orient="records")
            batch_size = 5000
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                forecasts = [
                    models.ForecastResult(
                        ProductID=r["ProductID"],
                        YearMonth=str(r["YearMonth"]),
                        Quantity=int(r["Quantity"]) if pd.notna(r.get("Quantity")) else 0,
                        Revenue=float(r["Revenue"]) if pd.notna(r.get("Revenue")) else 0.0,
                        Category=r.get("Category"),
                        SubCategory=r.get("SubCategory"),
                        Brand=r.get("Brand"),
                        Price=float(r["Price"]) if pd.notna(r.get("Price")) else 0.0,
                        Year=int(r["Year"]) if pd.notna(r.get("Year")) else None,
                        Month=int(r["Month"]) if pd.notna(r.get("Month")) else None,
                        Quarter=int(r["Quarter"]) if pd.notna(r.get("Quarter")) else None,
                        Week=int(r["Week"]) if pd.notna(r.get("Week")) else None,
                        Day=int(r["Day"]) if pd.notna(r.get("Day")) else None,
                        AveragePrice=float(r["AveragePrice"]) if pd.notna(r.get("AveragePrice")) else 0.0,
                        Season=r.get("Season"),
                        Festival=r.get("Festival"),
                        TargetQuantity=int(r["TargetQuantity"]) if pd.notna(r.get("TargetQuantity")) else 0,
                        TargetRevenue=float(r["TargetRevenue"]) if pd.notna(r.get("TargetRevenue")) else 0.0,
                    )
                    for r in batch
                ]
                db.bulk_save_objects(forecasts)
                db.commit()
                print(f"Seeded forecast batch {i} to {i + len(batch)}.")
            print("ForecastResults seeding complete.")
        else:
            print("ForecastResults already exist.")

        # 7. Users (Upsert 10 staff members)
        print("\n--- Seeding Users ---")
        for u in RAW_USERS:
            existing = db.query(models.User).filter(models.User.UserID == u["UserID"]).first()
            if existing:
                existing.Username = u["Username"]
                existing.Password = u["Password"]
                existing.FullName = u["FullName"]
                existing.Role = u["Role"]
                existing.Email = u["Email"]
            else:
                db.add(models.User(**u))
        db.commit()
        print(f"Seeded/Updated {len(RAW_USERS)} staff users.")

        # 8. Create SQL Views and Performance Indexes
        print("\n--- Creating SQL Views and Performance Indexes ---")
        view_product_inventory = """
        CREATE OR REPLACE VIEW ProductInventory AS
        SELECT
            p."ProductID",
            p."ProductName",
            p."Brand",
            i."CurrentStock",
            i."InventoryStatus",
            i."ReorderPoint"
        FROM products p
        JOIN inventory i ON p."ProductID" = i."ProductID";
        """
        view_customer_purchases = """
        CREATE OR REPLACE VIEW CustomerPurchases AS
        SELECT
            c."CustomerID",
            c."FullName",
            p."ProductName",
            s."Quantity",
            s."FinalPrice",
            s."SaleDate"
        FROM sales s
        JOIN customers c ON s."CustomerID" = c."CustomerID"
        JOIN products p ON s."ProductID" = p."ProductID";
        """
        db.execute(text(view_product_inventory))
        db.execute(text(view_customer_purchases))

        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_inventory_productid ON inventory("ProductID");',
            'CREATE INDEX IF NOT EXISTS idx_inventory_status ON inventory("InventoryStatus");',
            'CREATE INDEX IF NOT EXISTS idx_inventory_current_safety ON inventory("CurrentStock", "SafetyStock");',
            'CREATE INDEX IF NOT EXISTS idx_inventory_current_reorder ON inventory("CurrentStock", "ReorderPoint");',
            'CREATE INDEX IF NOT EXISTS idx_products_productid ON products("ProductID");',
            'CREATE INDEX IF NOT EXISTS idx_sales_customerid ON sales("CustomerID");',
            'CREATE INDEX IF NOT EXISTS idx_sales_productid ON sales("ProductID");',
            'CREATE INDEX IF NOT EXISTS idx_sales_saledate ON sales("SaleDate");',
            'CREATE INDEX IF NOT EXISTS idx_forecastresults_ym_desc ON forecastresults("YearMonth" DESC);',
            'CREATE INDEX IF NOT EXISTS idx_forecastresults_ym_prod ON forecastresults("YearMonth", "ProductID");',
        ]
        for idx in indexes:
            db.execute(text(idx))
        db.commit()
        print("Created views (ProductInventory, CustomerPurchases) and 10 performance indexes.")

        print("\n========== ALL DATABASE TABLES, SEED DATA, AND VIEWS CREATED SUCCESSFULLY ==========")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database seeding failed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
