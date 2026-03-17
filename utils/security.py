from datetime import datetime, timedelta
from flask import request, session, flash
import app
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

db = app.db

# Security settings
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = 15  # minutes
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@passwordmanager.com")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def is_account_locked(user):
    """Check if user account is locked due to failed attempts"""
    if user.locked_until and user.locked_until > datetime.utcnow():
        return True
    return False


def record_failed_login(user):
    """Record a failed login attempt and lock account if necessary"""
    user.failed_login_attempts += 1
    
    if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
        user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION)
        send_security_alert(user.email, "Account Locked", 
                          f"Your account has been locked due to {MAX_FAILED_ATTEMPTS} failed login attempts. "
                          f"It will be unlocked in {LOCKOUT_DURATION} minutes.")
    
    db.session.commit()


def record_successful_login(user):
    """Record a successful login and reset failed attempts"""
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    user.last_login_ip = request.remote_addr
    
    # Send login notification if it's a new location
    if user.last_login_ip != request.remote_addr:
        send_security_alert(user.email, "New Login Detected",
                          f"A new login was detected from IP: {request.remote_addr} "
                          f"at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    
    db.session.commit()


def send_security_alert(email, subject, message):
    """Send security alert email to user"""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print(f"[SECURITY ALERT] To: {email}")
        print(f"Subject: {subject}")
        print(f"Message: {message}")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = email
        msg["Subject"] = f"[Password Manager Security] {subject}"

        body = f"""
Security Alert - Password Manager

{message}

If you did not perform this action, please secure your account immediately.

Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
IP Address: {request.remote_addr}
        """
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
        
        print(f"Security alert sent to {email}")
    except Exception as e:
        print(f"Error sending security alert to {email}: {e}")


def check_login_attempts(user):
    """Check if user can attempt login based on failed attempts"""
    if is_account_locked(user):
        remaining_time = user.locked_until - datetime.utcnow()
        minutes = int(remaining_time.total_seconds() / 60)
        flash(f"Account locked. Try again in {minutes} minutes.", "error")
        return False
    return True


def get_security_status(user):
    """Get user's security status for dashboard"""
    status = {
        "failed_attempts": user.failed_login_attempts,
        "is_locked": is_account_locked(user),
        "last_login": user.last_login,
        "last_login_ip": user.last_login_ip,
        "lockout_time_remaining": None
    }
    
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining = user.locked_until - datetime.utcnow()
        status["lockout_time_remaining"] = int(remaining.total_seconds() / 60)
    
    return status
