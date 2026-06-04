from flask import Blueprint, jsonify

bp = Blueprint('push', __name__)


@bp.route('/push')
def push():
    return jsonify({
        "status": "ok",
        "message": "Push endpoint not implemented in this snapshot"
    })

