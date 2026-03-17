import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_otp_email(to_email, otp):
    """Send OTP email to the specified address."""
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_username = os.environ.get('SMTP_USERNAME', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    sender_email = os.environ.get('SENDER_EMAIL', smtp_username)
    
    if not smtp_username or not smtp_password:
        print(f"[DEV MODE] OTP for {to_email}: {otp}")
        return True, "OTP sent successfully (logged to console for development)"
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Your Password Manager OTP'
        msg['From'] = sender_email
        msg['To'] = to_email
        
        text_content = f"""
Your One-Time Password (OTP) for login is: {otp}

This OTP will expire in 5 minutes.

If you did not request this OTP, please ignore this email.
"""
        
        html_content = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #4a90d9;">Password Manager OTP</h2>
        <p>Your One-Time Password (OTP) for login is:</p>
        <div style="background: #f5f5f5; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
            {otp}
        </div>
        <p>This OTP will expire in <strong>5 minutes</strong>.</p>
        <p style="color: #666; font-size: 12px;">If you did not request this OTP, please ignore this email.</p>
    </div>
</body>
</html>
"""
        
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        
        return True, "OTP sent successfully"
        
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"
