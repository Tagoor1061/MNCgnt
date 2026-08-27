import sys
import io

# Force stdout encoding to utf-8 for Windows compatibility
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
Database Inspector Utility
Run this script to inspect the contents of your SQLite database (instance/guntur.db).

Usage:
  python check_db.py
  or
  .\\venv\\Scripts\\python.exe check_db.py
"""

from app import create_app, db
from app.models import User, Issue, News, ZoneMarking, PushSubscription

app = create_app()

with app.app_context():
    print("=" * 65)
    print(" 📊 GUNTUR MUNICIPAL CORPORATION - DATABASE SUMMARY")
    print("=" * 65)

    # 1. Users
    users = User.query.all()
    print(f"\n👤 USERS ({len(users)} registered):")
    print("-" * 65)
    print(f"{'ID':<5} | {'Username':<18} | {'Email':<28} | {'Role':<8}")
    print("-" * 65)
    for u in users:
        print(f"{u.id:<5} | {u.username:<18} | {u.email:<28} | {u.role:<8}")

    # 2. Issues
    issues = Issue.query.all()
    print(f"\n📢 REPORTED ISSUES ({len(issues)} total):")
    print("-" * 65)
    print(f"{'ID':<5} | {'Status':<10} | {'Reported By':<15} | {'Description':<28}")
    print("-" * 65)
    for i in issues:
        username = i.user.username if i.user else "Unknown"
        desc = (i.description[:25] + "...") if len(i.description) > 28 else i.description
        print(f"{i.id:<5} | {i.status:<10} | {username:<15} | {desc:<28}")

    # 3. Zone Markings
    markings = ZoneMarking.query.all()
    print(f"\n🗺️ SAFETY ZONE MARKINGS ({len(markings)} total):")
    print("-" * 65)
    print(f"{'ID':<5} | {'Title':<25} | {'Risk Level':<12} | {'Shape':<10}")
    print("-" * 65)
    for m in markings:
        print(f"{m.id:<5} | {m.title:<25} | {m.risk_level:<12} | {m.shape_type:<10}")

    # 4. News
    news = News.query.all()
    print(f"\n📰 NEWS ARTICLES ({len(news)} total):")
    print("-" * 65)
    for n in news:
        print(f"[{n.id}] {n.title} (Category: {n.category})")

    print("\n" + "=" * 65)
    print(" ✅ Database File Location: instance/guntur.db")
    print("=" * 65)
