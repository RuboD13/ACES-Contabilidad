import os
import json as json_mod
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.db import get_db, get_all_periods, get_all_accounts, log_action_db
from modules.csv_parser import parse_file, detect_periods
from modules.categorizer import categorize_batch
from config import UPLOAD_FOLDER

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'.csv', '.txt', '.xls', '.xlsx'}


@upload_bp.route('/upload', methods=['GET'])
def upload_form():
    conn = get_db()
    account_id = request.args.get('account', 1, type=int)
    periods    = get_all_periods(conn, account_id)
    accounts   = get_all_accounts(conn)
    conn.close()
    return render_template('upload.html', periods=periods, accounts=accounts,
                           current_account_id=account_id)


@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    f = request.files.get('csv_file')
    if not f or not f.filename:
        flash('Selecciona un archivo.', 'danger')
        return redirect(url_for('upload.upload_form'))

    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        flash('Formato no soportado. Usa CSV, XLS o XLSX.', 'danger')
        return redirect(url_for('upload.upload_form'))

    tipo               = request.form.get('tipo', 'banco')
    account_id         = request.form.get('account_id', 1, type=int)
    periods_config_raw = request.form.get('periods_config', '')

    try:
        parsed = parse_file(f)
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('upload.upload_form'))

    all_txs = parsed['transactions']

    try:
        periods_config = json_mod.loads(periods_config_raw) if periods_config_raw else []
    except (json_mod.JSONDecodeError, ValueError):
        periods_config = []

    if not periods_config:
        periods_config = [
            {'name': p['name'], 'date_from': p['date_from'],
             'date_to': p['date_to'], 'saldo_inicial': None}
            for p in detect_periods(all_txs)
        ]

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    conn = get_db()
    last_period_id = None

    try:
        rules = conn.execute(
            "SELECT * FROM categorization_rules WHERE is_active=1 ORDER BY priority"
        ).fetchall()

        for pc in periods_config:
            date_from = pc['date_from']
            date_to   = pc['date_to']
            name      = pc.get('name') or _auto_period_name(date_from)

            saldo_ini_raw = pc.get('saldo_inicial', '')
            saldo_inicial = None
            if saldo_ini_raw not in (None, '', 'null'):
                try:
                    saldo_inicial = float(str(saldo_ini_raw).replace(',', '.'))
                except ValueError:
                    pass

            period_txs = [t for t in all_txs if date_from <= t['fecha'] <= date_to]
            if not period_txs:
                continue

            if saldo_inicial is None:
                first = period_txs[0]
                if first.get('saldo') is not None:
                    saldo_inicial = round(first['saldo'] - first['importe'], 2)

            saldo_final = period_txs[-1].get('saldo')
            categorize_batch(period_txs, rules)

            cur = conn.execute(
                """INSERT INTO periods
                   (account_id, name, date_from, date_to, tipo,
                    saldo_inicial, saldo_final_csv, csv_filename)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (account_id, name, date_from, date_to, tipo,
                 saldo_inicial, saldo_final, f.filename),
            )
            period_id      = cur.lastrowid
            last_period_id = period_id

            conn.executemany(
                """INSERT INTO transactions
                   (period_id, fecha, concepto, importe, saldo, is_income,
                    category_key, rule_id, confidence, raw_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [(period_id, t['fecha'], t['concepto'], t['importe'], t.get('saldo'),
                  1 if t['importe'] > 0 else 0,
                  t['category_key'], t['rule_id'], t['confidence'],
                  json_mod.dumps(t['raw_data'], ensure_ascii=False) if t.get('raw_data') else None)
                 for t in period_txs],
            )

        n = len(periods_config)
        period_names = [pc.get('name') or _auto_period_name(pc['date_from']) for pc in periods_config if pc]
        log_action_db(conn, 'import',
            f'Importado "{f.filename}": {len(all_txs)} transacciones en {n} período(s)',
            account_id,
            details={
                'archivo':    f.filename,
                'transacciones': len(all_txs),
                'periodos':   period_names,
                'cuenta_id':  account_id,
            })
        conn.commit()
    finally:
        conn.close()

    for w in parsed['warnings']:
        flash(w, 'warning')

    flash(f'Importadas {len(all_txs)} transacciones en {len(periods_config)} período{"s" if len(periods_config) > 1 else ""}.', 'success')
    return redirect(url_for('dashboard.dashboard',
                            period=last_period_id, account=account_id))


@upload_bp.route('/upload/preview', methods=['POST'])
def upload_preview():
    f = request.files.get('csv_file')
    if not f:
        return jsonify({'error': 'No se recibió ningún archivo.'}), 400

    ext = os.path.splitext(f.filename or '')[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Formato no soportado: {ext}. Usa CSV, XLS o XLSX.'}), 400

    try:
        parsed = parse_file(f)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    txs     = parsed['transactions']
    periods = detect_periods(txs)

    return jsonify({
        'rows':          txs[:15],
        'total':         len(txs),
        'date_from':     parsed['date_from'],
        'date_to':       parsed['date_to'],
        'saldo_inicial': parsed['saldo_inicial'],
        'saldo_final':   parsed['saldo_final'],
        'warnings':      parsed['warnings'],
        'periods':       periods,
    })


@upload_bp.route('/api/periods/<int:period_id>', methods=['DELETE'])
def delete_period(period_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT name, account_id FROM periods WHERE id=?", [period_id]).fetchone()
        if not row:
            return jsonify({'error': 'Período no encontrado'}), 404
        log_action_db(conn, 'period_delete',
            f'Período "{row["name"]}" eliminado',
            row['account_id'],
            details={
                'periodo':    row['name'],
                'periodo_id': period_id,
            })
        conn.execute("DELETE FROM periods WHERE id=?", [period_id])
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


_MESES = ['','Enero','Febrero','Marzo','Abril','Mayo','Junio',
          'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']


def _auto_period_name(date_str):
    try:
        year, month, _ = date_str.split('-')
        return f"{_MESES[int(month)]} {year}"
    except Exception:
        return date_str
