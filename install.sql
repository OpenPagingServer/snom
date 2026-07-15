CREATE TABLE IF NOT EXISTS `endpoints-output-snom` (
  `macaddr` VARCHAR(64) NOT NULL,
  `name` VARCHAR(255) DEFAULT '',
  `ipv4` VARCHAR(45) DEFAULT '',
  `http_username` VARCHAR(255) DEFAULT 'admin',
  `http_password` VARCHAR(255) DEFAULT '',
  `status` ENUM('New', 'Unchecked', 'Offline', 'Online') NOT NULL DEFAULT 'Unchecked',
  `audio` ENUM('Multicast', 'Unicast', 'Disabled') NOT NULL DEFAULT 'Multicast',
  `model` VARCHAR(32) NOT NULL DEFAULT 'D785',
  `visual` ENUM('None', 'Text', 'Image') NOT NULL DEFAULT 'Image',
  `volume` ENUM('0', '10', '20', '30', '40', '50', '60', '70', '80', '90', '100', 'asis') NOT NULL DEFAULT 'asis',
  PRIMARY KEY (`macaddr`),
  KEY `ipv4_idx` (`ipv4`),
  KEY `status_idx` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `endpoints-modulesettings-snom` (
  `parameter` VARCHAR(128) NOT NULL,
  `value` TEXT,
  PRIMARY KEY (`parameter`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
