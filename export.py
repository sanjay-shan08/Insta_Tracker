"""
export.py — CSV export helpers for InstaTrack

Provides functions to export account data to CSV format,
used by Flask routes in app.py.
"""

import csv
import io
from db import queries
from db.queries import execute_query


def export_posts_csv(account_id: int) -> str:
    """Return CSV string of all posts for an account."""
    posts = queries.get_posts(account_id) or []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["shortcode", "post_type", "posted_at", "likes", "comments", "caption"])

    for p in posts:
        writer.writerow([
            p.get("shortcode", ""),
            p.get("post_type", ""),
            p.get("posted_at", ""),
            p.get("latest_likes") or 0,
            p.get("latest_comments") or 0,
            (p.get("caption") or "").replace("\n", " ")[:200]
        ])

    return output.getvalue()


def export_snapshots_csv(account_id: int) -> str:
    """Return CSV string of follower snapshot history."""
    snapshots = queries.get_snapshots(account_id, limit=1000) or []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["scraped_at", "followers", "following", "post_count"])

    for s in snapshots:
        writer.writerow([
            str(s.get("scraped_at", "")),
            s.get("followers", 0),
            s.get("following", 0),
            s.get("post_count", 0)
        ])

    return output.getvalue()


def export_comments_csv(account_id: int) -> str:
    """Return CSV of all comments across all posts for an account."""
    rows = execute_query("""
        SELECT p.shortcode, p.posted_at, c.commenter_username, c.comment_text, c.commented_at
        FROM comments c
        JOIN posts p ON c.post_id = p.id
        WHERE p.account_id = %s
        ORDER BY c.commented_at DESC
    """, (account_id,), fetch=True) or []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["post_shortcode", "post_date", "commenter", "comment", "commented_at"])

    for r in rows:
        writer.writerow([
            r.get("shortcode", ""),
            str(r.get("posted_at", "")),
            r.get("commenter_username", ""),
            (r.get("comment_text") or "").replace("\n", " "),
            str(r.get("commented_at", ""))
        ])

    return output.getvalue()
