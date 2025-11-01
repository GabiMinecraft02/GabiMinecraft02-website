import os
import json
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# ----------------------------
# Config port / host (Render)
# ----------------------------
PORT = int(os.environ.get("PORT", 5000))
HOST = "0.0.0.0"

# ----------------------------
# Flask app & secret
# ----------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change_this_secret_in_env")
MASTER_KEY = os.environ.get("MASTER_KEY", "change_this_master_key")

# ----------------------------
# Paths and settings
# ----------------------------
UPLOAD_FOLDER = "uploads"
TEXT_FOLDER = "texts"
AUTH_FILE = "auth.json"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
MAX_LOGIN_ATTEMPTS = 4
LOGIN_RESET_HOURS = 24

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEXT_FOLDER, exist_ok=True)
if not os.path.exists(AUTH_FILE):
    with open(AUTH_FILE, "w") as f:
        json.dump({}, f)

# ----------------------------
# Helper functions
# ----------------------------
def load_auth():
    with open(AUTH_FILE, "r") as f:
        return json.load(f)

def save_auth(auth_data):
    with open(AUTH_FILE, "w") as f:
        json.dump(auth_data, f, indent=4)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def limit_login_attempts(user):
    auth_data = load_auth()
    info = auth_data.get(user, {})
    attempts = info.get("attempts", 0)
    last_try = info.get("last_try", 0)
    now = time.time()
    if now - last_try > LOGIN_RESET_HOURS * 3600:
        attempts = 0
    if attempts >= MAX_LOGIN_ATTEMPTS:
        return False
    info["attempts"] = attempts + 1
    info["last_try"] = now
    auth_data[user] = info
    save_auth(auth_data)
    return True

def check_password(user, password):
    auth_data = load_auth()
    if user not in auth_data:
        return False
    return check_password_hash(auth_data[user]["password"], password)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_logged_in" not in session:
            flash("Admin login required")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ----------------------------
# Advancements page (uploads)
# ----------------------------
@app.route("/advancements", methods=["GET", "POST"])
def advancements():
    auth_data = load_auth()
    admin_pass = auth_data.get("admin", {}).get("password", None)
    if request.method == "POST":
        if session.get("admin_logged_in"):
            # Upload image
            if "image" in request.files:
                file = request.files["image"]
                if file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    flash("Image uploaded successfully")
            # Upload text
            text_content = request.form.get("text")
            if text_content:
                timestamp = int(time.time())
                text_file = os.path.join(TEXT_FOLDER, f"{timestamp}.txt")
                with open(text_file, "w", encoding="utf-8") as f:
                    f.write(text_content)
                flash("Text uploaded successfully")
        else:
            flash("You must be admin to upload")
            return redirect(url_for("admin_login"))
    images = os.listdir(UPLOAD_FOLDER)
    texts = os.listdir(TEXT_FOLDER)
    return render_template("advancements.html", images=images, texts=texts)

# ----------------------------
# Admin login
# ----------------------------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        user = request.form.get("login_id")
        password = request.form.get("password")
        if not limit_login_attempts(user):
            flash("Maximum login attempts reached, try again later")
            return redirect(url_for("admin_login"))
        if check_password(user, password):
            session["admin_logged_in"] = True
            flash("Logged in as admin")
            return redirect(url_for("advancements"))
        else:
            flash("Invalid login or password")
    return render_template("admin_login.html")

# ----------------------------
# Admin logout
# ----------------------------
@app.route("/admin_logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Logged out")
    return redirect(url_for("index"))

# ----------------------------
# Set credentials (master key required)
# ----------------------------
@app.route("/set_credentials", methods=["POST"])
def set_credentials():
    key = request.args.get("master_key")
    if key != MASTER_KEY:
        abort(403, "MASTER_KEY required")
    login_id = request.form.get("login_id")
    password = request.form.get("password")
    if not login_id or not password:
        abort(400, "login_id and password required")
    auth_data = load_auth()
    auth_data[login_id] = {"password": generate_password_hash(password), "attempts": 0, "last_try": 0}
    save_auth(auth_data)
    return jsonify({"status": "success", "login_id": login_id})

# ----------------------------
# Static files for uploads
# ----------------------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ----------------------------
# Run app
# ----------------------------
if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)
