"""
scheduler.py — Background auto-scraper

Runs as a separate process alongside app.py.
Every N hours (set in config.py), it re-scrapes all tracked accounts.

Usage:
    python scheduler.py
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from config import AUTO_SCRAPE_INTERVAL_HOURS
from tracker import run_scrape
from db import queries

scheduler = BlockingScheduler(timezone="UTC")

def scrape_all_accounts():
    print(f"\n[{datetime.now()}] ⏰ Auto-scrape started...")
    accounts = queries.get_all_accounts() or []

    if not accounts:
        print("  No accounts to scrape.")
        return

    for acc in accounts:
        username = acc["username"]
        print(f"  → Scraping @{username}...")
        result = run_scrape(username)
        if result["success"]:
            print(f"    ✅ @{username}: {result['followers']:,} followers, {result['posts_saved']} posts saved.")
        else:
            print(f"    ❌ @{username} failed: {result['error']}")

    print(f"[{datetime.now()}] Auto-scrape complete.\n")


if AUTO_SCRAPE_INTERVAL_HOURS > 0:
    scheduler.add_job(
        scrape_all_accounts,
        trigger=IntervalTrigger(hours=AUTO_SCRAPE_INTERVAL_HOURS),
        id="auto_scrape",
        name="Auto-scrape all tracked accounts",
        replace_existing=True
    )
    print(f"✅ Scheduler started — auto-scraping every {AUTO_SCRAPE_INTERVAL_HOURS} hour(s).")
    print("   Press Ctrl+C to stop.\n")
    scrape_all_accounts()  # Run once immediately on startup
    scheduler.start()
else:
    print("⚠️  AUTO_SCRAPE_INTERVAL_HOURS is 0 in config.py — scheduler is disabled.")
    print("   Set it to a non-zero value to enable auto-scraping.")
