-- Create database
CREATE DATABASE IF NOT EXISTS TrueColors;
USE TrueColors;

-- Create tables
CREATE TABLE IF NOT EXISTS questions (
    question_num INT(5),
    group_num INT(5),
    word_num INT(5),
    word VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS session (
    user_id VARCHAR(50),
    name VARCHAR(50),
    email VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS responses (
    user_id VARCHAR(255),
    test_id INT(5),
    question_num INT(5),
    group_num INT(5),
    score INT(1)
);

CREATE TABLE IF NOT EXISTS quiz (
    user_id VARCHAR(255),
    test_id INT(5),
    description VARCHAR(255),
    time_stamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
