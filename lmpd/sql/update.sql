ALTER TABLE `white_list_mail` RENAME TO `white_list_users`;
ALTER TABLE `white_list_users` CHANGE `accept` `action` varchar(255) NOT NULL DEFAULT 'OK';
ALTER TABLE `white_list_users` CHANGE `id_wl_mail` `id` int(10) unsigned NOT NULL AUTO_INCREMENT;
ALTER TABLE `white_list_users` CHANGE `mail` `token` varchar(255) NOT NULL;
ALTER TABLE `white_list_users` DROP FOREIGN KEY `white_list_users_ibfk_1`;

ALTER TABLE `white_list_dns` RENAME TO `white_list_email`;
ALTER TABLE `white_list_email` CHANGE `id_wl_dns` `id` int(10) unsigned NOT NULL AUTO_INCREMENT;
ALTER TABLE `white_list_email` CHANGE `accept` `action` varchar(255) NOT NULL DEFAULT 'OK';
ALTER TABLE `white_list_email` CHANGE `dns` `token` varchar(255) NOT NULL;
ALTER TABLE `white_list_email` DROP KEY `dns`;
ALTER TABLE `white_list_email` ADD UNIQUE KEY `token` (`token`);

ALTER TABLE `white_list_addr` CHANGE `id_wl_arrd id` int(10) unsigned NOT NULL AUTO_INCREMENT;
ALTER TABLE `white_list_addr` CHANGE `accept` action varchar(255) NOT NULL DEFAULT 'OK';
ALTER TABLE `white_list_addr` CHANGE `mx_addr` `token` varchar(255) NOT NULL;
ALTER TABLE `white_list_addr` DROP KEY `mx_addr`;
ALTER TABLE `white_list_addr` ADD UNIQUE KEY `token` (`token`);
