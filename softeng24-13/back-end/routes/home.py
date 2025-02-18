from flask import Blueprint, render_template, session, redirect, url_for, flash

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    # Check if the user is logged in
    if 'user_token' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth.login_page'))

    # Render the home page
    return render_template('home.html', username=session.get('username'))
