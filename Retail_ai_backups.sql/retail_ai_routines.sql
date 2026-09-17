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
-- Temporary view structure for view `productinventory`
--

DROP TABLE IF EXISTS `productinventory`;
/*!50001 DROP VIEW IF EXISTS `productinventory`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `productinventory` AS SELECT 
 1 AS `ProductID`,
 1 AS `ProductName`,
 1 AS `Brand`,
 1 AS `CurrentStock`,
 1 AS `InventoryStatus`,
 1 AS `ReorderPoint`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `customerpurchases`
--

DROP TABLE IF EXISTS `customerpurchases`;
/*!50001 DROP VIEW IF EXISTS `customerpurchases`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `customerpurchases` AS SELECT 
 1 AS `CustomerID`,
 1 AS `FullName`,
 1 AS `ProductName`,
 1 AS `Quantity`,
 1 AS `FinalPrice`,
 1 AS `SaleDate`*/;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `productinventory`
--

/*!50001 DROP VIEW IF EXISTS `productinventory`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `productinventory` AS select `p`.`ProductID` AS `ProductID`,`p`.`ProductName` AS `ProductName`,`p`.`Brand` AS `Brand`,`i`.`CurrentStock` AS `CurrentStock`,`i`.`InventoryStatus` AS `InventoryStatus`,`i`.`ReorderPoint` AS `ReorderPoint` from (`products` `p` join `inventory` `i` on((`p`.`ProductID` = `i`.`ProductID`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `customerpurchases`
--

/*!50001 DROP VIEW IF EXISTS `customerpurchases`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `customerpurchases` AS select `c`.`CustomerID` AS `CustomerID`,`c`.`FullName` AS `FullName`,`p`.`ProductName` AS `ProductName`,`s`.`Quantity` AS `Quantity`,`s`.`FinalPrice` AS `FinalPrice`,`s`.`SaleDate` AS `SaleDate` from ((`sales` `s` join `customers` `c` on((`s`.`CustomerID` = `c`.`CustomerID`))) join `products` `p` on((`s`.`ProductID` = `p`.`ProductID`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-18 14:48:09
