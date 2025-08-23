# models.py
from flask_login import UserMixin
from app import db
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)  # type: ignore
    username = db.Column(db.String(50), unique=True, nullable=False)  # type: ignore
    email = db.Column(db.String(120), unique=True, nullable=False)  # type: ignore
    password_hash = db.Column(db.String(128), nullable=False)  # type: ignore
    role = db.Column(db.String(20), default="user")  # type: ignore  # "admin" or "user"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def load_user(user_id): # type: ignore
        return User.query.get(int(user_id))
