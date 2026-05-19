from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response
from config import FLASK_SECRET_KEY, FLASK_DEBUG, FLASK_PORT
from tracker import run_scrape
from db import queries
from export import export_posts_csv, export_snapshots_csv, export_comments_csv
import threading

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
app.jinja_env.globals['enumerate'] = enumerate

# ─── HOME / DASHBOARD ────────────────────────────────────────────────────────
@app.route("/")
def index():
    accounts = queries.get_all_accounts() or []
    return render_template("index.html", accounts=accounts)

# ─── ADD / SCRAPE ACCOUNT ────────────────────────────────────────────────────
@app.route("/add", methods=["POST"])
def add_account():
    username = request.form.get("username", "").strip().lstrip("@")
    if not username:
        flash("Please enter a username.", "error")
        return redirect(url_for("index"))
    flash(f"Scraping @{username}… this may take a minute.", "info")
    return redirect(url_for("scrape_account", username=username))

@app.route("/scrape/<username>")
def scrape_account(username):
    result = run_scrape(username)
    if result["success"]:
        flash(f"✅ @{username} scraped — {result['posts_saved']} posts saved.", "success")
        return redirect(url_for("profile", username=username))
    else:
        flash(f"❌ {result['error']}", "error")
        return redirect(url_for("index"))

# ─── ASYNC SCRAPE (AJAX) ─────────────────────────────────────────────────────
scrape_status = {}  # simple in-memory job tracker

@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    data = request.get_json()
    username = data.get("username", "").strip().lstrip("@")
    if not username:
        return jsonify({"error": "No username provided"}), 400

    job_id = username
    scrape_status[job_id] = {"status": "running", "username": username}

    def do_scrape():
        result = run_scrape(username)
        scrape_status[job_id] = {"status": "done", "result": result}

    thread = threading.Thread(target=do_scrape, daemon=True)
    thread.start()
    return jsonify({"job_id": job_id, "status": "started"})

@app.route("/api/scrape/status/<job_id>")
def scrape_job_status(job_id):
    return jsonify(scrape_status.get(job_id, {"status": "not_found"}))

# ─── PROFILE PAGE ────────────────────────────────────────────────────────────
@app.route("/profile/<username>")
def profile(username):
    account = queries.get_account_by_username(username)
    if not account:
        flash(f"@{username} not found. Add it first.", "error")
        return redirect(url_for("index"))

    posts      = queries.get_posts(account["id"]) or []
    snapshots  = queries.get_snapshots(account["id"]) or []
    stats      = queries.get_engagement_stats(account["id"])
    eng_stats  = stats[0] if stats else {}

    # Prepare chart data (followers over time)
    chart_labels = [str(s["scraped_at"])[:10] for s in reversed(snapshots)]
    chart_followers = [s["followers"] for s in reversed(snapshots)]

    return render_template("profile.html",
        account=account,
        posts=posts,
        snapshots=snapshots,
        eng_stats=eng_stats,
        chart_labels=chart_labels,
        chart_followers=chart_followers
    )

# ─── POST DETAIL ─────────────────────────────────────────────────────────────
@app.route("/post/<int:post_id>")
def post_detail(post_id):
    from db.queries import execute_query
    post = execute_query("SELECT * FROM posts WHERE id=%s", (post_id,), fetch=True)
    if not post:
        return redirect(url_for("index"))
    post = post[0]
    comments = queries.get_comments(post_id) or []
    stats = execute_query("""
        SELECT * FROM post_stats WHERE post_id=%s ORDER BY scraped_at DESC LIMIT 10
    """, (post_id,), fetch=True) or []
    return render_template("post.html", post=post, comments=comments, stats=stats)

# ─── DELETE ACCOUNT ──────────────────────────────────────────────────────────
@app.route("/delete/<int:account_id>", methods=["POST"])
def delete_account(account_id):
    queries.delete_account(account_id)
    flash("Account removed.", "info")
    return redirect(url_for("index"))

# ─── CSV EXPORTS ─────────────────────────────────────────────────────────────
@app.route("/export/<username>/posts")
def export_posts(username):
    account = queries.get_account_by_username(username)
    if not account:
        return "Account not found", 404
    csv_data = export_posts_csv(account["id"])
    return Response(csv_data, mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={username}_posts.csv"})

@app.route("/export/<username>/snapshots")
def export_snapshots(username):
    account = queries.get_account_by_username(username)
    if not account:
        return "Account not found", 404
    csv_data = export_snapshots_csv(account["id"])
    return Response(csv_data, mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={username}_snapshots.csv"})

@app.route("/export/<username>/comments")
def export_comments_route(username):
    account = queries.get_account_by_username(username)
    if not account:
        return "Account not found", 404
    csv_data = export_comments_csv(account["id"])
    return Response(csv_data, mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={username}_comments.csv"})

# ─── API: ALL ACCOUNTS JSON ──────────────────────────────────────────────────
@app.route("/api/accounts")
def api_accounts():
    return jsonify(queries.get_all_accounts() or [])

if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)
