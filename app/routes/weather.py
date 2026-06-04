from flask import Blueprint, jsonify

bp = Blueprint('weather', __name__)


@bp.route('/weather')
def weather():
    return jsonify({
        "status": "ok",
        "message": "Weather endpoint not implemented in this snapshot"
    })

