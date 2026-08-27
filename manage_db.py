import sys
import shutil
from datetime import datetime
from app import create_app, db
from app.models import User, Issue, UserNotification, News, ZoneMarking, PushSubscription

app = create_app()

def print_help():
    print("""
==================================================
  JAL SURAKSHA - DATABASE MANAGEMENT CLI
==================================================

Usage: python manage_db.py [command]

Commands:
  status                        Display database stats (user and issue counts)
  list-users                    List all registered users and admins
  list-issues                   List all reported municipal issues
  add-admin <usr> <email> <pwd> Create a new Admin account
  delete-user <usr_or_email>    Delete a specific user account
  clear-users                   Delete all regular users (keeps Admin accounts)
  backup                        Create a timestamped backup of the database
  reset                         Reset entire DB and seed fresh admin accounts

==================================================
""")

def show_status():
    with app.app_context():
        total_users = User.query.count()
        admins = User.query.filter_by(role='admin').count()
        reg_users = User.query.filter(User.role != 'admin').count()
        issues = Issue.query.count()
        notifications = UserNotification.query.count()

        print("\n--- DATABASE STATUS ---")
        print(f"Total Users: {total_users} (Admins: {admins} | Citizens: {reg_users})")
        print(f"Reported Issues: {issues}")
        print(f"Notifications Recorded: {notifications}")
        print("-----------------------\n")

def list_users():
    with app.app_context():
        users = User.query.all()
        print(f"\n--- REGISTERED ACCOUNTS ({len(users)}) ---")
        for u in users:
            print(f"ID: {u.id:2d} | Role: {u.role:5s} | Username: {u.username:15s} | Email: {u.email:30s} | Phone: {u.phone or 'N/A'}")
        print("------------------------------------------\n")

def list_issues():
    with app.app_context():
        issues = Issue.query.all()
        print(f"\n--- REPORTED ISSUES ({len(issues)}) ---")
        for i in issues:
            usr = i.user.username if i.user else 'Unknown'
            print(f"ID: {i.id:2d} | Status: {i.status:8s} | User: {usr:12s} | Location: ({i.latitude}, {i.longitude}) | Desc: {i.description[:40]}")
        print("----------------------------------------\n")

def add_admin(username, email, password):
    with app.app_context():
        existing = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing:
            print(f"[ERROR] User with username '{username}' or email '{email}' already exists!")
            return
        admin = User(username=username, email=email, role='admin')
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"[SUCCESS] Admin account '{username}' ({email}) created successfully!")

def delete_user(identifier):
    with app.app_context():
        user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()
        if not user:
            print(f"[ERROR] User '{identifier}' not found.")
            return

        Issue.query.filter_by(user_id=user.id).delete()
        UserNotification.query.filter_by(user_id=user.id).delete()
        PushSubscription.query.filter_by(user_id=user.id).delete()

        db.session.delete(user)
        db.session.commit()
        print(f"[SUCCESS] User '{identifier}' and associated records deleted.")

def clear_users():
    with app.app_context():
        users = User.query.filter(User.role != 'admin').all()
        uids = [u.id for u in users]
        if uids:
            Issue.query.filter(Issue.user_id.in_(uids)).delete(synchronize_session=False)
            UserNotification.query.filter(UserNotification.user_id.in_(uids)).delete(synchronize_session=False)
            PushSubscription.query.filter(PushSubscription.user_id.in_(uids)).delete(synchronize_session=False)

        for u in users:
            db.session.delete(u)
        db.session.commit()
        print(f"[SUCCESS] Cleared {len(users)} regular user account(s).")

def backup_db():
    import os
    db_file = os.path.join('instance', 'app.db')
    if not os.path.exists(db_file):
        db_file = 'app.db'
    if not os.path.exists(db_file):
        print("[ERROR] Database file app.db not found.")
        return

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backup_app_{timestamp}.db"
    shutil.copy(db_file, backup_file)
    print(f"[SUCCESS] Database backup created: {backup_file}")

def reset_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        from app.routes.init_db import seed_admin_users
        seed_admin_users()
        print("[SUCCESS] Database completely reset and re-seeded with admin accounts!")

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] in ['-h', '--help', 'help']:
        print_help()
    elif args[0] == 'status':
        show_status()
    elif args[0] == 'list-users':
        list_users()
    elif args[0] == 'list-issues':
        list_issues()
    elif args[0] == 'add-admin' and len(args) == 4:
        add_admin(args[1], args[2], args[3])
    elif args[0] == 'delete-user' and len(args) == 2:
        delete_user(args[1])
    elif args[0] == 'clear-users':
        clear_users()
    elif args[0] == 'backup':
        backup_db()
    elif args[0] == 'reset':
        reset_db()
    else:
        print("[ERROR] Unknown command. Run 'python manage_db.py' to view command options.")
