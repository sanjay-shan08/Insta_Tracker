from instagrapi import Client
from instagrapi.exceptions import LoginRequired, UserNotFound, PrivateError
import time
from config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, MAX_POSTS_PER_SCRAPE, MAX_COMMENTS_PER_POST

_client = None

def get_client():
    global _client
    if _client is None:
        _client = Client()
        try:
            _client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            print(f"[instagrapi] Logged in as @{INSTAGRAM_USERNAME}")
        except Exception as e:
            print(f"[instagrapi] Login failed: {e}")
    return _client


def scrape_profile(username: str) -> dict:
    cl = get_client()

    try:
        # Get user info
        user = cl.user_info_by_username(username)

        profile = {
            "username":        user.username,
            "full_name":       user.full_name,
            "bio":             user.biography,
            "profile_pic_url": str(user.profile_pic_url),
            "followers":       user.follower_count,
            "following":       user.following_count,
            "post_count":      user.media_count,
            "is_private":      user.is_private,
        }

        if user.is_private:
            return {"error": "private", "username": username}

        posts_result = []

        # Get recent posts
        medias = cl.user_medias(user.pk, amount=MAX_POSTS_PER_SCRAPE)

        for media in medias:
            post_type = "image"
            if media.media_type == 2:
                post_type = "video"
            elif media.media_type == 8:
                post_type = "carousel"

            post_data = {
                "shortcode":      media.code,
                "caption":        media.caption_text or "",
                "post_type":      post_type,
                "media_url":      str(media.thumbnail_url or media.video_url or ""),
                "posted_at":      media.taken_at.strftime("%Y-%m-%d %H:%M:%S"),
                "likes":          media.like_count,
                "comments_count": media.comment_count,
                "comments":       []
            }

            # Get comments
            try:
                comments = cl.media_comments(media.id, amount=MAX_COMMENTS_PER_POST)
                for c in comments:
                    post_data["comments"].append({
                        "username":     c.user.username,
                        "text":         c.text,
                        "commented_at": c.created_at_utc.strftime("%Y-%m-%d %H:%M:%S")
                    })
                time.sleep(1)
            except Exception:
                pass

            posts_result.append(post_data)
            time.sleep(2)

        return {"profile": profile, "posts": posts_result}

    except UserNotFound:
        return {"error": "not_found", "username": username}
    except PrivateError:
        return {"error": "private", "username": username}
    except LoginRequired:
        return {"error": "login_required", "username": username}
    except Exception as e:
        print(f"[Scraper] ERROR: {type(e).__name__}: {e}")
        return {"error": "unknown", "message": str(e), "username": username}