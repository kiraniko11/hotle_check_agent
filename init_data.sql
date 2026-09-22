/*
SQLyog Ultimate v12.09 (64 bit)
MySQL - 8.0.26 : Database - hotel_booking
*********************************************************************
*/

/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
USE `hotel_booking`;

/*Table structure for table `room` */

DROP TABLE IF EXISTS `room`;

CREATE TABLE `room` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '房间唯一编号',
  `room_number` varchar(20) NOT NULL COMMENT '客房编号，例如305',
  `status` varchar(20) NOT NULL COMMENT '客房当前物理占用与清洁状态',
  `floor` int NOT NULL COMMENT '客房所在的物理楼层',
  `room_type_id` bigint NOT NULL COMMENT '客房所属的类型引用',
  PRIMARY KEY (`id`),
  UNIQUE KEY `room_number` (`room_number`),
  KEY `room_room_type_id_5e4ab8c6_fk_room_type_id` (`room_type_id`),
  CONSTRAINT `room_room_type_id_5e4ab8c6_fk_room_type_id` FOREIGN KEY (`room_type_id`) REFERENCES `room_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=85 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='房间信息';

/*Data for the table `room` */

insert  into `room`(`id`,`room_number`,`status`,`floor`,`room_type_id`) values (50,'201','occupied',2,13),(51,'202','vacant',2,13),(52,'203','occupied',2,13),(53,'204','vacant',2,13),(54,'205','cleaning',2,13),(55,'206','vacant',2,13),(56,'211','vacant',2,14),(57,'212','vacant',2,14),(58,'213','occupied',2,14),(59,'214','vacant',2,14),(60,'215','vacant',2,14),(61,'301','vacant',3,15),(62,'302','vacant',3,15),(63,'303','occupied',3,15),(64,'304','vacant',3,15),(65,'305','maintenance',3,15),(66,'401','vacant',4,16),(67,'402','vacant',4,16),(68,'403','vacant',4,16),(69,'404','cleaning',4,16),(70,'501','vacant',5,17),(71,'502','vacant',5,17),(72,'503','occupied',5,17),(73,'504','vacant',5,17),(74,'101','vacant',1,18),(75,'102','vacant',1,18),(76,'103','vacant',1,18),(77,'104','occupied',1,18),(78,'105','vacant',1,18),(79,'106','cleaning',1,18),(80,'601','vacant',6,19),(81,'602','vacant',6,19),(82,'603','occupied',6,19),(83,'701','vacant',7,20),(84,'702','vacant',7,20);

/*Table structure for table `room_type` */

DROP TABLE IF EXISTS `room_type`;

CREATE TABLE `room_type` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '房型唯一编号',
  `name` varchar(100) NOT NULL COMMENT '房间类型名称，例如标准大床房',
  `price` decimal(10,2) NOT NULL COMMENT '每晚房型单价',
  `capacity` int unsigned NOT NULL COMMENT '房间可入住的最大人数',
  `area` int unsigned NOT NULL COMMENT '房间的建筑面积（平方米）',
  `bed_type` varchar(100) NOT NULL COMMENT '房间的床铺配置说明',
  `window` tinyint(1) NOT NULL COMMENT '标识房间是否配备窗户',
  `breakfast` tinyint(1) NOT NULL COMMENT '标识房间是否包含免费早餐',
  `description` longtext NOT NULL COMMENT '关于房型的详细介绍说明',
  `cover_image` varchar(255) NOT NULL COMMENT '房型展示的封面图片相对路径或链接',
  `total_stock` int unsigned NOT NULL COMMENT '该房型的客房总物理库存数量',
  `remaining_stock` int unsigned NOT NULL COMMENT '当前可供预订的空闲房源数量',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  CONSTRAINT `room_type_chk_1` CHECK ((`capacity` >= 0)),
  CONSTRAINT `room_type_chk_2` CHECK ((`area` >= 0)),
  CONSTRAINT `room_type_chk_3` CHECK ((`total_stock` >= 0)),
  CONSTRAINT `room_type_chk_4` CHECK ((`remaining_stock` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='房间类型';

/*Data for the table `room_type` */

insert  into `room_type`(`id`,`name`,`price`,`capacity`,`area`,`bed_type`,`window`,`breakfast`,`description`,`cover_image`,`total_stock`,`remaining_stock`) values (13,'标准大床房','168.00',2,20,'1.5米大床',1,0,'房间干净整洁，有空调、无线网络和独立卫浴，热水随用随有，适合日常出行入住。','rooms/photo-1618773928121-c32242e63f39.avif',6,3),(14,'标准双床房','188.00',2,24,'1.2米单人床 x 2',1,0,'两张单人床，适合朋友或同事一起住，带书桌和衣柜，晚上安静不吵。','rooms/photo-1566665797739-1674de7a421a.avif',5,4),(15,'舒适大床房','218.00',2,28,'1.8米大床',1,1,'房间比标准间宽敞一些，采光好，含简单早餐，性价比不错。','rooms/photo-1590490360182-c33d57733427.avif',5,3),(16,'家庭房','258.00',3,32,'1.8米大床 + 1.2米单床',1,0,'适合一家三口住，空间够大，楼下有便利店和公交站，出行方便。','rooms/photo-1582719508461-905c673771fd.avif',4,3),(17,'商务双床房','268.00',2,30,'1.2米单人床 x 2',1,1,'带小办公桌和免费无线网络，含早餐，出差住着比较方便。','rooms/photo-1611892440504-42a792e24d32.avif',4,3),(18,'经济单人间','98.00',1,15,'1.2米单床',0,0,'面积不大但该有的都有，热水、空调、无线网齐全，适合一个人短期住宿。','rooms/photo-1631049307264-da0ec9d70304.avif',6,4),(19,'大床房（带窗）','238.00',2,26,'1.8米大床',1,0,'朝南带窗，白天光线好，床品干净，睡得踏实。','rooms/photo-1631049552240-59c37f38802b.avif',3,2),(20,'家庭套房','358.00',4,45,'两间房：1.8米大床 + 1.5米床',1,1,'两间独立的房间，适合一家人或几个朋友一起住，含简单早餐。','rooms/photo-1631049421450-348ccd7f8949.avif',2,2);

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
