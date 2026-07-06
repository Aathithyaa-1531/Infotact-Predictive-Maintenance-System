import os
import re
from datetime import datetime
import joblib
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, save_prediction, get_predictions, get_stats, create_user, get_user_by_username, get_user_by_email
app = Flask(__name__)
app.secret_key = "dev-key"

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL = joblib.load(os.path.join(BASE, "predictive_maintenance_model.pkl"))

TYPE_MAP = {"L": 0, "M": 1, "H": 2}
TYPE_LABELS = {"L": "Light", "M": "Medium", "H": "Heavy"}

init_db()

def predict_engine(form):
    air = float(form["air_temp"])
    proc = float(form["process_temp"])
    rpm = float(form["rpm"])
    torque = float(form["torque"])
    wear = float(form["tool_wear"])

    row = {
        "Type": TYPE_MAP.get(form.get("engine_type", "M"), 1),
        "Air temperature [K]": air,
        "Process temperature [K]": proc,
        "Rotational speed [rpm]": rpm,
        "Torque [Nm]": torque,
        "Tool wear [min]": wear,
        "Temp_Difference": proc - air,
        "Power_Index": rpm * torque,
        "Torque_RPM_Ratio": torque / rpm,
    }

    df = pd.DataFrame([row])[list(MODEL.feature_names_in_)]
    prob = float(MODEL.predict_proba(df)[0][1])
    fail = int(MODEL.predict(df)[0])

    if prob >= 0.6:
        risk, msg = "danger", "Get service immediately — the engine may fail!"
        days = max(3, int(15 * (1 - prob)))
        health = max(10, int(100 - prob * 100))
    elif prob >= 0.3:
        risk, msg = "warning", "Please schedule service soon."
        days = max(15, int(40 * (1 - prob)))
        health = max(40, int(75 - prob * 50))
    else:
        risk, msg = "safe", "Engine is healthy — continue regular maintenance."
        days = max(60, int(120 * (1 - prob)))
        health = max(70, int(95 - prob * 30))

    return {
        "fail": fail,
        "prob": round(prob * 100, 1),
        "risk": risk,
        "msg": msg,
        "days": days,
        "health": health,
        "time": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "rpm": rpm,
        "torque": torque,
        "wear": wear,
        "engine": TYPE_LABELS.get(form.get("engine_type", "M"), "Medium"),
    }

@app.route("/")
def home():
    stats = get_stats(session.get('user_id'))
    return render_template("index.html", stats=stats)


@app.route("/predict", methods=["POST"])
def predict():
    if "user_id" not in session:
        flash("Please sign in to run predictions.")
        return redirect(url_for("login"))
    try:
        result = predict_engine(request.form)
        save_prediction(request.form, result, session["user_id"])
        return render_template("result.html", r=result)
    except Exception as e:
        flash(f"Error: {e}")
        return redirect(url_for("home"))


@app.route("/history")
def history():
    if "user_id" not in session:
        flash("Please sign in to view history.")
        return redirect(url_for("login"))
    records = get_predictions(session["user_id"])
    stats = get_stats(session["user_id"])
    return render_template("history.html", records=records, stats=stats)


def validate_password(password):
    """Validate password strength: minimum 8 characters, with a mix of uppercase, lowercase, numbers, and special characters."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (!@#$%^&*(), etc.)."
    return True, ""


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        if not username or not email or not password:
            flash("Please fill in all fields.")
            return redirect(url_for("signup"))
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Please enter a valid email address.")
            return redirect(url_for("signup"))
        
        existing_user = get_user_by_username(username)
        if existing_user:
            flash("Username already exists. Please choose another one.")
            return redirect(url_for("signup"))
            
        existing_email = get_user_by_email(email)
        if existing_email:
            flash("Email address is already registered. Please login or use another one.")
            return redirect(url_for("signup"))
        
        is_valid, err_msg = validate_password(password)
        if not is_valid:
            flash(err_msg)
            return redirect(url_for("signup"))
        
        password_hash = generate_password_hash(password)
        if create_user(username, email, password_hash):
            flash("Signup successful! Please sign in.")
            return redirect(url_for("login"))
        else:
            flash("Something went wrong. Please try again.")
            return redirect(url_for("signup"))
    
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not identifier or not password:
            flash("Please fill in all fields.")
            return redirect(url_for("login"))
        
        # Support login by username or email
        user = get_user_by_username(identifier)
        if not user:
            user = get_user_by_email(identifier)
            
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome, {user['username']}!")
            return redirect(url_for("home"))
        else:
            flash("Invalid username/email or password.")
            return redirect(url_for("login"))
            
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.")
    return redirect(url_for("home"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/project")
def project():
    return render_template("project.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    print("\n>>> Server: http://127.0.0.1:5000")
    print(">>> Database: data/pridectiveengine.db\n")
    app.run(host="127.0.0.1", port=5000, debug=True)
