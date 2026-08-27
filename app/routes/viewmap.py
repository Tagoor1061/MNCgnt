import json
from flask import Blueprint, render_template, jsonify, request
from flask_login import current_user
from app import db
from app.models import ZoneMarking

bp = Blueprint('viewmap', __name__)

@bp.route('/viewmap')
def view_map():
    return render_template('viewmap.html')

@bp.route('/api/markings', methods=['GET'])
def get_markings():
    markings = ZoneMarking.query.all()
    return jsonify({
        'status': 'success',
        'markings': [m.to_dict() for m in markings]
    })

@bp.route('/api/markings', methods=['POST'])
def save_markings():
    if not current_user.is_authenticated or getattr(current_user, 'role', None) != 'admin':
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403

    data = request.get_json(silent=True) or {}
    markings_list = data.get('markings', [])
    if not isinstance(markings_list, list):
        markings_list = [data]

    saved_items = []
    for item in markings_list:
        shape_type = item.get('shape_type', 'pencil')
        risk_level = item.get('risk_level', 'safe')
        color = item.get('color', 'green')
        title = item.get('title') or f"{risk_level.capitalize()} Zone ({shape_type.capitalize()})"
        geojson_data = item.get('geojson_data', {})

        marking = ZoneMarking(
            title=title,
            risk_level=risk_level,
            color=color,
            shape_type=shape_type,
            geojson_data=json.dumps(geojson_data),
            created_by_id=current_user.id
        )
        db.session.add(marking)
        saved_items.append(marking)

    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': f'Saved {len(saved_items)} marking(s) successfully.',
        'markings': [m.to_dict() for m in saved_items]
    })

@bp.route('/api/markings/<int:marking_id>', methods=['DELETE'])
def delete_marking(marking_id):
    if not current_user.is_authenticated or getattr(current_user, 'role', None) != 'admin':
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403

    marking = ZoneMarking.query.get(marking_id)
    if not marking:
        return jsonify({'status': 'error', 'message': 'Marking not found'}), 404

    db.session.delete(marking)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Marking deleted successfully'})

@bp.route('/api/markings/clear', methods=['DELETE', 'POST'])
def clear_markings():
    if not current_user.is_authenticated or getattr(current_user, 'role', None) != 'admin':
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403

    ZoneMarking.query.delete()
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'All markings cleared successfully'})


