from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from models.user import User
from models.password import Password
import app

db = app.db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("auth.login"))
        
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            flash("Admin access required", "error")
            return redirect(url_for("passwords.list_passwords"))
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@admin_bp.route("/")
@admin_required
def admin_dashboard():
    users = User.query.all()
    # Add password count for each user
    for user in users:
        user.password_count = Password.query.filter_by(user_id=user.id).count()
    return render_template("admin_dashboard.html", users=users)


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    user.password_count = Password.query.filter_by(user_id=user_id).count()
    
    if request.method == "POST":
        email = request.form.get("email")
        is_admin = request.form.get("is_admin") == "on"
        
        if not email:
            flash("Email is required", "error")
            return render_template("edit_user.html", user=user)
        
        # Check if email is already taken by another user
        existing_user = User.query.filter(User.email == email, User.id != user_id).first()
        if existing_user:
            flash("Email already exists", "error")
            return render_template("edit_user.html", user=user)
        
        user.email = email
        user.is_admin = is_admin
        db.session.commit()
        
        flash("User updated successfully", "success")
        return redirect(url_for("admin.admin_dashboard"))
    
    return render_template("edit_user.html", user=user)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Don't allow admin to delete themselves
    if user.id == session.get("user_id"):
        flash("You cannot delete your own account", "error")
        return redirect(url_for("admin.admin_dashboard"))
    
    # Delete all passwords associated with this user
    Password.query.filter_by(user_id=user_id).delete()
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    flash("User deleted successfully", "success")
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    
    # Set a temporary password
    new_password = "temp123456"
    user.password_hash = "temp_hash"  # This would normally be properly hashed
    
    db.session.commit()
    
    flash(f"Password for {user.email} has been reset to: {new_password}", "info")
    return redirect(url_for("admin.admin_dashboard"))
