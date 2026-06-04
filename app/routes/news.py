from flask import Blueprint, jsonify

bp = Blueprint('news', __name__)


@bp.route('/news')
def news():
    return jsonify({
        "status": "ok",
        "message": "News endpoint not implemented in this snapshot"
    })

