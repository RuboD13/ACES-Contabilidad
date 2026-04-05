from flask import Blueprint, render_template, jsonify, request
from database.db import get_db

opciones_bp = Blueprint('opciones', __name__)


@opciones_bp.route('/opciones')
def opciones():
    return render_template('opciones.html')


@opciones_bp.route('/api/action_log')
def api_action_log():
    conn = get_db()
    try:
        account_id   = request.args.get('account', type=int)
        limit        = request.args.get('limit', 200, type=int)
        action_type  = request.args.get('type', '').strip()

        conditions = []
        params = []
        if account_id:
            conditions.append("account_id = ?")
            params.append(account_id)
        if action_type:
            # Support comma-separated list of types
            types = [t.strip() for t in action_type.split(',') if t.strip()]
            if types:
                ph = ','.join('?' * len(types))
                conditions.append(f"action_type IN ({ph})")
                params.extend(types)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)
        rows = conn.execute(
            f"SELECT * FROM action_log {where} ORDER BY created_at DESC LIMIT ?",
            params
        ).fetchall()
        return jsonify([dict(zip(r.keys(), tuple(r))) for r in rows])
    finally:
        conn.close()


@opciones_bp.route('/api/stats')
def api_stats():
    conn = get_db()
    try:
        account_id = request.args.get('account', type=int)
        if account_id:
            periods  = conn.execute("SELECT COUNT(*) FROM periods WHERE account_id=?", [account_id]).fetchone()[0]
            txs      = conn.execute("SELECT COUNT(*) FROM transactions t JOIN periods p ON t.period_id=p.id WHERE p.account_id=?", [account_id]).fetchone()[0]
            facturas = conn.execute("SELECT COUNT(*) FROM facturas WHERE account_id=?", [account_id]).fetchone()[0]
            tags     = conn.execute("SELECT COUNT(*) FROM tags WHERE account_id=?", [account_id]).fetchone()[0]
        else:
            periods  = conn.execute("SELECT COUNT(*) FROM periods").fetchone()[0]
            txs      = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
            facturas = conn.execute("SELECT COUNT(*) FROM facturas").fetchone()[0]
            tags     = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
        return jsonify({'periods': periods, 'transactions': txs, 'facturas': facturas, 'tags': tags})
    finally:
        conn.close()


@opciones_bp.route('/api/log_action', methods=['POST'])
def log_action():
    data = request.get_json(force=True) or {}
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO action_log (account_id, action_type, description, tx_id) VALUES (?,?,?,?)",
            (data.get('account_id', 1), data.get('action_type', 'other'),
             data.get('description', ''), data.get('tx_id'))
        )
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()
