import app

db = app.db

class Password(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    site = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    password_encrypted = db.Column(db.String(255), nullable=False)