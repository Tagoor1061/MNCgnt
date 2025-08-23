from app import db, create_app
from app.models import User

# Create app instance
app = create_app()

# Create tables inside app context
with app.app_context():
    db.create_all()
    print("✅ Tables created successfully!")
