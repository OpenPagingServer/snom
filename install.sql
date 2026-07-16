CREATE TABLE IF NOT EXISTS `endpoints-output-snom-push` (
  `ipv4` VARCHAR(45) NOT NULL,
  `status` ENUM('New', 'Unchecked', 'Offline', 'Online') NOT NULL DEFAULT 'Unchecked',
  `port` INT NOT NULL DEFAULT 80,
  `use_https` TINYINT(1) NOT NULL DEFAULT 0,
  `username` VARCHAR(255) NOT NULL DEFAULT '',
  `password` VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`ipv4`),
  KEY `status_idx` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
