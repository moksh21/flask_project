import random
import string
from flask import session
from datetime import datetime, timedelta


def generate_otp(length=6):
    """Generate a random numeric OTP of specified length."""
    digits = string.digits
    otp = ''.join(random.choices(digits, k=length))
    return otp


def store_otp(email, otp, expiry_minutes=5):
    """Store OTP in session with expiration time."""
    session['otp'] = {
        'email': email,
        'code': otp,
        'expires_at': (datetime.utcnow() + timedelta(minutes=expiry_minutes)).isoformat()
    }


def verify_stored_otp(email, user_input_otp):
    """Verify if the provided OTP matches the stored OTP and is not expired."""
    otp_data = session.get('otp')
    
    if not otp_data:
        return False, "No OTP found. Please request a new one."
    
    if otp_data['email'] != email:
        return False, "OTP does not match the email address."
    
    expires_at = datetime.fromisoformat(otp_data['expires_at'])
    if datetime.utcnow() > expires_at:
        session.pop('otp', None)
        return False, "OTP has expired. Please request a new one."
    
    if otp_data['code'] != user_input_otp:
        return False, "Invalid OTP. Please try again."
    
    session.pop('otp', None)
    return True, "OTP verified successfully."


def clear_otp():
    """Clear OTP from session."""
    session.pop('otp', None)
