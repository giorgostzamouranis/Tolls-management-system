from flask import Blueprint, render_template
from flask_login import login_required, current_user

operator_bp = Blueprint('operator', __name__)

@operator_bp.route('/operator/dashboard')
@login_required
def dashboard():
    if current_user.role != 'operator':
        return "Unauthorized", 403
    return render_template('operator_dashboard.html')
