from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from database.db import get_db, get_all_periods, get_period, get_latest_period
from modules.metrics import compute_metrics, compute_evolution
from modules.reconciler import compute_reconciliation

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
def dashboard():
    conn      = get_db()
    account_id = request.args.get('account', 1, type=int)
    periods   = get_all_periods(conn, account_id)

    try:
        period_id = int(request.args.get('period', 0))
    except (ValueError, TypeError):
        period_id = 0

    current = None
    if period_id:
        current = get_period(conn, period_id)
        # Make sure the period belongs to the current account
        if current and current['account_id'] != account_id:
            current = None
    if not current:
        current = get_latest_period(conn, account_id)

    conn.close()

    if not current:
        return redirect(url_for('upload.upload_form', account=account_id))

    return render_template('dashboard.html', periods=periods, current=current,
                           current_account_id=account_id)


@dashboard_bp.route('/api/metrics/<int:period_id>')
def api_metrics(period_id):
    conn = get_db()
    try:
        filters = _extract_filters(request.args)
        data    = compute_metrics(period_id, conn, filters)
        if not data:
            return jsonify({'error': 'Período no encontrado'}), 404

        period = get_period(conn, period_id)
        recon  = compute_reconciliation(period, conn)
        data['reconciliation'] = recon

        companion_tipo = 'caja' if period['tipo'] == 'banco' else 'banco'
        companion = conn.execute(
            """SELECT id FROM periods
               WHERE account_id=? AND tipo=? AND date_from=? AND date_to=?
               ORDER BY imported_at DESC LIMIT 1""",
            [period['account_id'], companion_tipo,
             period['date_from'], period['date_to']],
        ).fetchone()

        if companion:
            comp_period = get_period(conn, companion['id'])
            data['reconciliation_companion'] = compute_reconciliation(comp_period, conn)
        else:
            data['reconciliation_companion'] = None

        return jsonify(data)
    finally:
        conn.close()


@dashboard_bp.route('/api/evolution')
def api_evolution():
    account_id = request.args.get('account', 1, type=int)
    conn = get_db()
    try:
        return jsonify(compute_evolution(conn, account_id))
    finally:
        conn.close()


@dashboard_bp.route('/api/periods')
def api_periods():
    account_id = request.args.get('account', 1, type=int)
    conn = get_db()
    try:
        rows = get_all_periods(conn, account_id)
        return jsonify([dict(zip(p.keys(), tuple(p))) for p in rows])
    finally:
        conn.close()


def _extract_filters(args):
    cats_raw   = args.get('categories', '').strip()
    categories = [c.strip() for c in cats_raw.split(',') if c.strip()] if cats_raw else None
    min_imp    = args.get('min_importe')
    max_imp    = args.get('max_importe')
    return {
        'date_from':   args.get('date_from') or None,
        'date_to':     args.get('date_to')   or None,
        'tipo_tx':     args.get('tipo_tx')   or None,
        'categories':  categories,
        'min_importe': float(min_imp) if min_imp else None,
        'max_importe': float(max_imp) if max_imp else None,
    }
