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
# Auth file
# ----------------------------
AUTH_FILE = "auth.json"
with open(AUTH_FILE, "r") as f:
    auth_data = json.load(f)

MASTER_KEY = auth_data["master_key"]
ADMINS = auth_data["admins"]

# ----------------------------
# Helpers
# ----------------------------
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_logged_in" not in session:
            abort(403)
        return f(*args, **kwargs)
    return decorated

# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/advancements")
def advancements():
    # Lire les images et textes depuis un dossier /json si besoin
    images = []  # ex: ["img1.png", "img2.png"]
    texts = []   # ex: ["texte 1", "texte 2"]
    return render_template("advancements.html", images=images, texts=texts)

# ----------------------------
# Static files
# ----------------------------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory("uploads", filename)

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)
