

from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models import Issue # type: ignore

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    if current_user.is_authenticated:
        if getattr(current_user, 'role', None) == 'admin':
            # Prepare issues and issues_json for admin dashboard
            from app.models import Issue
            issues = Issue.query.all()
            issues_dicts = []
            for issue in issues:
                issues_dicts.append({
                    'id': issue.id,
                    'description': issue.description,
                    'status': issue.status,
                    'latitude': issue.latitude,
                    'longitude': issue.longitude,
                    'user': {'id': issue.user.id, 'username': issue.user.username} if issue.user else {},
                    'user_id': issue.user_id,
                    'timestamp': issue.timestamp.strftime('%Y-%m-%d %H:%M') if issue.timestamp else ''
                })
            return render_template('home.html', dashboard=True, user=current_user, is_admin=True, issues=issues, issues_json=issues_dicts)
        else:
            return render_template('home.html', dashboard=True, user=current_user, is_admin=False)
    else:
        return render_template('home.html', dashboard=False, is_admin=False)



@bp.route('/dashboard')
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    if getattr(current_user, 'role', None) == 'admin':
        from app.models import Issue
        issues = Issue.query.all()
        issues_dicts = []
        for issue in issues:
            issues_dicts.append({
                'id': issue.id,
                'description': issue.description,
                'status': issue.status,
                'latitude': issue.latitude,
                'longitude': issue.longitude,
                'user': {'id': issue.user.id, 'username': issue.user.username} if issue.user else {},
                'user_id': issue.user_id,
                'timestamp': issue.timestamp.strftime('%Y-%m-%d %H:%M') if issue.timestamp else ''
            })
        return render_template('admin_dashboard.html', issues=issues, issues_json=issues_dicts)
    else:
        return render_template('dashboard.html')

@bp.route('/select_location')
@login_required
def select_location():
    return render_template('select_location.html')


@bp.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_authenticated or getattr(current_user, 'role', None) != 'admin':
        return redirect(url_for('auth.login'))
    issues = Issue.query.all()
    # Convert issues to dicts for JSON serialization in template
    issues_dicts = []
    for issue in issues:
        issues_dicts.append({
            'id': issue.id,
            'description': issue.description,
            'status': issue.status,
            'latitude': issue.latitude,
            'longitude': issue.longitude,
            'user': {'id': issue.user.id, 'username': issue.user.username} if issue.user else {},
            'user_id': issue.user_id,
            'timestamp': issue.timestamp.strftime('%Y-%m-%d %H:%M') if issue.timestamp else ''
        })
    return render_template('admin_dashboard.html', issues=issues, issues_json=issues_dicts)
@bp.route('/remove_issue/<int:issue_id>', methods=['POST'])
@login_required
def remove_issue(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    if current_user.role == 'admin' or current_user.id == issue.user_id:
        db.session.delete(issue)
        db.session.commit()
        flash('Issue removed.', 'success')
    else:
        flash('You do not have permission to remove this issue.', 'danger')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/report_issue', methods=['POST'])
@login_required
def report_issue():
    description = request.form.get('issue')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    if not (description and latitude and longitude):
        flash('Please provide all required information, including location.', 'danger')
        return redirect(url_for('main.dashboard'))
    try:
        issue = Issue(
            description=description,
            latitude=float(latitude),
            longitude=float(longitude),
            user_id=current_user.id
        )
        db.session.add(issue) # type: ignore
        db.session.commit() # type: ignore
        flash('Your issue has been reported. Thank you!', 'success')
    except Exception as e:
        db.session.rollback() # type: ignore
        flash('Error reporting issue: ' + str(e), 'danger')
    return redirect(url_for('main.dashboard'))