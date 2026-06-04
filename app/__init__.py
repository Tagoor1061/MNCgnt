# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import Config
import atexit

# -----------------------------
# Extensions
# -----------------------------
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'   # type: ignore[attr-defined]
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
    from app.routes.about import bp as about_bp
    from app.routes.viewmap import bp as viewmap_bp
    from app.routes.news import bp as news_bp
    from app.routes.weather import bp as weather_bp
    from app.routes.push import bp as push_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(about_bp)
    app.register_blueprint(viewmap_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(push_bp)

    # Initialize background scheduler for weather monitoring
    from app.utils.weather_data import WeatherDataProcessor

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=lambda: WeatherDataProcessor.get_weather_summary(),
        trigger=IntervalTrigger(hours=1),  # Check every hour
        id='weather_monitor',
        name='Weather Monitoring Job',
        replace_existing=True
    )
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    return app

# -----------------------------
# User Loader for Flask-Login
# -----------------------------
from app.models import User  # Import after db is created

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
