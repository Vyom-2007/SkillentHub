-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Feb 09, 2026 at 04:07 AM
-- Server version: 8.4.7
-- PHP Version: 8.3.28

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `skillenthub`
--

-- --------------------------------------------------------

--
-- Table structure for table `applications`
--

DROP TABLE IF EXISTS `applications`;
CREATE TABLE IF NOT EXISTS `applications` (
  `application_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `item_type` enum('job','internship','competition','hackathon') COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_id` int NOT NULL,
  `resume_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cover_letter` text COLLATE utf8mb4_unicode_ci,
  `status` enum('applied','reviewing','shortlisted','rejected','accepted') COLLATE utf8mb4_unicode_ci DEFAULT 'applied',
  `applied_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `team_id` int DEFAULT NULL,
  PRIMARY KEY (`application_id`),
  KEY `idx_user_item_status` (`user_id`,`item_type`,`status`),
  KEY `idx_item_type_id` (`item_type`,`item_id`),
  KEY `idx_status` (`status`),
  KEY `idx_applications_user` (`user_id`,`item_type`,`status`),
  KEY `idx_applications_item` (`item_type`,`item_id`),
  KEY `fk_applications_team` (`team_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `comments`
--

DROP TABLE IF EXISTS `comments`;
CREATE TABLE IF NOT EXISTS `comments` (
  `comment_id` int NOT NULL AUTO_INCREMENT,
  `post_id` int NOT NULL,
  `user_id` int NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`comment_id`),
  KEY `idx_post_id` (`post_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_post_created` (`post_id`,`created_at`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `competitions`
--

DROP TABLE IF EXISTS `competitions`;
CREATE TABLE IF NOT EXISTS `competitions` (
  `competition_id` int NOT NULL AUTO_INCREMENT,
  `recruiter_id` int DEFAULT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `rules` text COLLATE utf8mb4_unicode_ci,
  `start_date` timestamp NOT NULL,
  `end_date` timestamp NOT NULL,
  `prize` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `max_participants` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`competition_id`),
  KEY `idx_recruiter_id` (`recruiter_id`),
  KEY `idx_active_start` (`is_active`,`start_date`),
  KEY `idx_start_end` (`start_date`,`end_date`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `competition_registrations`
--

DROP TABLE IF EXISTS `competition_registrations`;
CREATE TABLE IF NOT EXISTS `competition_registrations` (
  `registration_id` int NOT NULL AUTO_INCREMENT,
  `competition_id` int NOT NULL,
  `user_id` int NOT NULL,
  `registered_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`registration_id`),
  UNIQUE KEY `unique_registration` (`competition_id`,`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `connections`
--

DROP TABLE IF EXISTS `connections`;
CREATE TABLE IF NOT EXISTS `connections` (
  `connection_id` int NOT NULL AUTO_INCREMENT,
  `user_id_1` int NOT NULL,
  `user_id_2` int NOT NULL,
  `status` enum('pending','accepted','rejected') COLLATE utf8mb4_unicode_ci NOT NULL,
  `requested_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `responded_at` timestamp NULL DEFAULT NULL,
  `created_by` int NOT NULL,
  PRIMARY KEY (`connection_id`),
  KEY `fk_connections_user1` (`user_id_1`),
  KEY `fk_connections_user2` (`user_id_2`),
  KEY `fk_connections_created_by` (`created_by`)
) ;

-- --------------------------------------------------------

--
-- Table structure for table `education`
--

DROP TABLE IF EXISTS `education`;
CREATE TABLE IF NOT EXISTS `education` (
  `education_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `institution_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `degree` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `field_of_study` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `start_year` int DEFAULT NULL,
  `end_year` int DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`education_id`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `education`
--

INSERT INTO `education` (`education_id`, `user_id`, `institution_name`, `degree`, `field_of_study`, `start_year`, `end_year`, `description`, `created_at`) VALUES
(10, 1, 'LJ', 'B.Tech', 'CSE', 2024, 2028, NULL, '2026-02-08 23:49:05');

-- --------------------------------------------------------

--
-- Table structure for table `experience`
--

DROP TABLE IF EXISTS `experience`;
CREATE TABLE IF NOT EXISTS `experience` (
  `experience_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `company_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `position` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `location` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `is_current` tinyint(1) DEFAULT '0',
  `description` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`experience_id`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `hackathons`
--

DROP TABLE IF EXISTS `hackathons`;
CREATE TABLE IF NOT EXISTS `hackathons` (
  `hackathon_id` int NOT NULL AUTO_INCREMENT,
  `recruiter_id` int DEFAULT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `theme` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `start_date` timestamp NOT NULL,
  `end_date` timestamp NOT NULL,
  `venue` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `mode` enum('online','offline','hybrid') COLLATE utf8mb4_unicode_ci NOT NULL,
  `team_size` int DEFAULT NULL,
  `prizes` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`hackathon_id`),
  KEY `idx_recruiter_id` (`recruiter_id`),
  KEY `idx_mode` (`mode`),
  KEY `idx_active_start` (`is_active`,`start_date`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `hackathon_registrations`
--

DROP TABLE IF EXISTS `hackathon_registrations`;
CREATE TABLE IF NOT EXISTS `hackathon_registrations` (
  `registration_id` int NOT NULL AUTO_INCREMENT,
  `hackathon_id` int NOT NULL,
  `user_id` int NOT NULL,
  `team_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `registered_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`registration_id`),
  UNIQUE KEY `unique_registration` (`hackathon_id`,`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `internships`
--

DROP TABLE IF EXISTS `internships`;
CREATE TABLE IF NOT EXISTS `internships` (
  `internship_id` int NOT NULL AUTO_INCREMENT,
  `recruiter_id` int NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `location` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `duration` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `stipend` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `work_mode` enum('on-site','remote','hybrid') COLLATE utf8mb4_unicode_ci DEFAULT 'on-site',
  `certificate_provided` tinyint(1) DEFAULT '0',
  `skills_required` text COLLATE utf8mb4_unicode_ci,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `requirements` text COLLATE utf8mb4_unicode_ci,
  `posted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `deadline` date DEFAULT NULL,
  `status` enum('active','inactive','expired') COLLATE utf8mb4_unicode_ci DEFAULT 'active',
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`internship_id`),
  KEY `idx_recruiter_id` (`recruiter_id`),
  KEY `idx_status_posted` (`status`,`posted_at`),
  KEY `idx_internships_status` (`status`,`posted_at`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `jobs`
--

DROP TABLE IF EXISTS `jobs`;
CREATE TABLE IF NOT EXISTS `jobs` (
  `job_id` int NOT NULL AUTO_INCREMENT,
  `recruiter_id` int NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `location` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `job_type` enum('full-time','part-time','contract') COLLATE utf8mb4_unicode_ci NOT NULL,
  `work_mode` enum('on-site','remote','hybrid') COLLATE utf8mb4_unicode_ci DEFAULT 'on-site',
  `experience_required` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `skills_required` text COLLATE utf8mb4_unicode_ci,
  `salary_range` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `requirements` text COLLATE utf8mb4_unicode_ci,
  `posted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `deadline` date DEFAULT NULL,
  `number_of_openings` int DEFAULT '1',
  `status` enum('active','inactive','expired') COLLATE utf8mb4_unicode_ci DEFAULT 'active',
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`job_id`),
  KEY `idx_recruiter_id` (`recruiter_id`),
  KEY `idx_status_posted` (`status`,`posted_at`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_jobs_status` (`status`,`posted_at`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `messages`
--

DROP TABLE IF EXISTS `messages`;
CREATE TABLE IF NOT EXISTS `messages` (
  `message_id` int NOT NULL AUTO_INCREMENT,
  `sender_id` int NOT NULL,
  `receiver_id` int NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_read` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`message_id`),
  KEY `idx_sender_receiver_created` (`sender_id`,`receiver_id`,`created_at`),
  KEY `idx_receiver_read` (`receiver_id`,`is_read`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_messages_conversation` (`sender_id`,`receiver_id`,`created_at`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `messages`
--

INSERT INTO `messages` (`message_id`, `sender_id`, `receiver_id`, `content`, `is_read`, `created_at`) VALUES
(1, 1, 2, 'Hii', 0, '2026-02-08 18:42:16'),
(2, 1, 2, 'Hello', 0, '2026-02-08 18:42:27');

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
CREATE TABLE IF NOT EXISTS `notifications` (
  `notification_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `type` enum('post_like','post_comment','new_message','application_update','connection_request','connection_accepted','team_invitation','team_invitation_accepted','team_invitation_rejected') COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `related_id` int DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`notification_id`),
  KEY `idx_user_read_created` (`user_id`,`is_read`,`created_at`),
  KEY `idx_type` (`type`),
  KEY `idx_notifications_user_unread` (`user_id`,`is_read`,`created_at`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `password_reset_otps`
--

DROP TABLE IF EXISTS `password_reset_otps`;
CREATE TABLE IF NOT EXISTS `password_reset_otps` (
  `otp_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `otp` varchar(6) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` timestamp NOT NULL,
  `is_verified` tinyint(1) DEFAULT '0',
  `is_used` tinyint(1) DEFAULT '0',
  `attempts` int DEFAULT '0',
  PRIMARY KEY (`otp_id`),
  KEY `fk_password_reset_otps_user` (`user_id`),
  KEY `idx_email_otp_used_expiry` (`email`,`otp`,`is_used`,`expires_at`),
  KEY `idx_expires_at` (`expires_at`),
  KEY `idx_otp_lookup` (`email`,`otp`,`is_used`,`expires_at`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `password_reset_otps`
--

INSERT INTO `password_reset_otps` (`otp_id`, `user_id`, `email`, `otp`, `created_at`, `expires_at`, `is_verified`, `is_used`, `attempts`) VALUES
(1, 1, 'vyomfinaviya21@gmail.com', '535213', '2026-02-08 17:11:10', '2026-02-08 17:16:11', 1, 1, 1),
(2, 1, 'vyomfinaviya21@gmail.com', '052004', '2026-02-08 17:17:47', '2026-02-08 17:22:48', 1, 1, 1),
(3, 1, 'vyomfinaviya21@gmail.com', '970164', '2026-02-08 17:22:40', '2026-02-08 17:27:40', 0, 0, 0),
(4, 2, 'vyomfinaviya@gmail.com', '001961', '2026-02-08 17:24:09', '2026-02-08 17:29:10', 1, 1, 1);

-- --------------------------------------------------------

--
-- Table structure for table `posts`
--

DROP TABLE IF EXISTS `posts`;
CREATE TABLE IF NOT EXISTS `posts` (
  `post_id` int NOT NULL AUTO_INCREMENT,
  `author_id` int NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `likes_count` int DEFAULT '0',
  PRIMARY KEY (`post_id`),
  KEY `idx_author_id` (`author_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_author_created` (`author_id`,`created_at`),
  KEY `idx_posts_created` (`created_at`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `posts`
--

INSERT INTO `posts` (`post_id`, `author_id`, `content`, `image_path`, `created_at`, `updated_at`, `likes_count`) VALUES
(1, 1, 'Hii how are you', 'post_c85066daf8d9.png', '2026-02-08 18:22:01', '2026-02-08 18:24:03', 2),
(2, 2, 'Hello I am Fine', 'post_1ba7d4ecc9f4.png', '2026-02-08 18:23:03', '2026-02-08 18:24:04', 2);

-- --------------------------------------------------------

--
-- Table structure for table `post_comments`
--

DROP TABLE IF EXISTS `post_comments`;
CREATE TABLE IF NOT EXISTS `post_comments` (
  `comment_id` int NOT NULL AUTO_INCREMENT,
  `post_id` int NOT NULL,
  `user_id` int NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`comment_id`),
  KEY `idx_post_id` (`post_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `post_comments`
--

INSERT INTO `post_comments` (`comment_id`, `post_id`, `user_id`, `content`, `created_at`) VALUES
(1, 2, 2, 'Good', '2026-02-08 23:53:28'),
(2, 1, 2, 'Nice', '2026-02-08 23:53:39');

-- --------------------------------------------------------

--
-- Table structure for table `post_likes`
--

DROP TABLE IF EXISTS `post_likes`;
CREATE TABLE IF NOT EXISTS `post_likes` (
  `like_id` int NOT NULL AUTO_INCREMENT,
  `post_id` int NOT NULL,
  `user_id` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`like_id`),
  UNIQUE KEY `idx_post_user_unique` (`post_id`,`user_id`),
  KEY `idx_post_id` (`post_id`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `post_likes`
--

INSERT INTO `post_likes` (`like_id`, `post_id`, `user_id`, `created_at`) VALUES
(1, 2, 2, '2026-02-08 18:23:23'),
(2, 1, 2, '2026-02-08 18:23:31'),
(3, 1, 1, '2026-02-08 18:24:03'),
(4, 2, 1, '2026-02-08 18:24:04');

-- --------------------------------------------------------

--
-- Table structure for table `post_tags`
--

DROP TABLE IF EXISTS `post_tags`;
CREATE TABLE IF NOT EXISTS `post_tags` (
  `post_id` int NOT NULL,
  `tag_id` int NOT NULL,
  PRIMARY KEY (`post_id`,`tag_id`),
  KEY `fk_post_tags_tag` (`tag_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `profiles`
--

DROP TABLE IF EXISTS `profiles`;
CREATE TABLE IF NOT EXISTS `profiles` (
  `profile_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `full_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `headline` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bio` text COLLATE utf8mb4_unicode_ci,
  `profile_picture` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `location` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `visibility` enum('public','registered_only') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'public',
  `show_email` tinyint(1) NOT NULL DEFAULT '1',
  `show_phone` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`profile_id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `idx_full_name` (`full_name`(250)),
  KEY `idx_location` (`location`(250))
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `profiles`
--

INSERT INTO `profiles` (`profile_id`, `user_id`, `full_name`, `headline`, `bio`, `profile_picture`, `location`, `phone`, `updated_at`, `visibility`, `show_email`, `show_phone`) VALUES
(1, 2, 'Vyom21', 'Software Engineer', '', 'profile_2_ba1598ce.png', '', '', '2026-02-08 17:48:08', 'public', 1, 0),
(2, 1, 'Vyom Finaviya', 'Student', 'Student', 'profile_1_5a871d7c.png', 'India', '1234567890', '2026-02-08 19:21:02', 'public', 1, 1);

-- --------------------------------------------------------

--
-- Table structure for table `profile_visits`
--

DROP TABLE IF EXISTS `profile_visits`;
CREATE TABLE IF NOT EXISTS `profile_visits` (
  `visit_id` int NOT NULL AUTO_INCREMENT,
  `profile_user_id` int NOT NULL,
  `visitor_user_id` int DEFAULT NULL,
  `visitor_recruiter_id` int DEFAULT NULL,
  `visited_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`visit_id`),
  KEY `idx_profile_user` (`profile_user_id`),
  KEY `idx_visited_at` (`visited_at` DESC)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `profile_visits`
--

INSERT INTO `profile_visits` (`visit_id`, `profile_user_id`, `visitor_user_id`, `visitor_recruiter_id`, `visited_at`) VALUES
(1, 1, 2, NULL, '2026-02-08 23:52:33'),
(2, 2, 1, NULL, '2026-02-09 00:05:47');

-- --------------------------------------------------------

--
-- Table structure for table `recruiters`
--

DROP TABLE IF EXISTS `recruiters`;
CREATE TABLE IF NOT EXISTS `recruiters` (
  `recruiter_id` int NOT NULL AUTO_INCREMENT,
  `company_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `company_email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login` timestamp NULL DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`recruiter_id`),
  UNIQUE KEY `company_email` (`company_email`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `skills`
--

DROP TABLE IF EXISTS `skills`;
CREATE TABLE IF NOT EXISTS `skills` (
  `skill_id` int NOT NULL AUTO_INCREMENT,
  `skill_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`skill_id`),
  UNIQUE KEY `skill_name` (`skill_name`)
) ENGINE=MyISAM AUTO_INCREMENT=51 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `skills`
--

INSERT INTO `skills` (`skill_id`, `skill_name`) VALUES
(1, 'Python'),
(2, 'JavaScript'),
(3, 'TypeScript'),
(4, 'React'),
(5, 'Angular'),
(6, 'Vue.js'),
(7, 'Node.js'),
(8, 'Flask'),
(9, 'Django'),
(10, 'FastAPI'),
(11, 'Java'),
(12, 'C++'),
(13, 'C#'),
(14, 'Go'),
(15, 'Rust'),
(16, 'SQL'),
(17, 'MongoDB'),
(18, 'PostgreSQL'),
(19, 'MySQL'),
(20, 'Redis'),
(21, 'AWS'),
(22, 'Azure'),
(23, 'Google Cloud'),
(24, 'Docker'),
(25, 'Kubernetes'),
(26, 'Git'),
(27, 'Linux'),
(28, 'Machine Learning'),
(29, 'Deep Learning'),
(30, 'Data Science'),
(31, 'TensorFlow'),
(32, 'PyTorch'),
(33, 'NLP'),
(34, 'Computer Vision'),
(35, 'HTML/CSS'),
(36, 'Bootstrap'),
(37, 'Tailwind CSS'),
(38, 'REST API'),
(39, 'GraphQL'),
(40, 'Microservices'),
(41, 'CI/CD'),
(42, 'Agile'),
(43, 'Scrum'),
(44, 'Project Management'),
(45, 'UI/UX Design'),
(46, 'Figma'),
(47, 'Adobe XD'),
(48, 'Communication'),
(49, 'Problem Solving'),
(50, 'Leadership');

-- --------------------------------------------------------

--
-- Table structure for table `tags`
--

DROP TABLE IF EXISTS `tags`;
CREATE TABLE IF NOT EXISTS `tags` (
  `tag_id` int NOT NULL AUTO_INCREMENT,
  `tag_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`tag_id`),
  UNIQUE KEY `tag_name` (`tag_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `teams`
--

DROP TABLE IF EXISTS `teams`;
CREATE TABLE IF NOT EXISTS `teams` (
  `team_id` int NOT NULL AUTO_INCREMENT,
  `team_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_type` enum('competition','hackathon') COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_id` int NOT NULL,
  `created_by` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `max_members` int DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`team_id`),
  KEY `idx_team_event` (`item_type`,`item_id`),
  KEY `idx_team_creator` (`created_by`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `team_invitations`
--

DROP TABLE IF EXISTS `team_invitations`;
CREATE TABLE IF NOT EXISTS `team_invitations` (
  `invitation_id` int NOT NULL AUTO_INCREMENT,
  `team_id` int NOT NULL,
  `invited_user_id` int NOT NULL,
  `invited_by` int NOT NULL,
  `status` enum('pending','accepted','rejected') COLLATE utf8mb4_unicode_ci NOT NULL,
  `invited_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `responded_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`invitation_id`),
  UNIQUE KEY `idx_team_invitation_unique` (`team_id`,`invited_user_id`),
  KEY `idx_pending_invitations` (`invited_user_id`,`status`),
  KEY `idx_team_invitations` (`team_id`,`status`),
  KEY `fk_team_invitations_invited_by` (`invited_by`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `team_members`
--

DROP TABLE IF EXISTS `team_members`;
CREATE TABLE IF NOT EXISTS `team_members` (
  `member_id` int NOT NULL AUTO_INCREMENT,
  `team_id` int NOT NULL,
  `user_id` int NOT NULL,
  `role` enum('leader','member') COLLATE utf8mb4_unicode_ci NOT NULL,
  `joined_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`member_id`),
  UNIQUE KEY `idx_team_user_unique` (`team_id`,`user_id`),
  KEY `idx_user_teams` (`user_id`),
  KEY `idx_team_members_list` (`team_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login` timestamp NULL DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `email`, `password_hash`, `created_at`, `last_login`, `is_active`) VALUES
(1, 'vyomfinaviya21@gmail.com', '$2b$12$EJcUXOTXg/E0SrDKNVh9e.7A734atRbW7TUwzlp07LyzYSQQNeOJy', '2026-02-07 15:08:51', '2026-02-09 03:28:28', 1),
(2, 'vyomfinaviya@gmail.com', '$2b$12$fQTDxBtys9v9d8e1qMcv5.8NThsfpk9h9Mvam6zGgrAkiNr2B1uSC', '2026-02-08 17:13:06', '2026-02-08 18:22:27', 1);

-- --------------------------------------------------------

--
-- Table structure for table `user_skills`
--

DROP TABLE IF EXISTS `user_skills`;
CREATE TABLE IF NOT EXISTS `user_skills` (
  `user_id` int NOT NULL,
  `skill_id` int NOT NULL,
  `proficiency_level` enum('beginner','intermediate','advanced') COLLATE utf8mb4_unicode_ci DEFAULT 'intermediate',
  PRIMARY KEY (`user_id`,`skill_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_skill_id` (`skill_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `user_skills`
--

INSERT INTO `user_skills` (`user_id`, `skill_id`, `proficiency_level`) VALUES
(1, 47, 'intermediate'),
(1, 42, 'intermediate'),
(1, 2, 'intermediate');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
