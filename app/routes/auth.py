from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.models import User, db

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
        role = request.form.get('role', 'user')  # default user

        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(username=username, email=email, role=role)
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
            # Save user info in session
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role

            flash(f'Welcome, {user.username}!', 'success')
            # Redirect to home page instead of separate dashboard
            return redirect(url_for('main.home'))

        flash('Invalid login credentials', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('login.html')


# -----------------------
# Logout Route
# -----------------------
@bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", 'success')
    return redirect(url_for('main.home'))
