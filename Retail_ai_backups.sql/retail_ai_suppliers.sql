-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: retail_ai
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `suppliers`
--

DROP TABLE IF EXISTS `suppliers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `suppliers` (
  `SupplierID` varchar(10) NOT NULL,
  `SupplierName` varchar(100) NOT NULL,
  `ContactPerson` varchar(100) DEFAULT NULL,
  `Phone` varchar(20) DEFAULT NULL,
  `Email` varchar(100) DEFAULT NULL,
  `City` varchar(50) DEFAULT NULL,
  `State` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`SupplierID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `suppliers`
--

LOCK TABLES `suppliers` WRITE;
/*!40000 ALTER TABLE `suppliers` DISABLE KEYS */;
INSERT INTO `suppliers` VALUES ('SUP001','Ramraj Cotton','Arun Kumar','9876543201','sup001@retailai.com','Coimbatore','Tamil Nadu'),('SUP002','Raymond','Vijay Sharma','9876543202','sup002@retailai.com','Mumbai','Maharashtra'),('SUP003','Biba','Priya Singh','9876543203','sup003@retailai.com','New Delhi','Delhi'),('SUP004','Fabindia','Rahul Verma','9876543204','sup004@retailai.com','New Delhi','Delhi'),('SUP005','Westside','Sneha Gupta','9876543205','sup005@retailai.com','Bengaluru','Karnataka'),('SUP006','Uathayam','Murugan','9876543206','sup006@retailai.com','Erode','Tamil Nadu'),('SUP007','Prisma','Karthik','9876543207','sup007@retailai.com','Chennai','Tamil Nadu'),('SUP008','Guess','Amit Verma','9876543208','sup008@retailai.com','Hyderabad','Telangana'),('SUP009','Nandu Lungi','Suresh','9876543209','sup009@retailai.com','Salem','Tamil Nadu'),('SUP010','Peter England','Rakesh','9876543210','sup010@retailai.com','Bengaluru','Karnataka'),('SUP011','Louis Philippe','Ajay Kumar','9876543211','sup011@retailai.com','Chennai','Tamil Nadu'),('SUP012','Allen Solly','Kiran Rao','9876543212','sup012@retailai.com','Pune','Maharashtra'),('SUP013','Van Heusen','Sanjay Patel','9876543213','sup013@retailai.com','Ahmedabad','Gujarat'),('SUP014','Levi\'s','Rohan Shah','9876543214','sup014@retailai.com','Mumbai','Maharashtra'),('SUP015','Pepe Jeans','Anita Das','9876543215','sup015@retailai.com','Kolkata','West Bengal'),('SUP016','US Polo','Deepak Singh','9876543216','sup016@retailai.com','Lucknow','Uttar Pradesh'),('SUP017','Arrow','Manoj Kumar','9876543217','sup017@retailai.com','Jaipur','Rajasthan'),('SUP018','Nike','Arvind Nair','9876543218','sup018@retailai.com','Kochi','Kerala'),('SUP019','Adidas','Hari Prasad','9876543219','sup019@retailai.com','Hyderabad','Telangana'),('SUP020','Puma','Mahesh Reddy','9876543220','sup020@retailai.com','Visakhapatnam','Andhra Pradesh'),('SUP021','Campus','Ravi Teja','9876543221','sup021@retailai.com','Vijayawada','Andhra Pradesh'),('SUP022','Jockey','Vinod Menon','9876543222','sup022@retailai.com','Bengaluru','Karnataka'),('SUP023','Lux','Gopal Iyer','9876543223','sup023@retailai.com','Madurai','Tamil Nadu'),('SUP024','VIP','Balaji Kumar','9876543224','sup024@retailai.com','Tiruppur','Tamil Nadu'),('SUP025','Wildcraft','Naveen Raj','9876543225','sup025@retailai.com','Mysuru','Karnataka');
/*!40000 ALTER TABLE `suppliers` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-18 14:48:09
