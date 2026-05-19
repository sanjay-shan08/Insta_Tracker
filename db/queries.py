import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None

def execute_query(query, params=None, fetch=False):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
            return result
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        print(f"[QUERY ERROR] {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

# ---------- ACCOUNTS ----------
def get_all_accounts():
    return execute_query("SELECT * FROM accounts ORDER BY added_at DESC", fetch=True)

def get_account_by_username(username):
    result = execute_query("SELECT * FROM accounts WHERE username = %s", (username,), fetch=True)
    return result[0] if result else None

def upsert_account(data):
    existing = get_account_by_username(data['username'])
    if existing:
        execute_query("""
            UPDATE accounts SET full_name=%s, bio=%s, profile_pic_url=%s,
            is_private=%s, last_scraped=NOW() WHERE username=%s
        """, (data.get('full_name'), data.get('bio'), data.get('profile_pic_url'),
              data.get('is_private', False), data['username']))
        return existing['id']
    else:
        return execute_query("""
            INSERT INTO accounts (username, full_name, bio, profile_pic_url, is_private, last_scraped)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (data['username'], data.get('full_name'), data.get('bio'),
              data.get('profile_pic_url'), data.get('is_private', False)))

def delete_account(account_id):
    execute_query("DELETE FROM accounts WHERE id=%s", (account_id,))

# ---------- SNAPSHOTS ----------
def insert_snapshot(account_id, followers, following, post_count):
    execute_query("""
        INSERT INTO snapshots (account_id, followers, following, post_count)
        VALUES (%s, %s, %s, %s)
    """, (account_id, followers, following, post_count))

def get_snapshots(account_id, limit=30):
    return execute_query("""
        SELECT * FROM snapshots WHERE account_id=%s
        ORDER BY scraped_at DESC LIMIT %s
    """, (account_id, limit), fetch=True)

# ---------- POSTS ----------
def upsert_post(account_id, post_data):
    existing = execute_query(
        "SELECT id FROM posts WHERE shortcode=%s", (post_data['shortcode'],), fetch=True)
    if existing:
        return existing[0]['id']
    return execute_query("""
        INSERT INTO posts (account_id, shortcode, caption, post_type, media_url, posted_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (account_id, post_data['shortcode'], post_data.get('caption'),
          post_data.get('post_type', 'image'), post_data.get('media_url'), post_data.get('posted_at')))

def get_posts(account_id):
    return execute_query("""
        SELECT p.*, 
               (SELECT likes FROM post_stats WHERE post_id=p.id ORDER BY scraped_at DESC LIMIT 1) as latest_likes,
               (SELECT comments_count FROM post_stats WHERE post_id=p.id ORDER BY scraped_at DESC LIMIT 1) as latest_comments
        FROM posts p WHERE p.account_id=%s ORDER BY posted_at DESC
    """, (account_id,), fetch=True)

# ---------- POST STATS ----------
def insert_post_stats(post_id, likes, comments_count, views=0):
    execute_query("""
        INSERT INTO post_stats (post_id, likes, comments_count, views)
        VALUES (%s, %s, %s, %s)
    """, (post_id, likes, comments_count, views))

# ---------- COMMENTS ----------
def insert_comment(post_id, username, text, commented_at=None):
    execute_query("""
        INSERT INTO comments (post_id, commenter_username, comment_text, commented_at)
        VALUES (%s, %s, %s, %s)
    """, (post_id, username, text, commented_at))

def get_comments(post_id):
    return execute_query("""
        SELECT * FROM comments WHERE post_id=%s ORDER BY commented_at DESC
    """, (post_id,), fetch=True)

# ---------- ANALYTICS ----------
def get_engagement_stats(account_id):
    return execute_query("""
        SELECT 
            COUNT(DISTINCT p.id) as total_posts,
            COALESCE(SUM(ps.likes), 0) as total_likes,
            COALESCE(SUM(ps.comments_count), 0) as total_comments,
            COALESCE(AVG(ps.likes), 0) as avg_likes,
            COALESCE(AVG(ps.comments_count), 0) as avg_comments
        FROM posts p
        LEFT JOIN post_stats ps ON ps.post_id = p.id
        WHERE p.account_id = %s
        AND (ps.id IS NULL OR ps.id = (
            SELECT id FROM post_stats WHERE post_id = p.id ORDER BY scraped_at DESC LIMIT 1
        ))
    """, (account_id,), fetch=True)
