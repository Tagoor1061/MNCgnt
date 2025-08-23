from flask import Blueprint, render_template, session, redirect, url_for
from flask_login import current_user

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    if current_user.is_authenticated:
      return render_template('home.html',dashboard=True,user=current_user)
    else:
      return render_template('home.html',dashboard=False)

@bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') != "user":
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html')

@bp.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != "admin":
        return redirect(url_for('auth.login'))
    return render_template('admin_dashboard.html')
