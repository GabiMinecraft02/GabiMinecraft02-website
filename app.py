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

# ----------------------------
# Auth JSON path
# ----------------------------
AUTH_FILE = os.path.join(os.path.dirname(__file__), "auth.json")

# ----------------------------
# Load auth data
# ----------------------------
def load_auth():
    with open(AUTH_FILE, "r") as f:
        return json.load(f)

def save_auth(data):
    with open(AUTH_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ----------------------------
# Auth decorators
# ----------------------------
def master_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.args.get("master_key")
        auth = load_auth()
        if key != auth.get("master_key"):
            return "Forbidden\nMASTER_KEY required", 403
        return f(*args, **kwargs)
    return decorated

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated

# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/advancements")
@login_required
def advancements():
    # Liste des images/textes dans le dossier
    images_dir = os.path.join("static", "advancements", "images")
    texts_dir = os.path.join("static", "advancements", "texts")

    images = os.listdir(images_dir) if os.path.exists(images_dir) else []
    texts = os.listdir(texts_dir) if os.path.exists(texts_dir) else []

    return render_template("advancements.html", images=images, texts=texts)

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        login_id = request.form.get("login_id")
        password = request.form.get("password")
        auth = load_auth()
        admin = next((a for a in auth.get("admins", []) if a["login_id"] == login_id), None)
        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_logged_in"] = True
            flash("Admin logged in successfully", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid login or password", "danger")
    return render_template("admin_login.html")

# ----------------------------
# Upload for advancements
# ----------------------------
UPLOAD_FOLDER = os.path.join("static", "advancements")
os.makedirs(os.path.join(UPLOAD_FOLDER, "images"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "texts"), exist_ok=True)

@app.route("/advancements/upload", methods=["GET", "POST"])
@login_required
def upload_advancement():
    if request.method == "POST":
        if "image" in request.files:
            image = request.files["image"]
            if image.filename != "":
                filename = secure_filename(image.filename)
                image.save(os.path.join(UPLOAD_FOLDER, "images", filename))
        if "text" in request.form:
            text = request.form["text"]
            if text.strip():
                filename = f"{int(time.time())}.txt"
                with open(os.path.join(UPLOAD_FOLDER, "texts", filename), "w", encoding="utf-8") as f:
                    f.write(text)
        flash("Uploaded successfully!", "success")
        return redirect(url_for("advancements"))
    return render_template("upload.html")

# ----------------------------
# Run Flask
# ----------------------------
if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)
