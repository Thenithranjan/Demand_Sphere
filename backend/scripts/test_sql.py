import sys
import time
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal, engine
from sqlalchemy import text

db = SessionLocal()

print("--- Creating Advanced Indexes on PostgreSQL ---")
indexes_sql = [
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

with engine.begin() as conn:
    for idx_sql in indexes_sql:
        conn.execute(text(idx_sql))
print("Advanced Indexes Created!")

print("\n--- Testing Optimized Raw SQL Queries ---")

t0 = time.time()
sql_alerts = text("""
WITH latest_fc AS (
    SELECT "ProductID", "Quantity"
    FROM forecastresults
    WHERE "YearMonth" = (SELECT "YearMonth" FROM forecastresults ORDER BY "YearMonth" DESC LIMIT 1)
)
SELECT
    i."ProductID",
    p."ProductName",
    i."Warehouse",
    i."CurrentStock",
    i."SafetyStock",
    i."ReorderPoint",
    COALESCE(f."Quantity", i."ReorderPoint" * 2) AS "ForecastDemand",
    'Reorder Immediately' AS "Recommendation"
FROM inventory i
JOIN products p ON i."ProductID" = p."ProductID"
LEFT JOIN latest_fc f ON i."ProductID" = f."ProductID"
WHERE i."CurrentStock" <= i."SafetyStock"
""")

alerts_rows = db.execute(sql_alerts).mappings().all()
t1 = time.time()
print(f"CTE-Optimized Alerts SQL Time: {round((t1 - t0) * 1000, 2)} ms | Rows: {len(alerts_rows)}")

t2 = time.time()
sql_low_stock = text("""
WITH latest_fc AS (
    SELECT "ProductID", "Quantity"
    FROM forecastresults
    WHERE "YearMonth" = (SELECT "YearMonth" FROM forecastresults ORDER BY "YearMonth" DESC LIMIT 1)
)
SELECT
    i."ProductID",
    p."ProductName",
    i."Warehouse",
    i."CurrentStock",
    i."SafetyStock",
    i."ReorderPoint",
    COALESCE(f."Quantity", i."ReorderPoint" * 2) AS "ForecastDemand",
    'Reorder Immediately' AS "Recommendation"
FROM inventory i
JOIN products p ON i."ProductID" = p."ProductID"
LEFT JOIN latest_fc f ON i."ProductID" = f."ProductID"
WHERE i."CurrentStock" <= i."ReorderPoint"
""")

low_stock_rows = db.execute(sql_low_stock).mappings().all()
t3 = time.time()
print(f"CTE-Optimized Low Stock SQL Time: {round((t3 - t2) * 1000, 2)} ms | Rows: {len(low_stock_rows)}")

db.close()
