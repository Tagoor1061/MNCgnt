# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

# -----------------------------
# Extensions
# -----------------------------
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # redirect unauthenticated users to login
login_manager.login_message_category = 'info'

# -----------------------------
# Application Factory
# -----------------------------
def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder="../templates",  # global templates
        static_folder="../static"       # global static files
    )
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    from app.routes.main import bp as main_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.services import bp as services_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(services_bp)

    return app

# -----------------------------
# User Loader for Flask-Login
# -----------------------------
from app.models import User  # Import after db is created

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
