-- phpMyAdmin SQL Dump
-- version 3.4.2deb1
-- http://www.phpmyadmin.net
--
-- Хост: localhost
-- Время создания: Июн 28 2011 г., 22:43
-- Версия сервера: 5.1.57
-- Версия PHP: 5.3.6-12

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- База данных: `postfix`
--

--
-- Структура таблицы `users`
--

CREATE TABLE IF NOT EXISTS `white_list_users` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `address` varchar(128) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE KEY `address` (`address`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=2 ;

-- --------------------------------------------------------

--
-- Структура таблицы `white_list_addr`
--

CREATE TABLE IF NOT EXISTS `white_list_addr` (
  `id_wl_arrd` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `mx_addr` varchar(255) NOT NULL,
  `accept` varchar(255) NOT NULL DEFAULT 'OK',
  PRIMARY KEY (`id_wl_arrd`),
  UNIQUE KEY `mx_addr` (`mx_addr`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=3 ;

-- --------------------------------------------------------

--
-- Структура таблицы `white_list_dns`
--

CREATE TABLE IF NOT EXISTS `white_list_dns` (
  `id_wl_dns` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `dns` varchar(255) NOT NULL,
  `accept` varchar(255) NOT NULL DEFAULT 'OK',
  PRIMARY KEY (`id_wl_dns`),
  UNIQUE KEY `dns` (`dns`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=3 ;

-- --------------------------------------------------------

--
-- Структура таблицы `white_list_mail`
--

CREATE TABLE IF NOT EXISTS `white_list_mail` (
  `id_wl_mail` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned NOT NULL,
  `mail` varchar(255) NOT NULL,
  `accept` varchar(255) NOT NULL DEFAULT 'OK',
  PRIMARY KEY (`id_wl_mail`),
  UNIQUE (`user_id`, `mail`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=9 ;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
