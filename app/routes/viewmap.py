from flask import Blueprint, render_template

bp = Blueprint('viewmap', __name__)


@bp.route('/viewmap')
def view_map():
    # Uses endpoint name expected by templates: viewmap.view_map
    return render_template('viewmap.html')


