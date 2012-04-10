/* Default MySQL schema for LMPD (http://flant.ru/projects/lmpd) */


SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

CREATE TABLE IF NOT EXISTS `users` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(128) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

CREATE TABLE IF NOT EXISTS `white_list_addr` (
  `id_wl_arrd` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `mx_addr` varchar(255) NOT NULL,
  `accept` varchar(255) NOT NULL DEFAULT 'OK',
  PRIMARY KEY (`id_wl_arrd`),
  UNIQUE KEY `mx_addr` (`mx_addr`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

CREATE TABLE IF NOT EXISTS `white_list_dns` (
  `id_wl_dns` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `dns` varchar(255) NOT NULL,
  `accept` varchar(255) NOT NULL DEFAULT 'OK',
  PRIMARY KEY (`id_wl_dns`),
  UNIQUE KEY `dns` (`dns`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

CREATE TABLE IF NOT EXISTS `white_list_mail` (
  `id_wl_mail` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned NOT NULL,
  `mail` varchar(255) NOT NULL,
  `accept` varchar(255) NOT NULL DEFAULT 'OK',
  PRIMARY KEY (`id_wl_mail`),
  UNIQUE (`user_id`, `mail`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
