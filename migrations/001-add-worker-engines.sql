begin;
CREATE TABLE `work_workerengine` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `worker_id` integer NOT NULL,
    `engine` varchar(50) NOT NULL,
    `version` varchar(10) NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `work_workerengine` ADD CONSTRAINT `worker_id_refs_id_e503fac9` FOREIGN KEY (`worker_id`) REFERENCES `work_worker` (`id`);
CREATE INDEX `work_workerengine_20fc5b84` ON `work_workerengine` (`worker_id`);
CREATE INDEX `work_workerengine_93906ca3` ON `work_workerengine` (`engine`);
commit;
