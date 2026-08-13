# Executive EDA Summary: Retail Intelligence System

This report summarizes the findings of the Exploratory Data Analysis (EDA) module for the **AI-Powered Retail Intelligence System for Textile Stores**. All calculations are compiled dynamically from the processed retail datasets.

---

## 📊 Core Business KPIs

| Metric | Value | Business Significance |
| :--- | :--- | :--- |
| **Total Sales Revenue** | ₹89,097,332.50 | Represents the gross sales volume across the entire transactional history. |
| **Total Transactions** | 50,000 | Total count of sales invoices, showing customer traffic volume. |
| **Active Customers Profiled** | 2,000 | Total unique customers logged in the CRM profile database. |
| **Active Products in Catalog** | 500 | Size of the catalog variety across category segments. |
| **Average Customer Age** | 41.6 Years | Average demographic age profile of the stores' shoppers. |
| **Average Product Profit Margin** | 33.01% | Expected margin buffer to absorb discounts and promotions. |
| **Low-Stock Alert Items** | 60 Products | Catalog items currently sitting at or below minimum stock thresholds. |
| **Reorder Triggers Reached** | 118 Products | Items that have breached reorder thresholds and require restock orders. |
| **Total Inventory Volume** | 53,178 Units | Total stock units currently held across all warehouses. |

---

## 📈 Sales Insights

### Key Trends & Observations
1. **Monthly Sales Performance**: The time-series graphs trace transaction volumes and revenue growth. Spike periods highlight promotional success.
2. **Seasonal & Festival Dynamics**: Festivals like Diwali and Pongal drive massive revenue contribution, confirming the critical role of seasonal apparel stocks.
3. **Weekend Traffic spikes**: Sales volume on weekends compared to weekdays highlights the need for active staffing and real-time weekend promotions.

### Visualizations
````carousel
![Monthly Sales Trend](sales_monthly_trend.png)
<!-- slide -->
![Revenue Trend](sales_revenue_trend.png)
<!-- slide -->
![Quantity Sold Trend](sales_quantity_trend.png)
<!-- slide -->
![Festival Sales Contribution](sales_festival.png)
<!-- slide -->
![Seasonal Sales Contribution](sales_seasonal.png)
<!-- slide -->
![Top Products](sales_top_products.png)
<!-- slide -->
![Top Categories](sales_top_categories.png)
<!-- slide -->
![Top Brands](sales_top_brands.png)
<!-- slide -->
![Daily Distribution](sales_daily_distribution.png)
<!-- slide -->
![Weekend vs Weekday](sales_weekend_weekday.png)
````

---

## 👥 Customer Insights

### Key Trends & Observations
1. **Demographic Target**: Age distributions reveal whether the buyer profile skew is youthful or mature, letting marketing adjust catalog campaigns.
2. **Membership Loyalty**: Loyalty program distribution details the sizes of Silver, Gold, and Platinum cohorts, proving the value of loyalty points.
3. **Customer Value Segmentation**: The Tenure vs. Loyalty Points scatter plot identifies the highest value VIP groups who have long tenures and high loyalty scores.

### Visualizations
````carousel
![Age Distribution](customer_age_distribution.png)
<!-- slide -->
![Gender Distribution](customer_gender_distribution.png)
<!-- slide -->
![Membership Distribution](customer_membership_distribution.png)
<!-- slide -->
![Preferred Category](customer_preferred_category.png)
<!-- slide -->
![Preferred Fabric](customer_preferred_fabric.png)
<!-- slide -->
![Top Spenders](customer_top_spenders.png)
<!-- slide -->
![Loyalty Distribution](customer_loyalty_distribution.png)
<!-- slide -->
![Segmentation Scatter](customer_segmentation_overview.png)
````

---

## 👕 Product Insights

### Key Trends & Observations
1. **Catalog Density**: Product counts across category, brand, and fabric groupings show where inventory investments are focused.
2. **Pricing Structure**: The retail price distribution displays whether product offerings align with budget, premium, or luxury categories.
3. **Profit Margins**: Profit margin distributions show where margins concentrate, helping plan catalog markdowns.

### Visualizations
````carousel
![Product Category Distribution](product_category_distribution.png)
<!-- slide -->
![Product Brand Distribution](product_brand_distribution.png)
<!-- slide -->
![Product Fabric Distribution](product_fabric_distribution.png)
<!-- slide -->
![Product Price Distribution](product_price_distribution.png)
<!-- slide -->
![Product Profit Distribution](product_profit_distribution.png)
<!-- slide -->
![Product Seasonal Demand](product_seasonal_distribution.png)
````

---

## 📦 Inventory Insights

### Key Trends & Observations
1. **Low Stock Risks**: Highlights products that have breached safety lines, indicating potential stockout loss if not replinished.
2. **Overstock Assets**: Pinpoints products exceeding maximum thresholds, which ties up warehouse space and cash flow.
3. **Warehouse Allocation**: Distribution of current stock across Chennai, Madurai, and Coimbatore locations.
4. **Reorder Urgency**: Comparative visual check of current stock against reorder points flags critical procurement needs.

### Visualizations
````carousel
![Stock Distribution](inventory_stock_distribution.png)
<!-- slide -->
![Low Stock Products](inventory_low_stock.png)
<!-- slide -->
![Overstock Products](inventory_overstock.png)
<!-- slide -->
![Warehouse Stocks](inventory_warehouse_stock.png)
<!-- slide -->
![Safety Stock Analysis](inventory_safety_stock.png)
<!-- slide -->
![Reorder Point Analysis](inventory_reorder_point.png)
````

---

## 🤖 Recommendation Insights

### Key Trends & Observations
1. **Catalog Coverage Bias**: Tracks the most frequently recommended products to see if recommendation models have a popularity bias.
2. **Empirical Cross-Sell Co-occurrences**: Shows which item subcategories (e.g. Shirts + Pants) are bought together in historical sales invoices, validating complementary rules.
3. **Score Distribution**: The distribution of hybrid recommendation scores verifies the confidence of customer match rates.

### Visualizations
````carousel
![Most Recommended Products](recs_most_recommended.png)
<!-- slide -->
![Cross-Sell Co-occurrences](recs_cross_sell_frequency.png)
<!-- slide -->
![Score Distribution](recs_score_distribution.png)
````
