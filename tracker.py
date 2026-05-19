from scrapers.instagram import scrape_profile
from db import queries

def run_scrape(username: str) -> dict:
    """
    Full scrape pipeline: fetch from Instagram → save to MySQL.
    Returns a status dict for the Flask route to use.
    """
    data = scrape_profile(username)

    if not data:
        return {"success": False, "error": "No data returned"}

    if "error" in data:
        error_map = {
            "private":       "This account is private. Only public profiles can be tracked.",
            "not_found":     f"Account @{username} was not found on Instagram.",
            "login_required":"Instagram requires login to view this profile.",
            "rate_limited":  "Instagram rate limit hit. Please wait a few minutes and try again.",
            "unknown":       data.get("message", "An unexpected error occurred.")
        }
        return {"success": False, "error": error_map.get(data["error"], "Unknown error")}

    profile = data["profile"]

    # 1. Save / update account
    account_id = queries.upsert_account(profile)

    # 2. Save follower snapshot
    queries.insert_snapshot(
        account_id,
        profile["followers"],
        profile["following"],
        profile["post_count"]
    )

    # 3. Save posts + stats + comments
    saved_posts = 0
    for post_data in data["posts"]:
        post_id = queries.upsert_post(account_id, post_data)
        queries.insert_post_stats(post_id, post_data["likes"], post_data["comments_count"])

        for comment in post_data.get("comments", []):
            queries.insert_comment(
                post_id,
                comment["username"],
                comment["text"],
                comment["commented_at"]
            )
        saved_posts += 1

    return {
        "success":    True,
        "username":   profile["username"],
        "full_name":  profile["full_name"],
        "followers":  profile["followers"],
        "following":  profile["following"],
        "post_count": profile["post_count"],
        "posts_saved": saved_posts,
        "account_id": account_id
    }
