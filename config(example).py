# ─────────────────────────────────────────────
#  config(example).py  —  Edit these before running:
#  NOTE: This is just an example file.
#  1. Update DB_CONFIG with your MySQL credentials
#  2. Update INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD with your Instagram credentials
#  3. Edit file name to config.py
# ─────────────────────────────────────────────

DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "your_username",          
    "password": "your_password", 
    "database": "your_database"
}

# Scraping settings
SCRAPE_DELAY_SECONDS = 5        # delay between requests (be polite)
MAX_POSTS_PER_SCRAPE = 12       # how many recent posts to fetch
MAX_COMMENTS_PER_POST = 20      # max comments to collect per post

# Flask settings
FLASK_SECRET_KEY = "change_me_to_something_random"
FLASK_DEBUG = True
FLASK_PORT = 5000

# Scheduler: auto-scrape every X hours (0 = disabled)
AUTO_SCRAPE_INTERVAL_HOURS = 6

# Instagram login (needed to scrape public profiles)
INSTAGRAM_USERNAME = "your_username"
INSTAGRAM_PASSWORD = "your_password"