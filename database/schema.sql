-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Feb 10, 2026 at 04:49 AM
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
CREATE DATABASE IF NOT EXISTS `skillenthub` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `skillenthub`;

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
  `team_id` int DEFAULT NULL,
  `resume_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cover_letter` text COLLATE utf8mb4_unicode_ci,
  `status` enum('applied','reviewing','rejected','accepted') COLLATE utf8mb4_unicode_ci DEFAULT 'applied',
  `applied_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`application_id`),
  KEY `idx_user_applications` (`user_id`,`item_type`,`status`),
  KEY `idx_item_applications` (`item_type`,`item_id`),
  KEY `team_id` (`team_id`)
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
  `content` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`comment_id`),
  KEY `post_id` (`post_id`),
  KEY `user_id` (`user_id`)
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
  `prize` text COLLATE utf8mb4_unicode_ci,
  `max_participants` int DEFAULT NULL,
  `registration_deadline` date DEFAULT NULL,
  `posted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('upcoming','ongoing','completed') COLLATE utf8mb4_unicode_ci DEFAULT 'upcoming',
  PRIMARY KEY (`competition_id`),
  KEY `idx_competitions_status` (`status`,`start_date`),
  KEY `recruiter_id` (`recruiter_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
  UNIQUE KEY `unique_connection` (`user_id_1`,`user_id_2`),
  KEY `idx_user_connections` (`user_id_1`,`status`),
  KEY `idx_pending_requests` (`user_id_2`,`status`),
  KEY `created_by` (`created_by`)
) ;

-- --------------------------------------------------------

--
-- Table structure for table `education`
--

DROP TABLE IF EXISTS `education`;
CREATE TABLE IF NOT EXISTS `education` (
  `education_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `institution` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `degree` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `field_of_study` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `start_date` date NOT NULL,
  `end_date` date DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`education_id`),
  KEY `user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
  `rules` text COLLATE utf8mb4_unicode_ci,
  `venue` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `mode` enum('online','offline','hybrid') COLLATE utf8mb4_unicode_ci NOT NULL,
  `team_size` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `theme` text COLLATE utf8mb4_unicode_ci,
  `schedule` text COLLATE utf8mb4_unicode_ci,
  `start_date` timestamp NOT NULL,
  `end_date` timestamp NOT NULL,
  `prize` text COLLATE utf8mb4_unicode_ci,
  `max_participants` int DEFAULT NULL,
  `registration_deadline` date DEFAULT NULL,
  `posted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('upcoming','ongoing','completed') COLLATE utf8mb4_unicode_ci DEFAULT 'upcoming',
  PRIMARY KEY (`hackathon_id`),
  KEY `idx_hackathons_status` (`status`,`start_date`),
  KEY `recruiter_id` (`recruiter_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
  `work_mode` enum('on-site','remote','hybrid') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `duration` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `stipend` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `certificate_provided` tinyint(1) DEFAULT '0',
  `ppo_possibility` tinyint(1) DEFAULT '0',
  `skills_required` text COLLATE utf8mb4_unicode_ci,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `requirements` text COLLATE utf8mb4_unicode_ci,
  `perks_benefits` text COLLATE utf8mb4_unicode_ci,
  `posted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `deadline` date NOT NULL,
  `number_of_openings` int DEFAULT '1',
  `status` enum('active','inactive','expired') COLLATE utf8mb4_unicode_ci DEFAULT 'active',
  PRIMARY KEY (`internship_id`),
  KEY `idx_internships_status` (`status`,`posted_at`),
  KEY `idx_internships_recruiter` (`recruiter_id`)
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
  `work_mode` enum('on-site','remote','hybrid') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `experience_required` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `skills_required` text COLLATE utf8mb4_unicode_ci,
  `salary_range` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `requirements` text COLLATE utf8mb4_unicode_ci,
  `perks_benefits` text COLLATE utf8mb4_unicode_ci,
  `posted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `deadline` date NOT NULL,
  `number_of_openings` int DEFAULT '1',
  `status` enum('active','inactive','expired') COLLATE utf8mb4_unicode_ci DEFAULT 'active',
  PRIMARY KEY (`job_id`),
  KEY `idx_jobs_status` (`status`,`posted_at`),
  KEY `idx_jobs_recruiter` (`recruiter_id`)
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
  `content` varchar(1000) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_read` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`message_id`),
  KEY `idx_messages_conversation` (`sender_id`,`receiver_id`,`created_at`),
  KEY `receiver_id` (`receiver_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
  KEY `idx_notifications_user_unread` (`user_id`,`is_read`,`created_at`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `password_reset_otps`
--

DROP TABLE IF EXISTS `password_reset_otps`;
CREATE TABLE IF NOT EXISTS `password_reset_otps` (
  `otp_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `recruiter_id` int DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `otp` varchar(6) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` timestamp NOT NULL,
  `is_verified` tinyint(1) DEFAULT '0',
  `is_used` tinyint(1) DEFAULT '0',
  `attempts` int DEFAULT '0',
  PRIMARY KEY (`otp_id`),
  KEY `user_id` (`user_id`),
  KEY `recruiter_id` (`recruiter_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `posts`
--

DROP TABLE IF EXISTS `posts`;
CREATE TABLE IF NOT EXISTS `posts` (
  `post_id` int NOT NULL AUTO_INCREMENT,
  `author_id` int NOT NULL,
  `author_type` enum('user','recruiter') COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `likes_count` int DEFAULT '0',
  PRIMARY KEY (`post_id`),
  KEY `idx_posts_created` (`created_at`),
  KEY `idx_posts_author` (`author_id`,`author_type`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
  UNIQUE KEY `unique_post_like` (`post_id`,`user_id`),
  KEY `user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `profiles`
--

DROP TABLE IF EXISTS `profiles`;
CREATE TABLE IF NOT EXISTS `profiles` (
  `profile_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `headline` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bio` text COLLATE utf8mb4_unicode_ci,
  `profile_picture` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `location` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `resume_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cover_letter_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `profile_visits_by_users` int DEFAULT '0',
  `profile_visits_by_recruiters` int DEFAULT '0',
  `profile_completion` int DEFAULT '0',
  PRIMARY KEY (`profile_id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `recruiters`
--

DROP TABLE IF EXISTS `recruiters`;
CREATE TABLE IF NOT EXISTS `recruiters` (
  `recruiter_id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `full_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login` timestamp NULL DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`recruiter_id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_recruiters_email` (`email`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `recruiter_notes`
--

DROP TABLE IF EXISTS `recruiter_notes`;
CREATE TABLE IF NOT EXISTS `recruiter_notes` (
  `note_id` int NOT NULL AUTO_INCREMENT,
  `application_id` int NOT NULL,
  `recruiter_id` int NOT NULL,
  `note_text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`note_id`),
  KEY `application_id` (`application_id`),
  KEY `recruiter_id` (`recruiter_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `recruiter_profiles`
--

DROP TABLE IF EXISTS `recruiter_profiles`;
CREATE TABLE IF NOT EXISTS `recruiter_profiles` (
  `profile_id` int NOT NULL AUTO_INCREMENT,
  `recruiter_id` int NOT NULL,
  `headline` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bio` text COLLATE utf8mb4_unicode_ci,
  `profile_picture` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `location` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`profile_id`),
  UNIQUE KEY `recruiter_id` (`recruiter_id`)
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
  UNIQUE KEY `unique_team_invitation` (`team_id`,`invited_user_id`),
  KEY `idx_pending_invitations` (`invited_user_id`,`status`),
  KEY `idx_team_invitations` (`team_id`,`status`),
  KEY `invited_by` (`invited_by`)
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
  UNIQUE KEY `unique_team_member` (`team_id`,`user_id`),
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
  `full_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login` timestamp NULL DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `user_skills`
--

DROP TABLE IF EXISTS `user_skills`;
CREATE TABLE IF NOT EXISTS `user_skills` (
  `user_id` int NOT NULL,
  `skill_id` int NOT NULL,
  `proficiency_level` enum('beginner','intermediate','advanced') COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`user_id`,`skill_id`),
  KEY `skill_id` (`skill_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
