from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from database.db import get_db, get_all_periods, get_period, get_latest_period, log_action_db

transactions_bp = Blueprint('transactions', __name__)


@transactions_bp.route('/transactions')
def transactions():
    conn = get_db()
    periods = get_all_periods(conn)

    try:
        period_id = int(request.args.get('period', 0))
    except (ValueError, TypeError):
        period_id = 0

    current = None
    if period_id:
        current = get_period(conn, period_id)
    if not current:
        current = get_latest_period(conn)

    if not current:
        conn.close()
        return redirect(url_for('upload.upload_form'))

    rules = conn.execute(
        "SELECT category_key, category_label, category_type FROM categorization_rules WHERE is_active=1 ORDER BY category_label"
    ).fetchall()
    conn.close()

    return render_template('transactions.html', periods=periods, current=current, rules=rules)


@transactions_bp.route('/api/transactions/<int:period_id>')
def api_transactions(period_id):
    conn = get_db()
    try:
        # Filters from query params
        conditions = ["t.period_id = ?"]
        params = [period_id]

        tipo = request.args.get('tipo_tx')
        if tipo == 'income':
            conditions.append("t.is_income = 1")
        elif tipo == 'expense':
            conditions.append("t.is_income = 0")

        search = request.args.get('search', '').strip()
        if search:
            conditions.append("LOWER(t.concepto) LIKE ?")
            params.append(f'%{search.lower()}%')

        cats = request.args.get('categories', '').strip()
        if cats:
            cat_list = [c.strip() for c in cats.split(',') if c.strip()]
            if cat_list:
                ph = ','.join('?' * len(cat_list))
                conditions.append(f"t.category_key IN ({ph})")
                params.extend(cat_list)

        uncat_only = request.args.get('uncat_only')
        if uncat_only == '1':
            conditions.append("t.category_key = 'sin_categoria'")

        date_from = request.args.get('date_from')
        date_to   = request.args.get('date_to')
        if date_from:
            conditions.append("t.fecha >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("t.fecha <= ?")
            params.append(date_to)

        where = " AND ".join(conditions)
        order = "t.fecha DESC"

        rows = conn.execute(
            f"""SELECT t.id, t.fecha, t.concepto, t.importe, t.saldo,
                       t.is_income, t.category_key, t.confidence,
                       t.is_manual_override, t.notes, t.raw_data, t.factura_status,
                       r.category_label, r.category_type,
                       (SELECT COUNT(*) FROM facturas f WHERE f.transaction_id = t.id) AS factura_count
                FROM transactions t
                LEFT JOIN categorization_rules r
                       ON t.category_key = r.category_key AND r.is_active=1
                WHERE {where}
                ORDER BY {order}""",
            params,
        ).fetchall()

        result = [dict(zip(r.keys(), tuple(r))) for r in rows]

        # Attach tags to each transaction
        if result:
            tx_ids = [r['id'] for r in result]
            ph = ','.join('?' * len(tx_ids))
            tag_rows = conn.execute(
                f"""SELECT tt.transaction_id, tg.id, tg.name, tg.color
                    FROM transaction_tags tt JOIN tags tg ON tt.tag_id = tg.id
                    WHERE tt.transaction_id IN ({ph})""",
                tx_ids
            ).fetchall()
            tags_by_tx = {}
            for tr in tag_rows:
                tags_by_tx.setdefault(tr[0], []).append({'id': tr[1], 'name': tr[2], 'color': tr[3]})
            for r in result:
                r['tags'] = tags_by_tx.get(r['id'], [])

        return jsonify(result)
    finally:
        conn.close()


@transactions_bp.route('/api/transactions/<int:tx_id>', methods=['PATCH'])
def update_transaction(tx_id):
    data = request.get_json(force=True) or {}
    conn = get_db()
    try:
        allowed = {'category_key', 'notes'}
        updates = {k: v for k, v in data.items() if k in allowed}
        if not updates:
            return jsonify({'error': 'No valid fields'}), 400

        if 'category_key' in updates:
            updates['is_manual_override'] = 1
            updates['confidence'] = 1.0

        set_clause = ', '.join(f"{k} = ?" for k in updates)
        vals = list(updates.values()) + [tx_id]
        conn.execute(f"UPDATE transactions SET {set_clause} WHERE id = ?", vals)

        if 'category_key' in updates:
            tx_info = conn.execute(
                """SELECT t.concepto, t.importe, t.fecha, t.category_key AS old_cat,
                          COALESCE(p.account_id,1) AS account_id, p.name AS period_name
                   FROM transactions t LEFT JOIN periods p ON t.period_id=p.id WHERE t.id=?""",
                [tx_id]
            ).fetchone()
            old_rule = conn.execute(
                "SELECT category_label FROM categorization_rules WHERE category_key=? AND is_active=1",
                [tx_info['old_cat'] if tx_info else 'sin_categoria']
            ).fetchone()
            new_rule = conn.execute(
                "SELECT category_label FROM categorization_rules WHERE category_key=? AND is_active=1",
                [updates['category_key']]
            ).fetchone()
            concepto = tx_info['concepto'] if tx_info else f'#{tx_id}'
            log_action_db(conn, 'category_change',
                f'Categoría cambiada: "{concepto[:60]}"',
                tx_info['account_id'] if tx_info else 1, tx_id,
                details={
                    'concepto':            tx_info['concepto']    if tx_info else None,
                    'fecha':               tx_info['fecha']        if tx_info else None,
                    'importe':             tx_info['importe']      if tx_info else None,
                    'periodo':             tx_info['period_name']  if tx_info else None,
                    'categoria_anterior':  old_rule['category_label'] if old_rule else (tx_info['old_cat'] if tx_info else None),
                    'categoria_nueva':     new_rule['category_label'] if new_rule else updates['category_key'],
                })
        conn.commit()

        row = conn.execute(
            """SELECT t.*, r.category_label FROM transactions t
               LEFT JOIN categorization_rules r ON t.category_key = r.category_key AND r.is_active=1
               WHERE t.id = ?""",
            [tx_id],
        ).fetchone()
        return jsonify(dict(zip(row.keys(), tuple(row))))
    finally:
        conn.close()


@transactions_bp.route('/api/transactions/<int:tx_id>', methods=['DELETE'])
def delete_transaction(tx_id):
    conn = get_db()
    try:
        row = conn.execute(
            """SELECT t.concepto, t.importe, t.fecha, t.category_key,
                      COALESCE(p.account_id,1) AS account_id, p.name AS period_name
               FROM transactions t LEFT JOIN periods p ON t.period_id=p.id WHERE t.id=?""",
            [tx_id]
        ).fetchone()
        acct_id  = row['account_id'] if row else 1
        concepto = row['concepto'] if row else f'#{tx_id}'
        cat_rule = conn.execute(
            "SELECT category_label FROM categorization_rules WHERE category_key=? AND is_active=1",
            [row['category_key'] if row else 'sin_categoria']
        ).fetchone()
        log_action_db(conn, 'tx_delete',
            f'Transacción eliminada: "{concepto[:60]}"',
            acct_id, tx_id,
            details={
                'concepto':  row['concepto']        if row else None,
                'fecha':     row['fecha']            if row else None,
                'importe':   row['importe']          if row else None,
                'categoria': cat_rule['category_label'] if cat_rule else (row['category_key'] if row else None),
                'periodo':   row['period_name']      if row else None,
            })
        conn.execute("DELETE FROM transactions WHERE id = ?", [tx_id])
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


@transactions_bp.route('/api/transactions/<int:tx_id>/factura_status', methods=['PATCH'])
def update_factura_status(tx_id):
    data = request.get_json(force=True) or {}
    status = data.get('factura_status', 'sin_factura')
    valid = {'sin_factura', 'pedir_factura', 'factura_emitida', 'con_factura'}
    if status not in valid:
        return jsonify({'error': 'Estado no válido'}), 400
    conn = get_db()
    try:
        tx_info = conn.execute(
            """SELECT t.concepto, t.fecha, t.importe, t.factura_status AS old_status,
                      COALESCE(p.account_id,1) AS account_id
               FROM transactions t LEFT JOIN periods p ON t.period_id=p.id WHERE t.id=?""",
            [tx_id]
        ).fetchone()
        STATUS_LABELS = {
            'sin_factura':    'Sin factura',
            'pedir_factura':  'Pedir factura',
            'factura_emitida':'Factura emitida',
            'con_factura':    'Con factura',
        }
        concepto = tx_info['concepto'] if tx_info else f'#{tx_id}'
        log_action_db(conn, 'factura_status',
            f'Estado factura: "{concepto[:60]}"',
            tx_info['account_id'] if tx_info else 1, tx_id,
            details={
                'concepto':        tx_info['concepto']   if tx_info else None,
                'fecha':           tx_info['fecha']       if tx_info else None,
                'importe':         tx_info['importe']     if tx_info else None,
                'estado_anterior': STATUS_LABELS.get(tx_info['old_status'] if tx_info else '', ''),
                'estado_nuevo':    STATUS_LABELS.get(status, status),
            })
        conn.execute("UPDATE transactions SET factura_status=? WHERE id=?", [status, tx_id])
        conn.commit()
        return jsonify({'ok': True, 'factura_status': status})
    finally:
        conn.close()


@transactions_bp.route('/api/transactions/<int:tx_id>/tags', methods=['POST'])
def add_tag_to_tx(tx_id):
    data = request.get_json(force=True) or {}
    tag_id = data.get('tag_id')
    if not tag_id:
        return jsonify({'error': 'tag_id requerido'}), 400
    conn = get_db()
    try:
        tag     = conn.execute("SELECT name FROM tags WHERE id=?", [tag_id]).fetchone()
        tx_info = conn.execute("SELECT concepto, fecha, importe FROM transactions WHERE id=?", [tx_id]).fetchone()
        tag_name = tag['name'] if tag else f'#{tag_id}'
        concepto = tx_info['concepto'] if tx_info else f'#{tx_id}'
        log_action_db(conn, 'tag_add',
            f'Etiqueta "{tag_name}" añadida a "{concepto[:50]}"',
            tx_id=tx_id,
            details={
                'concepto': tx_info['concepto'] if tx_info else None,
                'fecha':    tx_info['fecha']    if tx_info else None,
                'importe':  tx_info['importe']  if tx_info else None,
                'etiqueta': tag_name,
            })
        conn.execute(
            "INSERT OR IGNORE INTO transaction_tags (transaction_id, tag_id) VALUES (?, ?)",
            [tx_id, tag_id]
        )
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


@transactions_bp.route('/api/transactions/<int:tx_id>/tags/<int:tag_id>', methods=['DELETE'])
def remove_tag_from_tx(tx_id, tag_id):
    conn = get_db()
    try:
        tag     = conn.execute("SELECT name FROM tags WHERE id=?", [tag_id]).fetchone()
        tx_info = conn.execute("SELECT concepto, fecha, importe FROM transactions WHERE id=?", [tx_id]).fetchone()
        tag_name = tag['name'] if tag else f'#{tag_id}'
        concepto = tx_info['concepto'] if tx_info else f'#{tx_id}'
        log_action_db(conn, 'tag_remove',
            f'Etiqueta "{tag_name}" quitada de "{concepto[:50]}"',
            tx_id=tx_id,
            details={
                'concepto': tx_info['concepto'] if tx_info else None,
                'fecha':    tx_info['fecha']    if tx_info else None,
                'importe':  tx_info['importe']  if tx_info else None,
                'etiqueta': tag_name,
            })
        conn.execute(
            "DELETE FROM transaction_tags WHERE transaction_id=? AND tag_id=?",
            [tx_id, tag_id]
        )
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


@transactions_bp.route('/api/periods/history')
def periods_history():
    """Return all periods with metadata for the file history panel."""
    conn = get_db()
    try:
        account_id = request.args.get('account', type=int)
        if account_id:
            rows = conn.execute(
                """SELECT p.*,
                          COUNT(t.id)                  AS tx_count,
                          SUM(CASE WHEN t.is_income=1 THEN t.importe ELSE 0 END) AS ingresos,
                          SUM(CASE WHEN t.is_income=0 THEN ABS(t.importe) ELSE 0 END) AS gastos
                   FROM periods p
                   LEFT JOIN transactions t ON t.period_id = p.id
                   WHERE p.account_id = ?
                   GROUP BY p.id
                   ORDER BY p.date_from DESC""",
                [account_id]
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT p.*,
                          COUNT(t.id)                  AS tx_count,
                          SUM(CASE WHEN t.is_income=1 THEN t.importe ELSE 0 END) AS ingresos,
                          SUM(CASE WHEN t.is_income=0 THEN ABS(t.importe) ELSE 0 END) AS gastos
                   FROM periods p
                   LEFT JOIN transactions t ON t.period_id = p.id
                   GROUP BY p.id
                   ORDER BY p.date_from DESC"""
            ).fetchall()
        return jsonify([dict(zip(r.keys(), tuple(r))) for r in rows])
    finally:
        conn.close()


@transactions_bp.route('/api/export/transactions')
def export_transactions():
    import csv, io
    from flask import Response
    conn = get_db()
    try:
        account_id = request.args.get('account', type=int)
        if account_id:
            rows = conn.execute(
                """SELECT t.fecha, t.concepto, t.importe, t.saldo, t.category_key,
                          r.category_label, t.is_income, t.notes, t.factura_status, p.name AS period_name
                   FROM transactions t
                   LEFT JOIN categorization_rules r ON t.category_key = r.category_key
                   LEFT JOIN periods p ON t.period_id = p.id
                   WHERE p.account_id = ?
                   ORDER BY t.fecha DESC""",
                [account_id]
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT t.fecha, t.concepto, t.importe, t.saldo, t.category_key,
                          r.category_label, t.is_income, t.notes, t.factura_status, p.name AS period_name
                   FROM transactions t
                   LEFT JOIN categorization_rules r ON t.category_key = r.category_key
                   LEFT JOIN periods p ON t.period_id = p.id
                   ORDER BY t.fecha DESC"""
            ).fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Fecha','Concepto','Importe','Saldo','Categoría','Tipo','Notas','Estado Factura','Período'])
        for r in rows:
            writer.writerow([r['fecha'], r['concepto'], r['importe'], r['saldo'] or '',
                             r['category_label'] or r['category_key'], 'Ingreso' if r['is_income'] else 'Gasto',
                             r['notes'] or '', r['factura_status'] or '', r['period_name'] or ''])
        output.seek(0)
        return Response(output.getvalue(), mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment; filename=transacciones.csv'})
    finally:
        conn.close()
