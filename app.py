from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import pathlib

APP_DIR = pathlib.Path(__file__).parent
DB_PATH = APP_DIR / "users.db"
COMMON_FILE = APP_DIR / "common_passwords.txt"

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"  # change before production!

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Load common passwords into a set (lowercased)
with COMMON_FILE.open(encoding="utf-8") as f:
    COMMON_PASSWORDS = set(line.strip().lower() for line in f if line.strip())

def init_db_if_needed():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )""")
    conn.commit()
    conn.close()

init_db_if_needed()

@app.route("/")
def index():
    user = session.get("username")
    return render_template("index.html", user=user)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # server-side validations
        errors = []
        if not username:
            errors.append("Username is required.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit.")
        if not any(not c.isalnum() for c in password):
            errors.append("Password must contain at least one special character.")
        if password.lower() in COMMON_PASSWORDS:
            errors.append("This password is found in a common-password list. Choose another password.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html", username=username)
        
        password_hash = generate_password_hash(password)
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            flash("Username already exists. Choose another.", "danger")
            return render_template("register.html", username=username)

        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()
        if row and check_password_hash(row["password_hash"], password):
            session["username"] = username
            flash("Logged in successfully.", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "danger")
            return render_template("login.html", username=username)

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Logged out.", "info")
    return redirect(url_for("index"))

@app.route("/api/check_password", methods=["POST"])
def api_check_password():
    """
    Expects JSON: { "password": "..." }
    Returns JSON with rule booleans and whether in common-password list.
    """
    data = request.get_json(force=True, silent=True) or {}
    password = data.get("password", "")

    resp = {
        "length_ok": len(password) >= 8,
        "has_upper": any(c.isupper() for c in password),
        "has_digit": any(c.isdigit() for c in password),
        "has_special": any(not c.isalnum() for c in password),
        "in_common": password.lower() in COMMON_PASSWORDS,
        "length": len(password)
    }
    # simple score: count of satisfied basic requirements (length + upper + digit + special) minus penalty for common
    score = 0
    score += 1 if resp["length_ok"] else 0
    score += 1 if resp["has_upper"] else 0
    score += 1 if resp["has_digit"] else 0
    score += 1 if resp["has_special"] else 0
    if resp["in_common"]:
        score = max(0, score - 2)
    resp["score"] = score  # 0-4 typically
    return jsonify(resp)

if __name__ == "__main__":
    app.run(debug=True)
