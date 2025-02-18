CREATE DATABASE IF NOT EXISTS toll_management_database;
USE toll_management_database;

-- Operator Table
DROP TABLE IF EXISTS operator;
CREATE TABLE operator (
    op_id VARCHAR(50) NOT NULL,
    op_name VARCHAR(50) UNIQUE,
    email VARCHAR(100) NOT NULL,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (op_id)
);

-- Toll Table
DROP TABLE IF EXISTS toll;
CREATE TABLE toll (
    toll_id VARCHAR(50) NOT NULL,
    toll_name VARCHAR(500) NOT NULL,
    op_id VARCHAR(50) NOT NULL,
    road VARCHAR(50) NOT NULL,
    latitude DECIMAL(10, 6) NOT NULL, -- Using DECIMAL for latitude
    longitude DECIMAL(10, 6) NOT NULL, -- Using DECIMAL for longitude
    PM VARCHAR(50) NOT NULL,
    price1 DECIMAL(10, 2) NOT NULL,
    price2 DECIMAL(10, 2) NOT NULL,
    price3 DECIMAL(10, 2) NOT NULL,
    price4 DECIMAL(10, 2) NOT NULL,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (toll_id),
    FOREIGN KEY (op_id) REFERENCES operator(op_id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
);

-- Tag Table
DROP TABLE IF EXISTS tag;
CREATE TABLE tag (
    tag_ref VARCHAR(50) NOT NULL,
    tag_home VARCHAR(50) NOT NULL,
    op_id VARCHAR(50) NOT NULL,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (tag_ref),
    FOREIGN KEY (op_id) REFERENCES operator(op_id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
);

-- Debt Table
DROP TABLE IF EXISTS debt;
CREATE TABLE debt (
    debt_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    debtor_id VARCHAR(50) NOT NULL,
    receiver_id VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (debt_id),
    FOREIGN KEY (debtor_id) REFERENCES operator(op_id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES operator(op_id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
    -- Removed foreign key on amount as it doesn't make sense
);

-- Pass Table
DROP TABLE IF EXISTS pass;
CREATE TABLE pass (
    pass_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    toll_id VARCHAR(50) NOT NULL,
    tag_ref VARCHAR(50) NOT NULL,
    charge DECIMAL(10, 2) NOT NULL,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `timestamp` DATETIME NOT NULL,
    PRIMARY KEY (pass_id),
    FOREIGN KEY (toll_id) REFERENCES toll(toll_id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    FOREIGN KEY (tag_ref) REFERENCES tag(tag_ref) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
);

-- User Table
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('operator', 'admin') NOT NULL,
    token VARCHAR(255) DEFAULT NULL
);



