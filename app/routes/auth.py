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
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        role = 'user'  # Always set role to user, preventing admin registration

        clean_phone = ''.join(c for c in phone if c.isdigit())

        error = None
        if not username or len(username) < 3:
            error = "Username must be at least 3 characters long."
        elif not email or '@' not in email:
            error = "Please enter a valid email address."
        elif not phone or len(clean_phone) < 10:
            error = "Please enter a valid 10-digit mobile number."
        elif not password or len(password) < 6:
            error = "Password must be at least 6 characters long."
        elif User.query.filter_by(username=username).first():
            error = f"The username '{username}' is already taken. Please choose another username."
        elif User.query.filter_by(email=email).first():
            error = f"The email '{email}' is already registered. Please login or use a different email."

        if error:
            flash(error, 'danger')
            return render_template('register.html', error=error, username=username, email=email, phone=phone)

        new_user = User(username=username, email=email, phone=clean_phone, role=role) # type: ignore
        new_user.set_password(password)
        db.session.add(new_user)  # type: ignore
        db.session.commit()       # type: ignore

        flash('Registration successful! Please login with your credentials.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# -----------------------
# Login Route
# -----------------------
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_input = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        error = None
        if not email_input:
            error = "Please enter your registered email address or username."
        elif not password:
            error = "Please enter your password."
        else:
            user = User.query.filter((User.email == email_input) | (User.username == email_input)).first()
            if not user:
                error = f"No account found matching '{email_input}'. Please check your details or register."
            elif not user.check_password(password):
                error = f"Incorrect password entered for '{email_input}'. Please try again."

        if error:
            flash(error, 'danger')
            return render_template('login.html', error=error, email=email_input)

        # Successful login
        user = User.query.filter((User.email == email_input) | (User.username == email_input)).first()
        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()
        flash(f'Welcome, {user.username}!', 'success')
        if user.role == 'admin':
            flash(f'Welcome, {user.username}! You are logged in as Admin.', 'success')
            return redirect(url_for('main.admin_dashboard'))
        else:
            return redirect(url_for('main.dashboard'))

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
