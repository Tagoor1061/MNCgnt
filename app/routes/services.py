from flask import Blueprint, render_template

bp = Blueprint('services', __name__, url_prefix='/services')

@bp.route('')
@bp.route('/')
def services():
    return render_template('services.html')
