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
CREATE DATABASE /*!32312 IF NOT EXISTS*/`hotel_booking` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `hotel_booking`;

/*Table structure for table `auth_group` */

DROP TABLE IF EXISTS `auth_group`;

CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `auth_group` */

/*Table structure for table `auth_group_permissions` */

DROP TABLE IF EXISTS `auth_group_permissions`;

CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `auth_group_permissions` */

/*Table structure for table `auth_permission` */

DROP TABLE IF EXISTS `auth_permission`;

CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `auth_permission` */

insert  into `auth_permission`(`id`,`name`,`content_type_id`,`codename`) values (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add 系统用户',6,'add_user'),(22,'Can change 系统用户',6,'change_user'),(23,'Can delete 系统用户',6,'delete_user'),(24,'Can view 系统用户',6,'view_user'),(25,'Can add 房间信息',7,'add_room'),(26,'Can change 房间信息',7,'change_room'),(27,'Can delete 房间信息',7,'delete_room'),(28,'Can view 房间信息',7,'view_room'),(29,'Can add 房间类型',8,'add_roomtype'),(30,'Can change 房间类型',8,'change_roomtype'),(31,'Can delete 房间类型',8,'delete_roomtype'),(32,'Can view 房间类型',8,'view_roomtype'),(33,'Can add 房型收藏',9,'add_favorite'),(34,'Can change 房型收藏',9,'change_favorite'),(35,'Can delete 房型收藏',9,'delete_favorite'),(36,'Can view 房型收藏',9,'view_favorite'),(37,'Can add 宾客评价',10,'add_review'),(38,'Can change 宾客评价',10,'change_review'),(39,'Can delete 宾客评价',10,'delete_review'),(40,'Can view 宾客评价',10,'view_review'),(41,'Can add 预订订单',11,'add_booking'),(42,'Can change 预订订单',11,'change_booking'),(43,'Can delete 预订订单',11,'delete_booking'),(44,'Can view 预订订单',11,'view_booking'),(45,'Can add 问题反馈',12,'add_feedback'),(46,'Can change 问题反馈',12,'change_feedback'),(47,'Can delete 问题反馈',12,'delete_feedback'),(48,'Can view 问题反馈',12,'view_feedback'),(49,'Can add AI 对话会话',14,'add_aichatsession'),(50,'Can change AI 对话会话',14,'change_aichatsession'),(51,'Can delete AI 对话会话',14,'delete_aichatsession'),(52,'Can view AI 对话会话',14,'view_aichatsession'),(53,'Can add AI 对话消息',13,'add_aichatmessage'),(54,'Can change AI 对话消息',13,'change_aichatmessage'),(55,'Can delete AI 对话消息',13,'delete_aichatmessage'),(56,'Can view AI 对话消息',13,'view_aichatmessage');

/*Table structure for table `django_admin_log` */

DROP TABLE IF EXISTS `django_admin_log`;

CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_system_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_system_user_id` FOREIGN KEY (`user_id`) REFERENCES `system_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `django_admin_log` */

/*Table structure for table `django_content_type` */

DROP TABLE IF EXISTS `django_content_type`;

CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `django_content_type` */

insert  into `django_content_type`(`id`,`app_label`,`model`) values (6,'accounts','user'),(1,'admin','logentry'),(13,'AiChat','aichatmessage'),(14,'AiChat','aichatsession'),(3,'auth','group'),(2,'auth','permission'),(4,'contenttypes','contenttype'),(12,'feedback','feedback'),(11,'rooms','booking'),(9,'rooms','favorite'),(10,'rooms','review'),(7,'rooms','room'),(8,'rooms','roomtype'),(5,'sessions','session');

/*Table structure for table `django_migrations` */

DROP TABLE IF EXISTS `django_migrations`;

CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `django_migrations` */

insert  into `django_migrations`(`id`,`app`,`name`,`applied`) values (1,'contenttypes','0001_initial','2026-06-12 01:41:57.022073'),(2,'contenttypes','0002_remove_content_type_name','2026-06-12 01:41:57.116480'),(3,'auth','0001_initial','2026-06-12 01:41:57.398617'),(4,'auth','0002_alter_permission_name_max_length','2026-06-12 01:41:57.465897'),(5,'auth','0003_alter_user_email_max_length','2026-06-12 01:41:57.470502'),(6,'auth','0004_alter_user_username_opts','2026-06-12 01:41:57.475449'),(7,'auth','0005_alter_user_last_login_null','2026-06-12 01:41:57.484253'),(8,'auth','0006_require_contenttypes_0002','2026-06-12 01:41:57.487991'),(9,'auth','0007_alter_validators_add_error_messages','2026-06-12 01:41:57.500535'),(10,'auth','0008_alter_user_username_max_length','2026-06-12 01:41:57.509296'),(11,'auth','0009_alter_user_last_name_max_length','2026-06-12 01:41:57.515090'),(12,'auth','0010_alter_group_name_max_length','2026-06-12 01:41:57.541833'),(13,'auth','0011_update_proxy_permissions','2026-06-12 01:41:57.549680'),(14,'auth','0012_alter_user_first_name_max_length','2026-06-12 01:41:57.555109'),(15,'accounts','0001_initial','2026-06-12 01:41:58.015323'),(16,'admin','0001_initial','2026-06-12 01:41:58.164214'),(17,'admin','0002_logentry_remove_auto_add','2026-06-12 01:41:58.186165'),(18,'admin','0003_logentry_add_action_flag_choices','2026-06-12 01:41:58.192631'),(19,'sessions','0001_initial','2026-06-12 01:41:58.238156'),(20,'rooms','0001_initial','2026-06-12 02:35:05.393093'),(21,'rooms','0002_booking_review_favorite','2026-06-12 05:48:32.825058'),(22,'rooms','0003_booking_contact_name_booking_contact_phone_and_more','2026-06-12 06:22:22.378307'),(23,'feedback','0001_initial','2026-06-12 08:11:41.394576'),(24,'AiChat','0001_initial','2026-06-29 02:39:45.693590'),(25,'accounts','0002_user_avatar','2026-06-29 03:15:37.783716');

/*Table structure for table `django_session` */

DROP TABLE IF EXISTS `django_session`;

CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `django_session` */

/*Table structure for table `system_user` */

DROP TABLE IF EXISTS `system_user`;

CREATE TABLE `system_user` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `username` varchar(150) NOT NULL COMMENT '用户名',
  `password` varchar(128) NOT NULL COMMENT '密码哈希值',
  `first_name` varchar(150) NOT NULL COMMENT '名',
  `last_name` varchar(150) NOT NULL COMMENT '姓',
  `email` varchar(254) NOT NULL COMMENT '邮箱',
  `mobile` varchar(11) NOT NULL COMMENT '手机号',
  `role` varchar(20) NOT NULL COMMENT '用户角色',
  `is_staff` tinyint(1) NOT NULL COMMENT '员工状态',
  `is_active` tinyint(1) NOT NULL COMMENT '启用状态',
  `last_login` datetime(6) DEFAULT NULL COMMENT '最后登录时间',
  `date_joined` datetime(6) NOT NULL COMMENT '注册时间',
  `is_superuser` tinyint(1) NOT NULL COMMENT '超级管理员状态',
  `avatar` varchar(100) NOT NULL COMMENT '用户头像文件路径',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `mobile` (`mobile`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统用户';

/*Data for the table `system_user` */

insert  into `system_user`(`id`,`username`,`password`,`first_name`,`last_name`,`email`,`mobile`,`role`,`is_staff`,`is_active`,`last_login`,`date_joined`,`is_superuser`,`avatar`) values (1,'admin','pbkdf2_sha256$600000$cOKyjOQGu05U9WZOb34r3C$f6ImFlpNlAvtkpv7EBdMn+fCrBbGivFlQneLNbbNcZI=','三','张','','15666666666','admin',0,1,NULL,'2026-06-12 02:30:18.363652',0,'avatars/2026/06/test.png'),(2,'royaluser','pbkdf2_sha256$1200000$eOgANd1DPa0ruQIGPTApAO$8J/eddMK057sWeNRzifb+OJtxHKglpbXfwRX4WvSoqI=','','','','13812345678','user',0,1,NULL,'2026-06-12 02:58:41.308947',0,''),(3,'luxury_guest','pbkdf2_sha256$1000000$cOvuXTeSWMtddvwvjRVar8$ttrK2HUj1sL/YQECZ2B0/3aYwqQfZeVXiN3etr/Eeds=','','','','13800000000','user',0,1,NULL,'2026-06-12 03:32:45.177360',0,''),(4,'normal_guest','pbkdf2_sha256$1000000$yzQa2xwZO4uGIDvXTYn38L$QhMeSvcigoubg187wueQnP7yxUPiyPPScuJ5EJOOB3c=','','','','13900139000','user',0,1,NULL,'2026-06-12 06:34:32.120239',0,'');

/*Table structure for table `system_user_groups` */

DROP TABLE IF EXISTS `system_user_groups`;

CREATE TABLE `system_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `system_user_groups_user_id_group_id_33e2ef7b_uniq` (`user_id`,`group_id`),
  KEY `system_user_groups_group_id_925e6bcb_fk_auth_group_id` (`group_id`),
  CONSTRAINT `system_user_groups_group_id_925e6bcb_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `system_user_groups_user_id_8e766c0f_fk_system_user_id` FOREIGN KEY (`user_id`) REFERENCES `system_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `system_user_groups` */

/*Table structure for table `system_user_user_permissions` */

DROP TABLE IF EXISTS `system_user_user_permissions`;

CREATE TABLE `system_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `system_user_user_permissions_user_id_permission_id_2c3e5fa1_uniq` (`user_id`,`permission_id`),
  KEY `system_user_user_per_permission_id_9339fa91_fk_auth_perm` (`permission_id`),
  CONSTRAINT `system_user_user_per_permission_id_9339fa91_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `system_user_user_permissions_user_id_0c39fdf8_fk_system_user_id` FOREIGN KEY (`user_id`) REFERENCES `system_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `system_user_user_permissions` */

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
