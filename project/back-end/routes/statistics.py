# routes/statistics.py
from flask import Blueprint, render_template

stats_bp = Blueprint('stats', __name__, template_folder='templates')

@stats_bp.route('/statistics', methods=['GET'])
def statistics():
    """
    Renders the common Statistics Dashboard page.
    """
    return render_template('statistics.html')
