CREATE TABLE `system_token` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `token` longtext NOT NULL,
    `test_suite_id` integer NOT NULL,
    `active` bool NOT NULL,
    `created` datetime,
    `last_modified` datetime
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `system_token` ADD CONSTRAINT `test_suite_id_refs_id_3268f678`
    FOREIGN KEY (`test_suite_id`) REFERENCES `system_testsuite` (`id`);
CREATE INDEX `system_token_34d728db` ON `system_token` (`active`);
COMMIT;
