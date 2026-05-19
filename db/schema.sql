-- Instagram Tracker Database Schema

CREATE DATABASE IF NOT EXISTS instagram_tracker;
USE instagram_tracker;

-- Tracked accounts
CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    bio TEXT,
    profile_pic_url TEXT,
    is_private BOOLEAN DEFAULT FALSE,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_scraped DATETIME
);

-- Snapshots: follower/following/post count over time
CREATE TABLE IF NOT EXISTS snapshots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    followers INT DEFAULT 0,
    following INT DEFAULT 0,
    post_count INT DEFAULT 0,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

-- Individual posts
CREATE TABLE IF NOT EXISTS posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    shortcode VARCHAR(50) UNIQUE NOT NULL,
    caption TEXT,
    post_type VARCHAR(20) DEFAULT 'image',  -- image, video, carousel
    media_url TEXT,
    posted_at DATETIME,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

-- Post stats snapshots (likes/comments can change over time)
CREATE TABLE IF NOT EXISTS post_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    likes INT DEFAULT 0,
    comments_count INT DEFAULT 0,
    views INT DEFAULT 0,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

-- Individual comments
CREATE TABLE IF NOT EXISTS comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    commenter_username VARCHAR(100),
    comment_text TEXT,
    commented_at DATETIME,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

-- Followers list snapshots
CREATE TABLE IF NOT EXISTS followers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    follower_username VARCHAR(100),
    snapshot_date DATE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);
