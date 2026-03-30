CREATE DATABASE IF NOT EXISTS dsci560_wells CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE dsci560_wells;

CREATE TABLE wells (
  id INT AUTO_INCREMENT PRIMARY KEY,
  api VARCHAR(64) UNIQUE,
  well_name VARCHAR(255),
  well_number VARCHAR(64),
  address VARCHAR(255),
  city VARCHAR(128),
  county VARCHAR(128),
  state VARCHAR(64),
  zip VARCHAR(20),
  latitude DOUBLE,
  longitude DOUBLE,
  status VARCHAR(128),
  well_type VARCHAR(128),
  closest_city VARCHAR(128),
  barrels_oil DOUBLE,
  barrels_gas DOUBLE,
  raw_text LONGTEXT,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE stimulation (
  id INT AUTO_INCREMENT PRIMARY KEY,
  well_api VARCHAR(64),
  stage INT,
  fluid_vol DOUBLE,
  proppant_lbs DOUBLE,
  chemicals TEXT,
  other_fields JSON,
  FOREIGN KEY (well_api) REFERENCES wells(api) ON DELETE CASCADE
);