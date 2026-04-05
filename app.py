import os
import webbrowser
import threading

from flask import Flask, redirect, url_for, request, g

from config import SECRET_KEY, UPLOAD_FOLDER, MAX_CONTENT_LENGTH
from database.db import init_db, get_db, get_all_accounts
from routes.upload import upload_bp
from routes.dashboard import dashboard_bp
from routes.transactions import transactions_bp
from routes.rules import rules_bp
from routes.accounts import accounts_bp
from routes.facturas import facturas_bp
from routes.opciones import opciones_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    app.jinja_env.auto_reload = True  # reload templates on change without debug mode

    app.register_blueprint(upload_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(rules_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(facturas_bp)
    app.register_blueprint(opciones_bp)

    @app.route('/')
    def index():
        return redirect(url_for('dashboard.dashboard'))

    @app.context_processor
    def inject_accounts():
        """Make accounts + current_account available in every template."""
        # Skip for static files and API endpoints
        if request.path.startswith('/static') or request.path.startswith('/api'):
            return {}
        conn = get_db()
        accounts = get_all_accounts(conn)
        conn.close()
        accounts_list = [dict(zip(a.keys(), tuple(a))) for a in accounts]
        current_id    = request.args.get('account', 1, type=int)
        current       = next((a for a in accounts_list if a['id'] == current_id),
                             accounts_list[0] if accounts_list else None)
        return dict(all_accounts=accounts_list, current_account=current,
                    current_account_id=current_id)

    return app


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_db()
    app = create_app()

    def _open_browser():
        webbrowser.open('http://127.0.0.1:5000')

    threading.Timer(1.2, _open_browser).start()
    app.run(host='127.0.0.1', port=5000, debug=False)
