CREATE DATABASE retail_ai;
USE retail_ai;

CREATE TABLE Suppliers (
    SupplierID VARCHAR(10) PRIMARY KEY,
    SupplierName VARCHAR(100) NOT NULL,
    ContactPerson VARCHAR(100),
    Phone VARCHAR(20),
    Email VARCHAR(100),
    City VARCHAR(50),
    State VARCHAR(50)
);
INSERT INTO Suppliers
VALUES
('SUP001','Ramraj Cotton','Arun Kumar','9876543201','sup001@retailai.com','Coimbatore','Tamil Nadu'),
('SUP002','Raymond','Vijay Sharma','9876543202','sup002@retailai.com','Mumbai','Maharashtra'),
('SUP003','Biba','Priya Singh','9876543203','sup003@retailai.com','New Delhi','Delhi'),
('SUP004','Fabindia','Rahul Verma','9876543204','sup004@retailai.com','New Delhi','Delhi'),
('SUP005','Westside','Sneha Gupta','9876543205','sup005@retailai.com','Bengaluru','Karnataka'),
('SUP006','Uathayam','Murugan','9876543206','sup006@retailai.com','Erode','Tamil Nadu'),
('SUP007','Prisma','Karthik','9876543207','sup007@retailai.com','Chennai','Tamil Nadu'),
('SUP008','Guess','Amit Verma','9876543208','sup008@retailai.com','Hyderabad','Telangana'),
('SUP009','Nandu Lungi','Suresh','9876543209','sup009@retailai.com','Salem','Tamil Nadu'),
('SUP010','Peter England','Rakesh','9876543210','sup010@retailai.com','Bengaluru','Karnataka'),
('SUP011','Louis Philippe','Ajay Kumar','9876543211','sup011@retailai.com','Chennai','Tamil Nadu'),
('SUP012','Allen Solly','Kiran Rao','9876543212','sup012@retailai.com','Pune','Maharashtra'),
('SUP013','Van Heusen','Sanjay Patel','9876543213','sup013@retailai.com','Ahmedabad','Gujarat'),
('SUP014','Levi''s','Rohan Shah','9876543214','sup014@retailai.com','Mumbai','Maharashtra'),
('SUP015','Pepe Jeans','Anita Das','9876543215','sup015@retailai.com','Kolkata','West Bengal'),
('SUP016','US Polo','Deepak Singh','9876543216','sup016@retailai.com','Lucknow','Uttar Pradesh'),
('SUP017','Arrow','Manoj Kumar','9876543217','sup017@retailai.com','Jaipur','Rajasthan'),
('SUP018','Nike','Arvind Nair','9876543218','sup018@retailai.com','Kochi','Kerala'),
('SUP019','Adidas','Hari Prasad','9876543219','sup019@retailai.com','Hyderabad','Telangana'),
('SUP020','Puma','Mahesh Reddy','9876543220','sup020@retailai.com','Visakhapatnam','Andhra Pradesh'),
('SUP021','Campus','Ravi Teja','9876543221','sup021@retailai.com','Vijayawada','Andhra Pradesh'),
('SUP022','Jockey','Vinod Menon','9876543222','sup022@retailai.com','Bengaluru','Karnataka'),
('SUP023','Lux','Gopal Iyer','9876543223','sup023@retailai.com','Madurai','Tamil Nadu'),
('SUP024','VIP','Balaji Kumar','9876543224','sup024@retailai.com','Tiruppur','Tamil Nadu'),
('SUP025','Wildcraft','Naveen Raj','9876543225','sup025@retailai.com','Mysuru','Karnataka');


CREATE TABLE Products (
    ProductID VARCHAR(10) PRIMARY KEY,
    SKU VARCHAR(30) UNIQUE,
    ProductName VARCHAR(150) NOT NULL,
    Category VARCHAR(50),
    SubCategory VARCHAR(50),
    Brand VARCHAR(50),
    Color VARCHAR(30),
    Size VARCHAR(20),
    Fabric VARCHAR(50),
    SeasonalDemandTag VARCHAR(50),
    Gender VARCHAR(20),
    Price DECIMAL(10,2),
    CostPrice DECIMAL(10,2),
    SupplierID VARCHAR(10),
    ProductStatus VARCHAR(30),
    ImageURL VARCHAR(255),
    ProfitMargin DECIMAL(10,2)
);
SELECT * FROM Products LIMIT 10;
SELECT COUNT(*) AS TotalProducts
FROM Products;


CREATE TABLE Customers (
    CustomerID VARCHAR(10) PRIMARY KEY,
    FullName VARCHAR(100) NOT NULL,
    Gender VARCHAR(20),
    Age INT,
    City VARCHAR(100),
    State VARCHAR(100),
    Membership VARCHAR(30),
    JoinDate DATE,
    PreferredCategory VARCHAR(50),
    PreferredFabric VARCHAR(50),
    PreferredPriceRange VARCHAR(30),
    LoyaltyPoints INT,
    CustomerTenureDays INT
);
SELECT * FROM Customers LIMIT 10;
SELECT COUNT(*) AS TotalCustomers
FROM Customers;


CREATE TABLE Inventory (
    ProductID VARCHAR(10) NOT NULL,
    Warehouse VARCHAR(100),
    CurrentStock INT,
    MinimumStock INT,
    MaximumStock INT,
    SafetyStock INT,
    ReorderPoint INT,
    LeadTimeDays INT,
    SupplierID VARCHAR(10),
    LastRestocked DATE,
    InventoryStatus VARCHAR(30),
    StockUtilisation DECIMAL(5,2),
    DaysSinceRestock INT,
    PRIMARY KEY (ProductID, Warehouse)
);
SELECT * FROM Inventory LIMIT 10;
SELECT COUNT(*) AS TotalInventory
FROM Inventory;


CREATE TABLE Sales (
    SaleID VARCHAR(15) PRIMARY KEY,
    InvoiceID VARCHAR(20),
    CustomerID VARCHAR(10) NOT NULL,
    ProductID VARCHAR(10) NOT NULL,
    SubCategory VARCHAR(50),
    SaleDate DATE,
    Quantity INT,
    MRP DECIMAL(10,2),
    DiscountPercent DECIMAL(5,2),
    FinalPrice DECIMAL(10,2),
    Festival VARCHAR(50),
    Season VARCHAR(30),
    DayOfWeek VARCHAR(15),
    SaleMonth INT,
    SaleYear INT
);
SELECT * FROM Sales LIMIT 10;
SELECT COUNT(*) AS TotalSales
FROM Sales;


CREATE TABLE ForecastResults (
    ProductID VARCHAR(10) NOT NULL,
    YearMonth VARCHAR(7) NOT NULL,
    Quantity INT,
    Revenue DECIMAL(12,2),
    Category VARCHAR(50),
    SubCategory VARCHAR(50),
    Brand VARCHAR(50),
    Price DECIMAL(10,2),
    Year INT,
    Month INT,
    Quarter INT,
    Week INT,
    Day INT,
    AveragePrice DECIMAL(10,2),
    Season VARCHAR(30),
    Festival VARCHAR(50),
    TargetQuantity INT,
    TargetRevenue DECIMAL(12,2),
    PRIMARY KEY (ProductID, YearMonth)
);
SELECT * FROM ForecastResults LIMIT 10;
SELECT COUNT(*) AS TotalForecastRecords
FROM ForecastResults;



CREATE TABLE Users (
    UserID VARCHAR(10) PRIMARY KEY,
    Username VARCHAR(50) UNIQUE,
    Password VARCHAR(255),
    FullName VARCHAR(100),
    Role VARCHAR(20),
    Email VARCHAR(100),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO Users
VALUES
('U0001','admin','admin123','System Administrator','Admin','admin@retailai.com',CURRENT_TIMESTAMP),
('U0002','manager','manager123','Store Manager','Manager','manager@retailai.com',CURRENT_TIMESTAMP),
('U0003','employee1','employee123','Arun Kumar','Employee','employee1@retailai.com',CURRENT_TIMESTAMP),
('U0004','employee2','employee123','Priya Sharma','Employee','employee2@retailai.com',CURRENT_TIMESTAMP),
('U0005','employee3','employee123','Rahul Verma','Employee','employee3@retailai.com',CURRENT_TIMESTAMP),
('U0006','employee4','employee123','Sneha Gupta','Employee','employee4@retailai.com',CURRENT_TIMESTAMP),
('U0007','employee5','employee123','Karthik Raj','Employee','employee5@retailai.com',CURRENT_TIMESTAMP),
('U0008','employee6','employee123','Divya Nair','Employee','employee6@retailai.com',CURRENT_TIMESTAMP),
('U0009','employee7','employee123','Vignesh Kumar','Employee','employee7@retailai.com',CURRENT_TIMESTAMP),
('U0010','employee8','employee123','Meena Krishnan','Employee','employee8@retailai.com',CURRENT_TIMESTAMP);

ALTER TABLE Products
ADD CONSTRAINT FK_Product_Supplier
FOREIGN KEY (SupplierID)
REFERENCES Suppliers(SupplierID);

ALTER TABLE Inventory
ADD CONSTRAINT FK_Inventory_Product
FOREIGN KEY (ProductID)
REFERENCES Products(ProductID);

ALTER TABLE Inventory
ADD CONSTRAINT FK_Inventory_Supplier
FOREIGN KEY (SupplierID)
REFERENCES Suppliers(SupplierID);

ALTER TABLE Sales
ADD CONSTRAINT FK_Sales_Product
FOREIGN KEY (ProductID)
REFERENCES Products(ProductID);

ALTER TABLE Sales
ADD CONSTRAINT FK_Sales_Customer
FOREIGN KEY (CustomerID)
REFERENCES Customers(CustomerID);

ALTER TABLE ForecastResults
ADD CONSTRAINT FK_Forecast_Product
FOREIGN KEY (ProductID)
REFERENCES Products(ProductID);

SELECT
p.ProductID,
p.ProductName,
s.SupplierName
FROM Products p
JOIN Suppliers s
ON p.SupplierID = s.SupplierID
LIMIT 20;


SELECT
sa.SaleID,
c.FullName,
p.ProductName,
sa.Quantity,
sa.FinalPrice
FROM Sales sa
JOIN Customers c
ON sa.CustomerID = c.CustomerID
JOIN Products p
ON sa.ProductID = p.ProductID
LIMIT 20;


SELECT
p.ProductName,
i.CurrentStock,
i.InventoryStatus
FROM Products p
JOIN Inventory i
ON p.ProductID = i.ProductID
LIMIT 20;

CREATE VIEW ProductInventory AS
SELECT
p.ProductID,
p.ProductName,
p.Brand,
i.CurrentStock,
i.InventoryStatus,
i.ReorderPoint
FROM Products p
JOIN Inventory i
ON p.ProductID = i.ProductID;

CREATE VIEW CustomerPurchases AS
SELECT
c.CustomerID,
c.FullName,
p.ProductName,
s.Quantity,
s.FinalPrice,
s.SaleDate
FROM Sales s
JOIN Customers c
ON s.CustomerID = c.CustomerID
JOIN Products p
ON s.ProductID = p.ProductID;

SELECT *
FROM Inventory
WHERE CurrentStock < ReorderPoint;

SELECT
ProductID,
SUM(Quantity) AS TotalSold
FROM Sales
GROUP BY ProductID
ORDER BY TotalSold DESC
LIMIT 10;

SELECT
SaleMonth,
SUM(FinalPrice) AS Revenue
FROM Sales
GROUP BY SaleMonth;

SELECT
CustomerID,
SUM(FinalPrice) AS TotalSpent
FROM Sales
GROUP BY CustomerID
ORDER BY TotalSpent DESC
LIMIT 10;