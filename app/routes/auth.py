from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.models import User, db
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')

# -----------------------
# Register Route
# -----------------------
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = 'user'  # Always set role to user, preventing admin registration

        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(username=username, email=email, role=role) # type: ignore
        new_user.set_password(password)
        db.session.add(new_user)  # type: ignore
        db.session.commit()       # type: ignore

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# -----------------------
# Login Route
# -----------------------
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()



        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash(f'Welcome, {user.username}!', 'success')
            if user.role == 'admin':
                flash(f'Welcome, {user.username}! You are logged in as Admin.', 'success')
                return redirect(url_for('main.home'))
            else:
                return redirect(url_for('main.dashboard'))

        flash('Invalid login credentials', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('login.html')


# -----------------------
# Logout Route
# -----------------------
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", 'success')
    return redirect(url_for('main.home'))
