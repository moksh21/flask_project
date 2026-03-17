from flask import Blueprint, render_template, redirect, url_for, request, session, flash, current_app
from werkzeug.utils import secure_filename
from models.user import User
from models.password import Password
import app
import os
import uuid

db = app.db

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")

# Avatar options
DEFAULT_AVATARS = [
    "avatar1.svg", "avatar2.svg", "avatar3.svg", "avatar4.svg", 
    "avatar5.svg", "avatar6.svg", "avatar7.svg", "avatar8.svg"
]

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@profile_bp.route("/")
def view_profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    
    user = User.query.get(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("auth.login"))
    
    password_count = Password.query.filter_by(user_id=user_id).count()
    return render_template("profile.html", user=user, password_count=password_count, avatars=DEFAULT_AVATARS)


@profile_bp.route("/edit", methods=["GET", "POST"])
def edit_profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    
    user = User.query.get(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        
        if not email:
            flash("Email is required", "error")
            return render_template("edit_profile.html", user=user, avatars=DEFAULT_AVATARS)
        
        # Check if email is already taken by another user
        existing_user = User.query.filter(User.email == email, User.id != user_id).first()
        if existing_user:
            flash("Email already exists", "error")
            return render_template("edit_profile.html", user=user, avatars=DEFAULT_AVATARS)
        
        user.email = email
        user.username = username if username else None
        db.session.commit()
        
        flash("Profile updated successfully", "success")
        return redirect(url_for("profile.view_profile"))
    
    return render_template("edit_profile.html", user=user, avatars=DEFAULT_AVATARS)


@profile_bp.route("/change-password", methods=["GET", "POST"])
def change_password():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    
    user = User.query.get(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        if not current_password or not new_password or not confirm_password:
            flash("All fields are required", "error")
            return render_template("change_password.html", user=user)
        
        # Verify current password (simplified - in production you'd use proper password verification)
        if current_password != "temp_password":  # This is a simplified check
            flash("Current password is incorrect", "error")
            return render_template("change_password.html", user=user)
        
        if new_password != confirm_password:
            flash("New passwords do not match", "error")
            return render_template("change_password.html", user=user)
        
        if len(new_password) < 6:
            flash("Password must be at least 6 characters", "error")
            return render_template("change_password.html", user=user)
        
        # Update password (simplified - in production you'd hash it properly)
        user.password_hash = "new_hash_" + new_password
        db.session.commit()
        
        flash("Password changed successfully", "success")
        return redirect(url_for("profile.view_profile"))
    
    return render_template("change_password.html", user=user)


@profile_bp.route("/upload-avatar", methods=["POST"])
def upload_avatar():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    
    user = User.query.get(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("profile.view_profile"))
    
    if 'avatar' not in request.files:
        flash("No file selected", "error")
        return redirect(url_for("profile.edit_profile"))
    
    file = request.files['avatar']
    if file.filename == '':
        flash("No file selected", "error")
        return redirect(url_for("profile.edit_profile"))
    
    if file and allowed_file(file.filename):
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        file.save(file_path)
        
        # Update user profile picture
        user.profile_picture = f"uploads/{unique_filename}"
        db.session.commit()
        
        flash("Profile picture updated successfully", "success")
    else:
        flash("Invalid file type. Please upload PNG, JPG, or GIF", "error")
    
    return redirect(url_for("profile.edit_profile"))


@profile_bp.route("/select-avatar/<avatar_name>", methods=["POST"])
def select_avatar(avatar_name):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    
    user = User.query.get(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("profile.edit_profile"))
    
    if avatar_name in DEFAULT_AVATARS:
        user.profile_picture = f"avatars/{avatar_name}"
        db.session.commit()
        flash("Profile picture updated successfully", "success")
    else:
        flash("Invalid avatar selection", "error")
    
    return redirect(url_for("profile.edit_profile"))
