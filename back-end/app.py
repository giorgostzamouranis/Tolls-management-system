from flask import Flask, session, redirect, url_for, request
from routes.home import home_bp
from routes.debts import debts_bp
from routes.statistics import stats_bp
from routes.charts import charts_bp
from routes.admin import admin_bp
from routes.toll_station_passes_site import toll_station_passes_site_bp
from routes.pass_analysis_site import pass_analysis_site_bp
from routes.passescost_site import passes_cost_site_bp
from routes.passescost_cli import passes_cost_cli_bp
from routes.chargesby_site import charges_by_site_bp
from routes.chargesby_cli import charges_by_cli_bp
from routes.auth import auth_bp
from routes.toll_station_passes_cli import toll_station_passes_cli_bp
from routes.healthcheck_cli import healthcheck_cli_bp
from routes.resetpasses_cli import resetpasses_cli_bp
from routes.resetstations_cli import resetstations_cli_bp
from routes.pass_analysis_cli import pass_analysis_cli_bp

app = Flask(
    __name__,
    template_folder='../front-end/templates',
    static_folder='../front-end/static'
)
app.secret_key = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['TESTING'] = True


# ----------------------------------
# Register Blueprints under /api
# ----------------------------------
app.register_blueprint(passes_cost_cli_bp,      url_prefix='/api')
app.register_blueprint(pass_analysis_cli_bp,    url_prefix='/api')
app.register_blueprint(resetpasses_cli_bp,      url_prefix='/api')
app.register_blueprint(toll_station_passes_cli_bp, url_prefix='/api')
app.register_blueprint(healthcheck_cli_bp,      url_prefix='/api')
app.register_blueprint(home_bp,                 url_prefix='/api')
app.register_blueprint(debts_bp,                url_prefix='/api')
app.register_blueprint(stats_bp,                url_prefix='/api')
app.register_blueprint(charts_bp,               url_prefix='/api')
app.register_blueprint(pass_analysis_site_bp,   url_prefix='/api')
app.register_blueprint(admin_bp,                url_prefix='/api')
app.register_blueprint(toll_station_passes_site_bp, url_prefix='/api')
app.register_blueprint(passes_cost_site_bp,     url_prefix='/api')
app.register_blueprint(charges_by_site_bp,      url_prefix='/api')
app.register_blueprint(charges_by_cli_bp,       url_prefix='/api')
app.register_blueprint(auth_bp,                 url_prefix='/api')
app.register_blueprint(resetstations_cli_bp,    url_prefix='/api')



@app.before_request
def require_login():
    # Προσαρμόστε το όνομα του endpoint, αν αλλάξει λόγω url_prefix
    if not session.get('user_token') and request.endpoint not in [
        'admin.usermod', 'auth.login', 'auth.login_page',
        'resetpasses_cli.resetpasses_cli', 'static',
        'passanalysis_cli.passanalysis_cli', 'admin.list_users',
        'admin.add_passes', 
    ]:
        return redirect(url_for('auth.login_page'))

if __name__ == '__main__':
    # Χρήση adhoc SSL για δοκιμές (https://...:9115/api).
    # Σε παραγωγικό περιβάλλον βάλτε έγκυρο πιστοποιητικό.
    app.run(host='0.0.0.0', port=9115, debug=True)
