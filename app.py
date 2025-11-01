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
# Files / folders
# ----------------------------
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
TEXT_FILE = os.path.join(UPLOAD_FOLDER, "text.txt")

AUTH_FILE = "auth.json"         # stores users dict
ATTEMPTS_FILE = "attempts.json" # stores attempts counters
SESSIONS_FILE = "sessions.json" # short-lived session tokens if needed

# ----------------------------
# Security params
# ----------------------------
MAX_ATTEMPTS = 4
ATTEMPT_WINDOW_SECONDS = 24 * 3600  # 24h
MASTER_KEY_ENV = "MASTER_KEY"       # env var name for master key
SESSION_TTL = 24 * 3600             # 24h session validity

# ----------------------------
# Simple JSON helpers
# ----------------------------
def read_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ----------------------------
# Auth management (users)
# auth.json structure:
# {
#   "users": {
#       "username_lower": {
#           "pw_hash": "...",
#           "created_at": 1234567890,
#           "owner": true/false
#       },
#       ...
#   }
# }
# ----------------------------
def load_auth():
    return read_json(AUTH_FILE, {"users": {}})

def save_auth(data):
    write_json(AUTH_FILE, data)

def is_user_present(username_lower):
    auth = load_auth()
    return username_lower in auth.get("users", {})

def create_user(username, password, owner=False):
    auth = load_auth()
    uname = username.lower()
    auth.setdefault("users", {})
    auth["users"][uname] = {
        "pw_hash": generate_password_hash(password),
        "created_at": int(time.time()),
        "owner": bool(owner)
    }
    save_auth(auth)

def delete_user(username):
    auth = load_auth()
    uname = username.lower()
    users = auth.get("users", {})
    if uname in users and not users[uname].get("owner"):
        users.pop(uname, None)
        save_auth(auth)
        return True
    return False

def reset_user_password(username, new_password):
    auth = load_auth()
    uname = username.lower()
    if uname in auth.get("users", {}):
        auth["users"][uname]["pw_hash"] = generate_password_hash(new_password)
        save_auth(auth)
        return True
    return False

# ----------------------------
# Attempts handling
# attempts.json structure:
# { "by_user": { "user": {"count": n, "reset_at": ts}}, "by_ip": {...} }
# ----------------------------
def get_attempts():
    return read_json(ATTEMPTS_FILE, {"by_user": {}, "by_ip": {}})

def save_attempts(data):
    write_json(ATTEMPTS_FILE, data)

def ensure_key(attempts, side, key):
    now = int(time.time())
    if key not in attempts.get(side, {}):
        attempts[side][key] = {"count": 0, "reset_at": now + ATTEMPT_WINDOW_SECONDS}
    else:
        if attempts[side][key].get("reset_at", 0) <= now:
            attempts[side][key] = {"count": 0, "reset_at": now + ATTEMPT_WINDOW_SECONDS}

def attempts_remaining(key, by="user"):
    attempts = get_attempts()
    side = "by_user" if by == "user" else "by_ip"
    ensure_key(attempts, side, key)
    info = attempts[side][key]
    return max(0, MAX_ATTEMPTS - info.get("count", 0)), info.get("reset_at", int(time.time()) + ATTEMPT_WINDOW_SECONDS)

def incr_attempt(key, by="user"):
    attempts = get_attempts()
    side = "by_user" if by == "user" else "by_ip"
    ensure_key(attempts, side, key)
    attempts[side][key]["count"] = attempts[side][key].get("count", 0) + 1
    save_attempts(attempts)

def reset_attempts_for(key, by="user"):
    attempts = get_attempts()
    side = "by_user" if by == "user" else "by_ip"
    ensure_key(attempts, side, key)
    attempts[side][key] = {"count": 0, "reset_at": int(time.time()) + ATTEMPT_WINDOW_SECONDS}
    save_attempts(attempts)

# ----------------------------
# Session helpers (Flask session)
# We store: session['admin_user'] and session['admin_until'] (timestamp)
# ----------------------------
def login_session_set(username):
    session['admin_user'] = username.lower()
    session['admin_until'] = int(time.time()) + SESSION_TTL

def login_session_clear():
    session.pop('admin_user', None)
    session.pop('admin_until', None)

def login_session_valid():
    u = session.get('admin_user')
    until = session.get('admin_until', 0)
    return bool(u) and int(until) > int(time.time())

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not login_session_valid():
            flash("Accès admin requis.", "error")
            return redirect(url_for("advancements"))
        return f(*args, **kwargs)
    return decorated

# ----------------------------
# Routes: index + advancements
# ----------------------------
@app.before_request
def cleanup_attempts():
    # normalize and reset expired attempt windows
    attempts = get_attempts()
    now = int(time.time())
    changed = False
    for side in ("by_user", "by_ip"):
        for key, val in list(attempts.get(side, {}).items()):
            if val.get("reset_at", 0) <= now:
                attempts[side][key] = {"count": 0, "reset_at": now + ATTEMPT_WINDOW_SECONDS}
                changed = True
    if changed:
        save_attempts(attempts)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/advancements")
def advancements():
    images = sorted([f for f in os.listdir(UPLOAD_FOLDER)
                     if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))])
    texts = []
    if os.path.exists(TEXT_FILE):
        with open(TEXT_FILE, "r", encoding="utf-8") as tf:
            texts = [line.strip() for line in tf.readlines() if line.strip()]
    client_ip = request.remote_addr or "unknown"
    rem_ip, reset_at = attempts_remaining(client_ip, by="ip")
    return render_template("advancements.html", images=images, texts=texts,
                           attempts_left=rem_ip, reset_at=reset_at, session_valid=login_session_valid())

# ----------------------------
# Upload handlers
# ----------------------------
@app.route("/upload_image", methods=["POST"])
def upload_image():
    name = request.form.get("name", "").strip()
    file = request.files.get("file")
    if not file or file.filename == "":
        flash("Aucun fichier sélectionné.", "error")
        return redirect(url_for("advancements"))
    filename = secure_filename(file.filename)
    if name:
        base, ext = os.path.splitext(filename)
        filename = secure_filename(f"{name}_{base}{ext}")
    dest = os.path.join(UPLOAD_FOLDER, filename)
    file.save(dest)
    flash("Image uploadée.", "success")
    return redirect(url_for("advancements"))

@app.route("/upload_text", methods=["POST"])
def upload_text():
    text = request.form.get("text", "").strip()
    if not text:
        flash("Aucun texte fourni.", "error")
        return redirect(url_for("advancements"))
    with open(TEXT_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    flash("Texte ajouté.", "success")
    return redirect(url_for("advancements"))

# ----------------------------
# Locked login (from advancements page)
# ----------------------------
@app.route("/locked_login", methods=["POST"])
def locked_login():
    username = request.form.get("login_id", "").strip().lower()
    password = request.form.get("password", "")
    client_ip = request.remote_addr or "unknown"

    # check ip attempts
    rem_ip, _ = attempts_remaining(client_ip, by="ip")
    if rem_ip <= 0:
        flash("Trop d'essais depuis ton IP. Reviens plus tard.", "error")
        return redirect(url_for("advancements"))

    auth = load_auth()
    users = auth.get("users", {})

    if username not in users:
        # register attempts for ip and username
        incr_attempt(client_ip, by="ip")
        incr_attempt(username, by="user")
        rem, _ = attempts_remaining(client_ip, by="ip")
        flash(f"Identifiants incorrects. Essais restants (IP): {rem}", "error")
        return redirect(url_for("advancements"))

    stored = users[username]
    if not check_password_hash(stored["pw_hash"], password):
        incr_attempt(client_ip, by="ip")
        incr_attempt(username, by="user")
        rem, _ = attempts_remaining(client_ip, by="ip")
        flash(f"Identifiants incorrects. Essais restants (IP): {rem}", "error")
        return redirect(url_for("advancements"))

    # success -> set session and reset attempts
    login_session_set(username)
    reset_attempts_for(client_ip, by="ip")
    reset_attempts_for(username, by="user")
    flash("Connexion réussie. Zone admin déverrouillée 24h.", "success")
    return redirect(url_for("locked_area"))

# ----------------------------
# Locked area (admin dashboard) - requires session
# ----------------------------
@app.route("/locked_area")
def locked_area():
    if not login_session_valid():
        flash("Connecte-toi d'abord via le formulaire.", "error")
        return redirect(url_for("advancements"))
    auth = load_auth()
    users = auth.get("users", {})
    # prepare list with flags
    users_list = []
    for uname, info in users.items():
        users_list.append({
            "username": uname,
            "created_at": info.get("created_at"),
            "owner": info.get("owner", False)
        })
    return render_template("locked_area.html", users=users_list)

# ----------------------------
# Admin actions (create / delete / unlock user) - protected by session
# ----------------------------
@app.route("/admin_create_user", methods=["POST"])
@require_admin
def admin_create_user():
    new_login = request.form.get("new_login", "").strip().lower()
    new_pass = request.form.get("new_pass", "")
    if not new_login or not new_pass:
        flash("Login et mot de passe requis.", "error")
        return redirect(url_for("locked_area"))
    if is_user_present(new_login):
        flash("Utilisateur existe déjà.", "error")
        return redirect(url_for("locked_area"))
    create_user(new_login, new_pass, owner=False)
    flash(f"Utilisateur {new_login} créé.", "success")
    return redirect(url_for("locked_area"))

@app.route("/admin_delete_user", methods=["POST"])
@require_admin
def admin_delete_user():
    target = request.form.get("target", "").strip().lower()
    if not target:
        flash("Utilisateur non précisé.", "error")
        return redirect(url_for("locked_area"))
    auth = load_auth()
    users = auth.get("users", {})
    if target not in users:
        flash("Utilisateur introuvable.", "error")
        return redirect(url_for("locked_area"))
    if users[target].get("owner"):
        flash("Impossible de supprimer le compte owner.", "error")
        return redirect(url_for("locked_area"))
    deleted = delete_user(target)
    if deleted:
        flash("Utilisateur supprimé.", "success")
    else:
        flash("Impossible de supprimer l'utilisateur.", "error")
    return redirect(url_for("locked_area"))

@app.route("/admin_reset_attempts", methods=["POST"])
@require_admin
def admin_reset_attempts():
    target = request.form.get("target", "").strip().lower()
    if not target:
        flash("Utilisateur non précisé.", "error")
        return redirect(url_for("locked_area"))
    reset_attempts_for(target, by="user")
    flash("Essais réinitialisés pour l'utilisateur.", "success")
    return redirect(url_for("locked_area"))

@app.route("/admin_logout", methods=["POST"])
@require_admin
def admin_logout():
    login_session_clear()
    flash("Déconnecté.", "success")
    return redirect(url_for("advancements"))

# ----------------------------
# Set credentials route
# - if no users exist: allow creation without MASTER_KEY (initial setup)
# - otherwise require MASTER_KEY in query or form
# ----------------------------
@app.route("/set_credentials", methods=["GET", "POST"])
def set_credentials():
    auth = load_auth()
    users = auth.get("users", {})
    master_key = os.environ.get(MASTER_KEY_ENV)

    # initial setup: if no users, allow creation without master_key
    initial_setup = len(users) == 0

    provided_key = request.values.get("master_key", "")

    if not initial_setup:
        # must provide correct master key
        if not master_key or provided_key != master_key:
            return abort(403, description="MASTER_KEY required")

    if request.method == "POST":
        new_login = request.form.get("new_login", "").strip().lower()
        new_pass = request.form.get("new_pass", "")
        if not new_login or not new_pass:
            flash("Login et mot de passe requis.", "error")
            return redirect(request.url)
        # if first user, mark owner
        owner_flag = initial_setup
        create_user(new_login, new_pass, owner=owner_flag)
        flash("Identifiants créés.", "success")
        return redirect(url_for("advancements"))
    # GET: render form
    return render_template("set_credentials.html", initial_setup=initial_setup, master_key=provided_key)

# ----------------------------
# Serve uploads
# ----------------------------
@app.route("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)

# ----------------------------
# Utility: attempts left (api)
# ----------------------------
@app.route("/attempts_left")
def attempts_left():
    cid = request.remote_addr or "unknown"
    rem_ip, reset_at = attempts_remaining(cid, by="ip")
    return jsonify({"attempts_left_ip": rem_ip, "reset_at": reset_at})

# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    # Affiche toutes les routes disponibles pour debugging
    print("=== Liste des routes Flask ===")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
