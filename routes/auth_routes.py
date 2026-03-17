from flask import Blueprint, render_template, redirect, url_for, request

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    from werkzeug.security import check_password_hash
    from models.user import User
    from flask import session, flash
    from utils.security import check_login_attempts, record_failed_login, record_successful_login, MAX_FAILED_ATTEMPTS

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        
        # Check if user exists
        if not user:
            flash("Invalid email or password", "error")
            return render_template("login.html")
        
        # Check if account is locked
        if not check_login_attempts(user):
            return render_template("login.html")
        
        # Check password
        if not check_password_hash(user.password_hash, password):
            record_failed_login(user)
            remaining_attempts = MAX_FAILED_ATTEMPTS - user.failed_login_attempts
            if remaining_attempts > 0:
                flash(f"Invalid email or password. {remaining_attempts} attempts remaining.", "error")
            else:
                flash("Account locked due to too many failed attempts. Check your email for details.", "error")
            return render_template("login.html")

        # Successful login
        record_successful_login(user)
        session["user_id"] = user.id
        session["user_email"] = user.email
        flash("Login successful", "success")
        return redirect(url_for("passwords.list_passwords"))

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    from werkzeug.security import generate_password_hash
    from flask import flash, session
    from models.user import User
    import app
    db = app.db
    from utils.otp import generate_otp, store_otp
    from utils.mail import send_otp_email

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not email or not password:
            flash("Email and password are required", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("register.html")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered", "error")
            return render_template("register.html")

        password_hash = generate_password_hash(password)
        new_user = User(email=email, password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()

        otp = generate_otp()
        store_otp(email, otp)
        success, message = send_otp_email(email, otp)
        if not success:
            flash(message, "error")
            return render_template("register.html")

        session["pending_email"] = email
        session["pending_user_id"] = new_user.id
        flash("OTP sent to your email. Verify to activate your account.", "success")
        return redirect(url_for("auth.verify_otp"))

    return render_template("register.html")


@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    from flask import session, flash
    from models.user import User
    from utils.otp import verify_stored_otp

    email = session.get("pending_email")
    pending_user_id = session.get("pending_user_id")
    if not email:
        flash("Please register first", "error")
        return redirect(url_for("auth.register"))

    if request.method == "POST":
        user_otp = request.form.get("otp")
        is_valid, message = verify_stored_otp(email, user_otp)
        if not is_valid:
            flash(message, "error")
            return render_template("verify_otp.html")

        user = None
        if pending_user_id:
            user = User.query.get(pending_user_id)
        if not user:
            user = User.query.filter_by(email=email).first()

        session["user_id"] = user.id
        session["user_email"] = user.email
        session.pop("pending_email", None)
        session.pop("pending_user_id", None)
        flash("Account verified successfully", "success")
        return redirect(url_for("passwords.list_passwords"))

    return render_template("verify_otp.html")


@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    from flask import session, flash
    from utils.otp import generate_otp, store_otp
    from utils.mail import send_otp_email

    email = session.get("pending_email")
    if not email:
        flash("Please register first", "error")
        return redirect(url_for("auth.register"))

    otp = generate_otp()
    store_otp(email, otp)
    success, message = send_otp_email(email, otp)
    if success:
        flash("New OTP sent to your email", "success")
    else:
        flash(message, "error")
    return redirect(url_for("auth.verify_otp"))


@auth_bp.route("/logout", methods=["POST"])
def logout():
    from flask import session, flash
    from utils.otp import clear_otp

    clear_otp()
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("auth.login"))