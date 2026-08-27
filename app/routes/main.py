

from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models import Issue # type: ignore

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    weather_summary = None
    try:
        from app.utils.weather_data import WeatherDataProcessor
        weather_summary = WeatherDataProcessor.get_weather_summary()
    except Exception as exc:
        print(f"Error fetching weather for home page: {exc}")

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
            return render_template('home.html', dashboard=True, user=current_user, is_admin=True, issues=issues, issues_json=issues_dicts, weather=weather_summary)
        else:
            return render_template('home.html', dashboard=True, user=current_user, is_admin=False, weather=weather_summary)
    else:
        return render_template('home.html', dashboard=False, is_admin=False, weather=weather_summary)



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
                'user': {'id': issue.user.id, 'username': issue.user.username, 'phone': issue.user.phone, 'email': issue.user.email} if issue.user else {},
                'user_id': issue.user_id,
                'timestamp': issue.timestamp.strftime('%Y-%m-%d %H:%M') if issue.timestamp else ''
            })
        return render_template('admin_dashboard.html', issues=issues, issues_json=issues_dicts)
    else:
        from app.models import UserNotification
        notifications = UserNotification.query.filter_by(user_id=current_user.id).order_by(UserNotification.created_at.desc()).all()
        return render_template('dashboard.html', notifications=notifications)

@bp.route('/select_location')
@login_required
def select_location():
    return redirect(url_for('main.dashboard'))


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
@bp.route('/clear_issue/<int:issue_id>', methods=['POST'])
@bp.route('/remove_issue/<int:issue_id>', methods=['POST'])
@login_required
def clear_issue(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    if current_user.role == 'admin' or current_user.id == issue.user_id:
        user_email = issue.user.email if issue.user else None
        user_phone = issue.user.phone if issue.user else None
        user_name = issue.user.username if issue.user else 'User'
        reported_date = issue.timestamp.strftime('%Y-%m-%d %H:%M') if issue.timestamp else ''

        # 1. Create in-database notification for the user
        if issue.user_id:
            try:
                from app.models import UserNotification
                notif = UserNotification(
                    user_id=issue.user_id,
                    title=f"Issue #{issue.id} CLEARED & RESOLVED",
                    message=f"Great news! Your reported issue #{issue.id} ('{issue.description}') at coordinates ({issue.latitude}, {issue.longitude}) has been inspected and CLEARED by the Guntur Municipal Corporation."
                )
                db.session.add(notif)
            except Exception as exc:
                print(f"Error creating in-app notification: {exc}")

        # 2. Send clear confirmation email
        if user_email:
            from app.utils.email_service import send_issue_cleared_email
            try:
                send_issue_cleared_email(
                    recipient_email=user_email,
                    recipient_name=user_name,
                    issue_id=issue.id,
                    issue_description=issue.description,
                    latitude=issue.latitude,
                    longitude=issue.longitude,
                    reported_date=reported_date
                )
            except Exception as exc:
                print(f"Error sending email: {exc}")

        # 3. Send clear confirmation SMS to registered mobile number
        if user_phone:
            from app.utils.email_service import send_issue_cleared_sms
            try:
                send_issue_cleared_sms(
                    phone_number=user_phone,
                    issue_id=issue.id,
                    issue_description=issue.description
                )
            except Exception as exc:
                print(f"Error sending SMS: {exc}")

        # 4. Trigger Web Push Alert if subscribed
        try:
            from app.routes.push import send_push_alert
            send_push_alert(
                f"Issue #{issue.id} Cleared",
                f"Your reported issue '{issue.description[:40]}' was CLEARED by Municipal Admin."
            )
        except Exception:
            pass

        db.session.delete(issue)
        db.session.commit()

        msg = f'Issue #{issue_id} cleared!'
        if user_email:
            msg += f' Email sent to {user_email}.'
        if user_phone:
            msg += f' SMS sent to {user_phone}.'
        flash(msg, 'success')
    else:
        flash('You do not have permission to clear this issue.', 'danger')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/natural_disasters')
def natural_disasters():
    weather_summary = None
    try:
        from app.utils.weather_data import WeatherDataProcessor
        weather_summary = WeatherDataProcessor.get_weather_summary()
    except Exception as exc:
        print(f"Error fetching weather for natural disasters page: {exc}")
    return render_template('natural_disasters.html', weather=weather_summary)


@bp.route('/disasters/cyclone')
def disaster_cyclone():
    weather_summary = None
    try:
        from app.utils.weather_data import WeatherDataProcessor
        weather_summary = WeatherDataProcessor.get_weather_summary()
    except Exception:
        pass
    return render_template('disasters/cyclone.html', weather=weather_summary)


@bp.route('/disasters/tsunami')
def disaster_tsunami():
    return render_template('disasters/tsunami.html')


@bp.route('/disasters/floods')
def disaster_floods():
    weather_summary = None
    try:
        from app.utils.weather_data import WeatherDataProcessor
        weather_summary = WeatherDataProcessor.get_weather_summary()
    except Exception:
        pass
    return render_template('disasters/floods.html', weather=weather_summary)


@bp.route('/disasters/earthquakes')
def disaster_earthquakes():
    return render_template('disasters/earthquakes.html')


@bp.route('/disasters/winds')
def disaster_winds():
    weather_summary = None
    try:
        from app.utils.weather_data import WeatherDataProcessor
        weather_summary = WeatherDataProcessor.get_weather_summary()
    except Exception:
        pass
    return render_template('disasters/winds.html', weather=weather_summary)


@bp.route('/disasters/rainfall')
def disaster_rainfall():
    weather_summary = None
    try:
        from app.utils.weather_data import WeatherDataProcessor
        weather_summary = WeatherDataProcessor.get_weather_summary()
    except Exception:
        pass
    return render_template('disasters/rainfall.html', weather=weather_summary)


@bp.route('/disasters/landslides')
def disaster_landslides():
    weather_summary = None
    try:
        from app.utils.weather_data import WeatherDataProcessor
        weather_summary = WeatherDataProcessor.get_weather_summary()
    except Exception:
        pass
    return render_template('disasters/landslides.html', weather=weather_summary)


@bp.route('/issue_reporting')
def issue_reporting_page():
    return render_template('issue_reporting.html')


@bp.route('/learn')
def learn():
    """Citizen education hub: disaster awareness videos + quizzes."""
    return render_template('learn.html')


@bp.route('/report_issue', methods=['POST'])
@login_required
def report_issue():
    description = (request.form.get('issue') or '').strip()
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    redirect_url = request.referrer or url_for('main.dashboard')
    if not (description and latitude and longitude):
        flash('Please provide all required information, including location.', 'danger')
        return redirect(redirect_url)
    try:
        lat = float(latitude)
        lng = float(longitude)
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValueError('Latitude or longitude is outside the valid range.')

        issue = Issue(
            description=description,
            latitude=lat,
            longitude=lng,
            user_id=current_user.id
        )
        db.session.add(issue) # type: ignore
        db.session.commit() # type: ignore
        flash('Your issue has been reported. Thank you!', 'success')
    except Exception as e:
        db.session.rollback() # type: ignore
        flash('Error reporting issue: ' + str(e), 'danger')
    return redirect(redirect_url)

