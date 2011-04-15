ALTER TABLE `work_testrun` ADD COLUMN `url` varchar(255) NOT NULL;
ALTER TABLE `system_testsuite` CHANGE COLUMN `url` `default_url` varchar(255) NOT NULL;
