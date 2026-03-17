from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from models.password import Password
from models.user import User
import app

db = app.db

password_bp = Blueprint("passwords", __name__, url_prefix="/passwords")


@password_bp.route("/")
def list_passwords():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    entries = Password.query.filter_by(user_id=user_id).all()
    user = User.query.get(user_id)
    return render_template("dashboard.html", entries=entries, user=user)


@password_bp.route("/add", methods=["GET", "POST"])
def add_password():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        site = request.form.get("site")
        username = request.form.get("username")
        password_plain = request.form.get("password")

        # NOTE: for now we store plain text; later you can encrypt
        entry = Password(
            user_id=user_id,
            site=site,
            username=username,
            password_encrypted=password_plain,
        )
        db.session.add(entry)
        db.session.commit()
        return redirect(url_for("passwords.list_passwords"))
    return render_template("add_password.html")


@password_bp.route("/<int:entry_id>/edit", methods=["GET", "POST"])
def edit_password(entry_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    
    entry = Password.query.filter_by(id=entry_id, user_id=user_id).first()
    if not entry:
        flash("Password entry not found", "error")
        return redirect(url_for("passwords.list_passwords"))
    
    if request.method == "POST":
        site = request.form.get("site")
        username = request.form.get("username")
        password_plain = request.form.get("password")
        
        if not site or not username or not password_plain:
            flash("All fields are required", "error")
            return render_template("edit_password.html", entry=entry, password=entry.password_encrypted)
        
        entry.site = site
        entry.username = username
        entry.password_encrypted = password_plain
        db.session.commit()
        
        flash("Password updated successfully", "success")
        return redirect(url_for("passwords.list_passwords"))
    
    return render_template("edit_password.html", entry=entry, password=entry.password_encrypted)


@password_bp.route("/<int:entry_id>/delete", methods=["POST"])
def delete_password(entry_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    
    entry = Password.query.filter_by(id=entry_id, user_id=user_id).first()
    if not entry:
        flash("Password entry not found", "error")
        return redirect(url_for("passwords.list_passwords"))
    
    db.session.delete(entry)
    db.session.commit()
    
    flash("Password deleted successfully", "success")
    return redirect(url_for("passwords.list_passwords"))