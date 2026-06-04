from app import db, create_app
from app.models import User

# Create app instance
app = create_app()

# Create tables inside app context
with app.app_context():
    db.create_all()
    print("✅ Tables created successfully!")

    # Insert default admin users if they don't exist
    admin1_email = 'tagoorncc10@gmail.com'
    admin2_email = 'archanasenapathi63@gmail.com'

    if not User.query.filter_by(email=admin1_email).first():
        admin1 = User(username='admin1', email=admin1_email, role='admin')
        admin1.set_password('2007')
        db.session.add(admin1)
        print(f"✅ Admin user {admin1_email} created.")

    if not User.query.filter_by(email=admin2_email).first():
        admin2 = User(username='admin2', email=admin2_email, role='admin')
        admin2.set_password('44')
        db.session.add(admin2)
        print(f"✅ Admin user {admin2_email} created.")

    db.session.commit()
    print("✅ Default admin users inserted successfully!")
