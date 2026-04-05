import os
from flask import Blueprint, render_template, request, jsonify, send_from_directory, abort
from database.db import get_db, log_action_db
from config import UPLOAD_FOLDER
from werkzeug.utils import secure_filename

facturas_bp = Blueprint('facturas', __name__)

FACTURAS_FOLDER = os.path.join(UPLOAD_FOLDER, 'facturas')
ALLOWED_MIME = {'.pdf', '.jpg', '.jpeg', '.png', '.webp', '.heic', '.tiff'}


@facturas_bp.route('/facturas')
def facturas():
    conn = get_db()
    account_id = request.args.get('account', 1, type=int)
    conn.close()
    return render_template('facturas.html', current_account_id=account_id)


@facturas_bp.route('/api/facturas', methods=['GET'])
def api_list_facturas():
    conn = get_db()
    try:
        account_id = request.args.get('account', type=int)
        trimestre  = request.args.get('trimestre', '').strip()
        search     = request.args.get('search', '').strip()
        tx_id      = request.args.get('transaction_id', type=int)

        conditions = []
        params = []
        if account_id:
            conditions.append("f.account_id = ?")
            params.append(account_id)
        if trimestre:
            conditions.append("f.trimestre = ?")
            params.append(trimestre)
        if search:
            conditions.append("(LOWER(f.proveedor) LIKE ? OR LOWER(f.numero_factura) LIKE ? OR LOWER(f.original_name) LIKE ?)")
            like = f'%{search.lower()}%'
            params.extend([like, like, like])
        if tx_id:
            conditions.append("f.transaction_id = ?")
            params.append(tx_id)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = conn.execute(
            f"""SELECT f.*,
                       t.concepto  AS tx_concepto,
                       t.fecha     AS tx_fecha,
                       t.importe   AS tx_importe,
                       p.name      AS tx_period_name
                FROM facturas f
                LEFT JOIN transactions t ON f.transaction_id = t.id
                LEFT JOIN periods p ON t.period_id = p.id
                {where}
                ORDER BY f.uploaded_at DESC""",
            params
        ).fetchall()
        return jsonify([dict(zip(r.keys(), tuple(r))) for r in rows])
    finally:
        conn.close()


@facturas_bp.route('/api/facturas', methods=['POST'])
def api_upload_factura():
    os.makedirs(FACTURAS_FOLDER, exist_ok=True)
    f = request.files.get('file')
    if not f or not f.filename:
        return jsonify({'error': 'No se recibió ningún archivo'}), 400

    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_MIME:
        return jsonify({'error': f'Formato no permitido: {ext}'}), 400

    safe_name = secure_filename(f.filename)
    # Avoid collisions
    import time
    unique_name = f"{int(time.time())}_{safe_name}"
    dest = os.path.join(FACTURAS_FOLDER, unique_name)
    f.save(dest)
    file_size = os.path.getsize(dest)

    account_id     = request.form.get('account_id', 1, type=int)
    transaction_id = request.form.get('transaction_id', type=int)
    fecha_factura  = request.form.get('fecha_factura', '')
    numero_factura = request.form.get('numero_factura', '')
    proveedor      = request.form.get('proveedor', '')
    importe_str    = request.form.get('importe', '')
    notes          = request.form.get('notes', '')

    importe = None
    if importe_str:
        try:
            importe = float(importe_str.replace(',', '.'))
        except ValueError:
            pass

    # Auto-compute trimestre from fecha_factura
    trimestre = ''
    if fecha_factura:
        try:
            year, month, _ = fecha_factura.split('-')
            q = (int(month) - 1) // 3 + 1
            trimestre = f"{year}-Q{q}"
        except Exception:
            pass

    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO facturas
               (transaction_id, account_id, filename, original_name, file_size, mime_type,
                fecha_factura, numero_factura, proveedor, importe, trimestre, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (transaction_id, account_id, unique_name, f.filename, file_size,
             ext, fecha_factura, numero_factura, proveedor, importe, trimestre, notes)
        )
        tx_info = conn.execute("SELECT concepto, fecha FROM transactions WHERE id=?", [transaction_id]).fetchone() if transaction_id else None
        concepto = tx_info['concepto'] if tx_info else None
        prov = proveedor or f.filename
        log_action_db(conn, 'factura_upload',
            f'Factura subida: "{prov}"' + (f' → "{concepto[:50]}"' if concepto else ''),
            account_id, transaction_id,
            details={
                'archivo':        f.filename,
                'proveedor':      proveedor or None,
                'importe':        importe,
                'fecha_factura':  fecha_factura or None,
                'numero_factura': numero_factura or None,
                'concepto_tx':    concepto,
                'fecha_tx':       tx_info['fecha'] if tx_info else None,
            })
        conn.commit()
        row = conn.execute("SELECT * FROM facturas WHERE id=?", [cur.lastrowid]).fetchone()
        return jsonify(dict(zip(row.keys(), tuple(row)))), 201
    finally:
        conn.close()


@facturas_bp.route('/api/facturas/<int:factura_id>', methods=['PUT'])
def api_update_factura(factura_id):
    data = request.get_json(force=True) or {}
    conn = get_db()
    try:
        allowed = {'fecha_factura', 'numero_factura', 'proveedor', 'importe', 'notes', 'transaction_id'}
        updates = {k: v for k, v in data.items() if k in allowed}
        if 'fecha_factura' in updates and updates['fecha_factura']:
            try:
                year, month, _ = updates['fecha_factura'].split('-')
                q = (int(month) - 1) // 3 + 1
                updates['trimestre'] = f"{year}-Q{q}"
            except Exception:
                pass
        if not updates:
            return jsonify({'error': 'Sin cambios'}), 400
        set_clause = ', '.join(f"{k}=?" for k in updates)
        conn.execute(f"UPDATE facturas SET {set_clause} WHERE id=?",
                     list(updates.values()) + [factura_id])
        conn.commit()
        row = conn.execute("SELECT * FROM facturas WHERE id=?", [factura_id]).fetchone()
        return jsonify(dict(zip(row.keys(), tuple(row))))
    finally:
        conn.close()


@facturas_bp.route('/api/facturas/<int:factura_id>', methods=['DELETE'])
def api_delete_factura(factura_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT filename, original_name, account_id, transaction_id FROM facturas WHERE id=?", [factura_id]).fetchone()
        if not row:
            return jsonify({'error': 'No encontrada'}), 404
        tx_del = conn.execute("SELECT concepto, fecha FROM transactions WHERE id=?", [row['transaction_id']]).fetchone() if row['transaction_id'] else None
        log_action_db(conn, 'factura_delete',
            f'Factura eliminada: "{row["original_name"]}"',
            row['account_id'], row['transaction_id'],
            details={
                'archivo':     row['original_name'],
                'concepto_tx': tx_del['concepto'] if tx_del else None,
                'fecha_tx':    tx_del['fecha']    if tx_del else None,
            })
        conn.execute("DELETE FROM facturas WHERE id=?", [factura_id])
        conn.commit()
        # Try to delete the physical file
        try:
            os.remove(os.path.join(FACTURAS_FOLDER, row['filename']))
        except OSError:
            pass
        return jsonify({'ok': True})
    finally:
        conn.close()


@facturas_bp.route('/api/facturas/<int:factura_id>/file')
def serve_factura(factura_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT filename, original_name FROM facturas WHERE id=?", [factura_id]).fetchone()
        if not row:
            abort(404)
        return send_from_directory(FACTURAS_FOLDER, row['filename'],
                                   download_name=row['original_name'])
    finally:
        conn.close()
