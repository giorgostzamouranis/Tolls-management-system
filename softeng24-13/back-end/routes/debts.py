from flask import Blueprint, render_template
from common import get_debts

debts_bp = Blueprint('debts', __name__)

@debts_bp.route('/debts')
def debts():
    debts_data = get_debts()
    return render_template('debts.html', debts=debts_data)
