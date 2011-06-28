-- phpMyAdmin SQL Dump
-- version 3.4.2deb1
-- http://www.phpmyadmin.net
--
-- Хост: localhost
-- Время создания: Июн 28 2011 г., 22:45
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
-- Дамп данных таблицы `transport`
--

INSERT INTO `transport` (`domain`, `transport`) VALUES
('testtop.loc', 'virtual:');

--
-- Дамп данных таблицы `users`
--

INSERT INTO `users` (`id`, `user`, `address`, `crypt`, `clear`, `name`, `uid`, `gid`, `home`, `domain`, `maildir`, `imapok`, `bool1`, `bool2`) VALUES
(1, 'test', 'test@testtop.loc', 'Om1Avk7Z2pBL.', '123', 'Test tester', 114, 125, '/var/mail/postfix/', 'testtop.loc', 'testtop.loc/test/', 1, 1, 1);

--
-- Дамп данных таблицы `white_list_addr`
--

INSERT INTO `white_list_addr` (`id_wl_arrd`, `mx_addr`, `accept`) VALUES
(1, '192.168.0.1', 'OK'),
(2, '213.141.136.65', 'OK');

--
-- Дамп данных таблицы `white_list_dns`
--

INSERT INTO `white_list_dns` (`id_wl_dns`, `dns`, `accept`) VALUES
(1, 'mail.ru', 'OK'),
(2, 'auditory.ru', 'OK');

--
-- Дамп данных таблицы `white_list_mail`
--

INSERT INTO `white_list_mail` (`id_wl_mail`, `user_id`, `mail`, `accept`) VALUES
(1, 1, 'root@router.loc', 'OK'),
(2, 1, 'admin@klan-hub.ru', 'OK'),
(8, 1, 'cs@klan-hub.ru', 'OK');

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
