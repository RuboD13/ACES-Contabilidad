from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from database.db import get_db

accounts_bp = Blueprint('accounts', __name__)

ACCOUNT_COLORS = [
    '#6366f1', '#10b981', '#f59e0b', '#f43f5e',
    '#06b6d4', '#8b5cf6', '#ec4899', '#84cc16',
]
ACCOUNT_ICONS = ['book', 'buildings', 'briefcase', 'house', 'wallet2',
                 'graph-up', 'currency-euro', 'archive']


@accounts_bp.route('/accounts')
def accounts():
    conn = get_db()
    rows = conn.execute("""
        SELECT a.*,
               COUNT(DISTINCT p.id)   AS period_count,
               COUNT(DISTINCT t.id)   AS tx_count
        FROM accounts a
        LEFT JOIN periods p ON p.account_id = a.id
        LEFT JOIN transactions t ON t.period_id = p.id
        GROUP BY a.id
        ORDER BY a.created_at
    """).fetchall()
    conn.close()
    return render_template('accounts.html',
                           account_list=rows,
                           colors=ACCOUNT_COLORS,
                           icons=ACCOUNT_ICONS)


@accounts_bp.route('/api/accounts', methods=['GET'])
def api_list():
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM accounts ORDER BY name").fetchall()
        return jsonify([dict(zip(r.keys(), tuple(r))) for r in rows])
    finally:
        conn.close()


@accounts_bp.route('/api/accounts', methods=['POST'])
def api_create():
    data = request.get_json(force=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'El nombre es obligatorio'}), 400

    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO accounts (name, description, color, icon, iban) VALUES (?, ?, ?, ?, ?)",
            (name, data.get('description', ''), data.get('color', '#6366f1'),
             data.get('icon', 'book'), data.get('iban', '')),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM accounts WHERE id=?", [cur.lastrowid]).fetchone()
        return jsonify(dict(zip(row.keys(), tuple(row)))), 201
    finally:
        conn.close()


@accounts_bp.route('/api/accounts/<int:account_id>', methods=['PUT'])
def api_update(account_id):
    data = request.get_json(force=True) or {}
    conn = get_db()
    try:
        allowed = {'name', 'description', 'color', 'icon', 'iban'}
        updates = {k: v for k, v in data.items() if k in allowed}
        if not updates:
            return jsonify({'error': 'Sin cambios'}), 400
        set_clause = ', '.join(f"{k}=?" for k in updates)
        conn.execute(f"UPDATE accounts SET {set_clause} WHERE id=?",
                     list(updates.values()) + [account_id])
        conn.commit()
        row = conn.execute("SELECT * FROM accounts WHERE id=?", [account_id]).fetchone()
        return jsonify(dict(zip(row.keys(), tuple(row))))
    finally:
        conn.close()


@accounts_bp.route('/api/accounts/<int:account_id>', methods=['DELETE'])
def api_delete(account_id):
    conn = get_db()
    try:
        # Prevent deleting the last account
        count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        if count <= 1:
            return jsonify({'error': 'No puedes eliminar la última cuenta'}), 400
        conn.execute("DELETE FROM accounts WHERE id=?", [account_id])
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()
