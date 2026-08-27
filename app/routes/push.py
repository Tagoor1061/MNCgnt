import json

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user

from app import db
from app.models import PushSubscription

bp = Blueprint('push', __name__)


@bp.route('/push')
def push():
    return jsonify({
        'status': 'ok',
        'configured': _push_configured(),
        'public_key': current_app.config.get('VAPID_PUBLIC_KEY', ''),
    })


@bp.route('/push/public-key')
def public_key():
    return jsonify({
        'status': 'ok',
        'public_key': current_app.config.get('VAPID_PUBLIC_KEY', ''),
        'configured': _push_configured(),
    })


@bp.route('/push/subscribe', methods=['POST'])
def subscribe():
    payload = request.get_json(silent=True) or {}
    keys = payload.get('keys') or {}
    endpoint = payload.get('endpoint')
    p256dh = keys.get('p256dh')
    auth = keys.get('auth')

    if not endpoint or not p256dh or not auth:
        return jsonify({'status': 'error', 'message': 'Invalid push subscription payload.'}), 400

    subscription = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if not subscription:
        subscription = PushSubscription(endpoint=endpoint, p256dh=p256dh, auth=auth)
        db.session.add(subscription)

    subscription.p256dh = p256dh
    subscription.auth = auth
    if current_user.is_authenticated:
        subscription.user_id = current_user.id

    db.session.commit()
    return jsonify({'status': 'ok', 'message': 'Push subscription saved.'})


@bp.route('/push/unsubscribe', methods=['POST'])
def unsubscribe():
    payload = request.get_json(silent=True) or {}
    endpoint = payload.get('endpoint')
    if not endpoint:
        return jsonify({'status': 'error', 'message': 'Missing endpoint.'}), 400

    subscription = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if subscription:
        db.session.delete(subscription)
        db.session.commit()

    return jsonify({'status': 'ok', 'message': 'Push subscription removed.'})


@bp.route('/push/test', methods=['POST'])
def test_push():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Admin access required.'}), 403

    result = send_push_alert('Guntur weather alert test', 'Push notifications are configured correctly.')
    return jsonify(result)


def send_push_alert(title, body):
    if not _push_configured():
        return {
            'status': 'error',
            'message': 'VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY must be set in .env.',
        }

    try:
        from pywebpush import WebPushException, webpush
    except Exception as exc:
        return {
            'status': 'error',
            'message': 'pywebpush dependencies are not installed correctly. Run pip install -r requirements.txt.',
            'detail': str(exc),
        }

    sent = 0
    failed = []
    subscriptions = PushSubscription.query.all()
    for subscription in subscriptions:
        payload = {
            'endpoint': subscription.endpoint,
            'keys': {
                'p256dh': subscription.p256dh,
                'auth': subscription.auth,
            },
        }
        try:
            webpush(
                subscription_info=payload,
                data=json.dumps({'title': title, 'body': body}),
                vapid_private_key=current_app.config['VAPID_PRIVATE_KEY'],
                vapid_claims=current_app.config['VAPID_CLAIMS'],
            )
            sent += 1
        except WebPushException as exc:
            failed.append({'endpoint': subscription.endpoint, 'error': str(exc)})

    return {'status': 'ok', 'sent': sent, 'failed': failed}


def _push_configured():
    return bool(current_app.config.get('VAPID_PUBLIC_KEY') and current_app.config.get('VAPID_PRIVATE_KEY'))

