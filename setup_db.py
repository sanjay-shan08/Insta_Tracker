"""
setup_db.py — Run this ONCE before starting the app.

Creates the MySQL database and all required tables.

Usage:
    python setup_db.py
"""

import mysql.connector
from mysql.connector import Error
import os

# Read config without importing full config (avoids import errors before install)
try:
    from config import DB_CONFIG
except ImportError:
    print("❌ Could not import config.py. Make sure you're in the instagram_tracker/ directory.")
    exit(1)

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "db", "schema.sql")

def run_setup():
    print("=" * 50)
    print("  InstaTrack — Database Setup")
    print("=" * 50)

    # 1. Connect WITHOUT specifying the database (it might not exist yet)
    init_config = {k: v for k, v in DB_CONFIG.items() if k != "database"}

    try:
        conn = mysql.connector.connect(**init_config)
        cursor = conn.cursor()
        print(f"✅ Connected to MySQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    except Error as e:
        print(f"❌ Could not connect to MySQL: {e}")
        print("\nCheck your credentials in config.py:")
        print(f"  host:     {DB_CONFIG['host']}")
        print(f"  port:     {DB_CONFIG['port']}")
        print(f"  user:     {DB_CONFIG['user']}")
        print(f"  password: {'*' * len(str(DB_CONFIG['password']))}")
        return False

    # 2. Create database
    db_name = DB_CONFIG["database"]
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.execute(f"USE `{db_name}`;")
        print(f"✅ Database '{db_name}' ready.")
    except Error as e:
        print(f"❌ Failed to create database: {e}")
        return False

    # 3. Read and run schema.sql
    try:
        with open(SCHEMA_PATH, "r") as f:
            sql = f.read()

        # Split on semicolons, skip USE/CREATE DATABASE lines (already handled)
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        created = 0
        for stmt in statements:
            # Skip the database-level statements we already ran
            upper = stmt.upper()
            if upper.startswith("CREATE DATABASE") or upper.startswith("USE "):
                continue
            try:
                cursor.execute(stmt)
                if "CREATE TABLE" in upper:
                    # Extract table name for logging
                    parts = stmt.split()
                    tbl = parts[5] if len(parts) > 5 else "?"
                    print(f"   ✔ Table {tbl} created.")
                    created += 1
            except Error as e:
                if e.errno == 1050:  # Table already exists
                    pass
                else:
                    print(f"   ⚠ Warning on statement: {e}")

        conn.commit()
        print(f"\n✅ Schema applied — {created} table(s) created (or already existed).")
    except FileNotFoundError:
        print(f"❌ schema.sql not found at: {SCHEMA_PATH}")
        return False
    except Error as e:
        print(f"❌ Schema error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

    # 4. Verify tables
    try:
        verify_conn = mysql.connector.connect(**DB_CONFIG)
        v_cursor = verify_conn.cursor()
        v_cursor.execute("SHOW TABLES;")
        tables = [row[0] for row in v_cursor.fetchall()]
        v_cursor.close()
        verify_conn.close()

        expected = {"accounts", "snapshots", "posts", "post_stats", "comments", "followers"}
        missing = expected - set(tables)
        if missing:
            print(f"⚠️  Missing tables: {missing}")
        else:
            print(f"✅ All tables verified: {', '.join(sorted(tables))}")
    except Error as e:
        print(f"⚠️  Could not verify tables: {e}")

    print("\n" + "=" * 50)
    print("  Setup complete! You can now run:")
    print("      python app.py")
    print("  Then open: http://localhost:5000")
    print("=" * 50 + "\n")
    return True


if __name__ == "__main__":
    run_setup()
