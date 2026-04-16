import json
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from database.db import get_db, get_all_periods, log_action_db
from modules.categorizer import recategorize_period

rules_bp = Blueprint('rules', __name__)


@rules_bp.route('/rules')
def rules():
    conn = get_db()
    all_rules = conn.execute(
        "SELECT * FROM categorization_rules ORDER BY category_type, priority, category_label"
    ).fetchall()
    periods = get_all_periods(conn)
    conn.close()
    return render_template('rules.html', rules=all_rules, periods=periods)


@rules_bp.route('/api/rules', methods=['GET'])
def api_rules():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM categorization_rules ORDER BY category_type, priority"
        ).fetchall()
        return jsonify([dict(zip(r.keys(), tuple(r))) for r in rows])
    finally:
        conn.close()


@rules_bp.route('/api/rules', methods=['POST'])
def create_rule():
    data = request.get_json(force=True) or {}
    required = {'category_key', 'category_label', 'category_type', 'keywords'}
    if not required.issubset(data):
        return jsonify({'error': 'Faltan campos obligatorios'}), 400

    kw = data['keywords']
    if isinstance(kw, str):
        kw = [k.strip() for k in kw.split(',') if k.strip()]

    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO categorization_rules
               (category_key, category_label, category_type, keywords, priority, is_active)
               VALUES (?, ?, ?, ?, ?, 1)""",
            (data['category_key'].strip(), data['category_label'].strip(),
             data['category_type'], json.dumps(kw, ensure_ascii=False),
             int(data.get('priority', 100))),
        )
        log_action_db(conn, 'rule_create',
            f'Nueva regla: "{data["category_label"].strip()}"',
            details={
                'clave':      data['category_key'].strip(),
                'etiqueta':   data['category_label'].strip(),
                'tipo':       data['category_type'],
                'palabras_clave': kw,
                'prioridad':  int(data.get('priority', 100)),
            })
        conn.commit()
        row = conn.execute("SELECT * FROM categorization_rules WHERE id=?", [cur.lastrowid]).fetchone()
        return jsonify(dict(zip(row.keys(), tuple(row)))), 201
    finally:
        conn.close()


@rules_bp.route('/api/rules/<int:rule_id>', methods=['PUT'])
def update_rule(rule_id):
    data = request.get_json(force=True) or {}
    conn = get_db()
    try:
        allowed = {'category_label', 'keywords', 'priority', 'is_active'}
        updates = {k: v for k, v in data.items() if k in allowed}
        if 'keywords' in updates:
            kw = updates['keywords']
            if isinstance(kw, str):
                kw = [k.strip() for k in kw.split(',') if k.strip()]
            updates['keywords'] = json.dumps(kw, ensure_ascii=False)
        updates['updated_at'] = "datetime('now')"

        set_parts = []
        vals = []
        for k, v in updates.items():
            if k == 'updated_at':
                set_parts.append(f"{k} = datetime('now')")
            else:
                set_parts.append(f"{k} = ?")
                vals.append(v)
        vals.append(rule_id)

        conn.execute(f"UPDATE categorization_rules SET {', '.join(set_parts)} WHERE id=?", vals)
        rule_row = conn.execute("SELECT * FROM categorization_rules WHERE id=?", [rule_id]).fetchone()
        edit_details = {'regla_id': rule_id}
        if rule_row:
            edit_details['clave']    = rule_row['category_key']
            edit_details['etiqueta'] = rule_row['category_label']
        if 'keywords' in updates:
            edit_details['palabras_clave_nuevas'] = json.loads(updates['keywords'])
        if 'priority' in updates:
            edit_details['prioridad_nueva'] = updates['priority']
        log_action_db(conn, 'rule_edit',
            f'Regla editada: "{rule_row["category_label"] if rule_row else rule_id}"',
            details=edit_details)
        conn.commit()
        row = conn.execute("SELECT * FROM categorization_rules WHERE id=?", [rule_id]).fetchone()
        return jsonify(dict(zip(row.keys(), tuple(row))))
    finally:
        conn.close()


@rules_bp.route('/api/rules/<int:rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT category_label FROM categorization_rules WHERE id=?", [rule_id]).fetchone()
        label = row['category_label'] if row else f'#{rule_id}'
        rule_row2 = conn.execute("SELECT * FROM categorization_rules WHERE id=?", [rule_id]).fetchone()
        log_action_db(conn, 'rule_delete',
            f'Regla desactivada: "{label}"',
            details={
                'regla_id':  rule_id,
                'clave':     rule_row2['category_key']   if rule_row2 else None,
                'etiqueta':  rule_row2['category_label'] if rule_row2 else label,
                'tipo':      rule_row2['category_type']  if rule_row2 else None,
            })
        conn.execute("UPDATE categorization_rules SET is_active=0 WHERE id=?", [rule_id])
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


# ── Tags API ───────────────────────────────────────────────────────────────────

@rules_bp.route('/api/tags', methods=['GET'])
def api_tags():
    conn = get_db()
    try:
        account_id = request.args.get('account', type=int)
        if account_id:
            rows = conn.execute(
                "SELECT * FROM tags WHERE account_id=? OR account_id IS NULL ORDER BY name",
                [account_id]
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM tags ORDER BY name").fetchall()
        result = []
        for r in rows:
            d = dict(zip(r.keys(), tuple(r)))
            if isinstance(d.get('keywords'), str):
                try:
                    d['keywords'] = json.loads(d['keywords'])
                except (json.JSONDecodeError, TypeError):
                    d['keywords'] = []
            result.append(d)
        return jsonify(result)
    finally:
        conn.close()


@rules_bp.route('/api/tags/<int:tag_id>', methods=['GET'])
def get_tag(tag_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM tags WHERE id=?", [tag_id]).fetchone()
        if not row:
            return jsonify({'error': 'Etiqueta no encontrada'}), 404
        d = dict(zip(row.keys(), tuple(row)))
        if isinstance(d.get('keywords'), str):
            try:
                d['keywords'] = json.loads(d['keywords'])
            except (json.JSONDecodeError, TypeError):
                d['keywords'] = []
        return jsonify(d)
    finally:
        conn.close()


def _parse_keywords(kw):
    """Normaliza keywords: acepta string CSV o lista. Devuelve lista limpia sin duplicados."""
    if isinstance(kw, str):
        kw = [k.strip().lower() for k in kw.split(',') if k.strip()]
    elif isinstance(kw, list):
        kw = [k.strip().lower() for k in kw if isinstance(k, str) and k.strip()]
    else:
        kw = []
    seen = set()
    return [k for k in kw if k not in seen and not seen.add(k)]


@rules_bp.route('/api/tags', methods=['POST'])
def create_tag():
    data = request.get_json(force=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'El nombre es obligatorio'}), 400
    conn = get_db()
    try:
        acct = data.get('account_id')
        kw = _parse_keywords(data.get('keywords', []))
        is_auto = 1 if data.get('is_auto_apply') else 0
        cur = conn.execute(
            "INSERT INTO tags (name, color, account_id, keywords, is_auto_apply) VALUES (?, ?, ?, ?, ?)",
            (name, data.get('color', '#6366f1'), acct, json.dumps(kw, ensure_ascii=False), is_auto)
        )
        log_action_db(conn, 'tag_create', f'Nueva etiqueta: "{name}"', acct or 1,
            details={'nombre': name, 'color': data.get('color', '#6366f1'),
                     'palabras_clave': kw, 'auto_aplicar': bool(is_auto)})
        conn.commit()
        row = conn.execute("SELECT * FROM tags WHERE id=?", [cur.lastrowid]).fetchone()
        d = dict(zip(row.keys(), tuple(row)))
        d['keywords'] = json.loads(d['keywords']) if isinstance(d.get('keywords'), str) else (d.get('keywords') or [])
        return jsonify(d), 201
    finally:
        conn.close()


@rules_bp.route('/api/tags/<int:tag_id>', methods=['PUT'])
def update_tag(tag_id):
    data = request.get_json(force=True) or {}
    conn = get_db()
    try:
        allowed = {'name', 'color', 'keywords', 'is_auto_apply'}
        updates = {k: v for k, v in data.items() if k in allowed}
        if not updates:
            return jsonify({'error': 'Sin cambios'}), 400
        if 'keywords' in updates:
            updates['keywords'] = json.dumps(
                _parse_keywords(updates['keywords']), ensure_ascii=False)
        if 'is_auto_apply' in updates:
            updates['is_auto_apply'] = 1 if updates['is_auto_apply'] else 0
        set_clause = ', '.join(f"{k}=?" for k in updates)
        conn.execute(f"UPDATE tags SET {set_clause} WHERE id=?",
                     list(updates.values()) + [tag_id])
        tag_row = conn.execute("SELECT name FROM tags WHERE id=?", [tag_id]).fetchone()
        log_action_db(conn, 'tag_edit',
            f'Etiqueta editada: "{tag_row["name"] if tag_row else tag_id}"',
            details={'tag_id': tag_id, **{k: v for k, v in updates.items()}})
        conn.commit()
        row = conn.execute("SELECT * FROM tags WHERE id=?", [tag_id]).fetchone()
        d = dict(zip(row.keys(), tuple(row)))
        d['keywords'] = json.loads(d['keywords']) if isinstance(d.get('keywords'), str) else (d.get('keywords') or [])
        return jsonify(d)
    finally:
        conn.close()


@rules_bp.route('/api/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    conn = get_db()
    try:
        tag = conn.execute("SELECT name FROM tags WHERE id=?", [tag_id]).fetchone()
        tag_name = tag['name'] if tag else f'#{tag_id}'
        log_action_db(conn, 'tag_delete', f'Etiqueta eliminada: "{tag_name}"',
            details={'nombre': tag_name, 'tag_id': tag_id})
        conn.execute("DELETE FROM tags WHERE id=?", [tag_id])
        conn.commit()
        return jsonify({'ok': True})
    finally:
        conn.close()


@rules_bp.route('/api/rules/reapply', methods=['POST'])
def reapply_rules():
    data = request.get_json(force=True) or {}
    period_id = data.get('period_id')
    if not period_id:
        return jsonify({'error': 'period_id requerido'}), 400

    conn = get_db()
    try:
        period = conn.execute("SELECT name, account_id FROM periods WHERE id=?", [period_id]).fetchone()
        recategorize_period(period_id, conn)  # commits internally
        count = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE period_id=?", [period_id]
        ).fetchone()[0]
        pname = period['name'] if period else f'#{period_id}'
        log_action_db(conn, 'rules_reapply',
            f'Reglas reaplicadas en "{pname}": {count} transacciones',
            period['account_id'] if period else 1,
            details={
                'periodo':        pname,
                'periodo_id':     period_id,
                'recategorizadas': count,
            })
        conn.commit()
        return jsonify({'ok': True, 'recategorized': count})
    finally:
        conn.close()


@rules_bp.route('/api/rules/reapply_all', methods=['POST'])
def reapply_rules_all():
    conn = get_db()
    try:
        periods = conn.execute("SELECT id, name, account_id FROM periods").fetchall()
        total = 0
        for p in periods:
            recategorize_period(p['id'], conn)  # commits each period
            c = conn.execute(
                "SELECT COUNT(*) FROM transactions WHERE period_id=?", [p['id']]
            ).fetchone()[0]
            total += c
        log_action_db(conn, 'rules_reapply',
            f'Reglas reaplicadas en todos los períodos ({len(periods)}): {total} transacciones',
            details={
                'modo':           'todos los períodos',
                'num_periodos':   len(periods),
                'recategorizadas': total,
            })
        conn.commit()
        return jsonify({'ok': True, 'recategorized': total, 'periods': len(periods)})
    finally:
        conn.close()
