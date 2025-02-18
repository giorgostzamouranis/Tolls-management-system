from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, flash
import base64
from common import get_db_connection  # Ensure your DB connection works correctly

auth_bp = Blueprint('auth', __name__)

# -------------------------------------------------
# API/Teacher Testing Endpoint: Always returns JSON
# -------------------------------------------------
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /login
    - Expects application/x-www-form-urlencoded data with parameters:
         • username
         • password
    - On successful authentication, returns a JSON object with the token:
         { "token": "<FOO>" }
    - On failure, returns a JSON error.
    
    (This endpoint is intended for teacher testing and API/CLI calls.)
    """
    # Allow charset variations by checking the mimetype
    if request.mimetype != 'application/x-www-form-urlencoded':
        return jsonify({"status": "failed", "error": "Content-Type must be application/x-www-form-urlencoded"}), 400

    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify({"status": "failed", "error": "Missing username or password"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        if user and user['password'] == password:
            # For demonstration, we use the user_id as the token.
            token = str(user['user_id'])
            session['user_token'] = token
            session['username'] = user['username']
            session['role'] = user['role']
            return jsonify({"token": token}), 200
        else:
            return jsonify({"status": "failed", "error": "Invalid username or password"}), 401
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()


# -------------------------------------------------
# Website HTML Login Page Endpoint: Renders HTML
# -------------------------------------------------
@auth_bp.route('/login_page', methods=['GET', 'POST'])
def login_page():
    """
    GET /login_page:
      - Renders the HTML login page.
    POST /login_page:
      - Processes the login form submitted from the browser.
      - On successful authentication, redirects to the home page.
      - On failure, re-renders the login page with an error message.
    """
    if request.method == 'GET':
        if 'user_token' in session:
            flash('You are already logged in.', 'info')
            return redirect(url_for('home.home'))
        return render_template('login.html')
    else:  # POST method from HTML form
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Missing username or password', 'error')
            return render_template('login.html')

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            if user and user['password'] == password:
                token = str(user['user_id'])
                session['user_token'] = token
                session['username'] = user['username']
                session['role'] = user['role']
                flash('Login successful', 'success')
                return redirect(url_for('home.home'))
            else:
                flash('Invalid username or password', 'error')
                return render_template('login.html')
        except Exception as e:
            flash(f"An error occurred: {str(e)}", 'error')
            return render_template('login.html')
        finally:
            if 'conn' in locals():
                conn.close()


# -------------------------------------------------
# Logout Endpoint: Used by both website and API
# -------------------------------------------------
@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    POST /logout
    - For API/CLI (if ?cli=true is provided): returns an empty response with status code 200,
      or a JSON error if something goes wrong.
    - For website usage (no cli parameter):
         • Expects the user's token to be either in the header X-OBSERVATORY-AUTH or in the session.
         • On success, clears the session, flashes a logout message, and redirects to the login page.
    """
    token = request.headers.get('X-OBSERVATORY-AUTH') or session.get('user_token')
    
    # Check for missing token
    if not token:
        if request.args.get('cli', 'false').lower() == 'true':
            return jsonify({"status": "failed", "error": "Missing token"}), 400
        else:
            flash("Missing token. You are not logged in.", "error")
            return redirect(url_for('auth.login_page'))
    
    # Check if token is valid
    if session.get('user_token') != token:
        if request.args.get('cli', 'false').lower() == 'true':
            return jsonify({"status": "failed", "error": "Invalid token"}), 401
        else:
            flash("Invalid token", "error")
            return redirect(url_for('auth.login_page'))
    
    # Clear the session
    session.clear()
    
    # Return appropriate response based on the caller
    if request.args.get('cli', 'false').lower() == 'true':
         return '', 200
    else:
         flash("You have been logged out.", "success")
         return redirect(url_for('auth.login_page'))



# -------------------------------------------------
# WhoAmI Endpoint (unchanged)
# -------------------------------------------------
@auth_bp.route('/auth/whoami', methods=['GET'])
def whoami():
    """
    GET /auth/whoami
    Returns information about the logged-in user.
    If no session exists, attempts to authenticate using the X-OBSERVATORY-AUTH header.
    """
    if 'user_token' not in session:
        auth_header = request.headers.get('X-OBSERVATORY-AUTH')
        if auth_header:
            try:
                decoded_credentials = base64.b64decode(auth_header).decode('utf-8')
                username, password = decoded_credentials.split(':', 1)
            except Exception as e:
                return jsonify({"status": "failed", "error": "Invalid authentication header format"}), 400

            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                query = "SELECT * FROM users WHERE username = %s"
                cursor.execute(query, (username,))
                user = cursor.fetchone()
                if user and user['password'] == password:
                    return jsonify({
                        "status": "success",
                        "user_id": user['user_id'],
                        "username": user['username'],
                        "role": user['role']
                    }), 200
                else:
                    return jsonify({"status": "failed", "error": "Invalid credentials"}), 401
            except Exception as e:
                return jsonify({"status": "failed", "error": str(e)}), 500
            finally:
                if 'conn' in locals():
                    conn.close()
        else:
            return jsonify({"status": "failed", "error": "Not logged in"}), 401

    return jsonify({
        "status": "success",
        "user_id": session.get('user_token'),
        "username": session.get('username'),
        "role": session.get('role')
    }), 200
