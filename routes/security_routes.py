from flask import Blueprint, render_template, redirect, url_for, session
from models.user import User
from utils.security import get_security_status
import app

db = app.db

security_bp = Blueprint("security", __name__, url_prefix="/security")


@security_bp.route("/")
def security_dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    
    user = User.query.get(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("auth.login"))
    
    security_status = get_security_status(user)
    return render_template("security_dashboard.html", user=user, security=security_status)


@security_bp.route("/unlock-account", methods=["POST"])
def unlock_account():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    
    user = User.query.get(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("auth.login"))
    
    # Reset failed attempts and unlock
    user.failed_login_attempts = 0
    user.locked_until = None
    db.session.commit()
    
    flash("Account unlocked successfully", "success")
    return redirect(url_for("security.security_dashboard"))
