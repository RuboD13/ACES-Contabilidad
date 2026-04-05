"""
Business metrics computation for ACES Alquiler.

compute_metrics(period_id, conn, filters=None)
    → full metrics dict (JSON-serializable) for the dashboard API

compute_evolution(conn)
    → monthly trend dict for the evolution line chart
"""

from collections import defaultdict
from config import CATEGORY_COLORS


# ── Public API ─────────────────────────────────────────────────────────────────

def compute_metrics(period_id, conn, filters=None):
    period = conn.execute("SELECT * FROM periods WHERE id = ?", [period_id]).fetchone()
    if not period:
        return None

    where, params = _build_where(period_id, filters)

    txs = conn.execute(
        f"""SELECT t.id, t.fecha, t.concepto, t.importe, t.is_income,
                   t.category_key, t.confidence,
                   r.category_label, r.category_type
            FROM transactions t
            LEFT JOIN categorization_rules r
                   ON t.category_key = r.category_key AND r.is_active = 1
            WHERE {where}
            ORDER BY t.fecha""",
        params,
    ).fetchall()

    ingresos = [t for t in txs if t['is_income'] == 1]
    gastos   = [t for t in txs if t['is_income'] == 0]

    ingresos_total = sum(t['importe'] for t in ingresos)
    gastos_total   = abs(sum(t['importe'] for t in gastos))
    beneficio      = ingresos_total - gastos_total
    margen_pct     = (beneficio / ingresos_total * 100) if ingresos_total else 0
    sin_cat        = sum(1 for t in txs if t['category_key'] == 'sin_categoria')
    ticket_medio   = (ingresos_total / len(ingresos)) if ingresos else 0

    ingresos_por_fuente = _group_by_category(ingresos, ingresos_total, tipo='income')
    gastos_por_cat      = _group_by_category(gastos,   gastos_total,   tipo='expense', abs_amount=True)
    mejor_fuente        = ingresos_por_fuente[0] if ingresos_por_fuente else None
    vs_anterior         = _vs_anterior(period_id, period['tipo'], ingresos_total, gastos_total, beneficio, conn)

    return {
        'period':   _row_to_dict(period),
        'kpis': {
            'ingresos_totales':     _r(ingresos_total),
            'gastos_totales':       _r(gastos_total),
            'beneficio_neto':       _r(beneficio),
            'margen_pct':           _r(margen_pct, 1),
            'total_operaciones':    len(txs),
            'ingresos_count':       len(ingresos),
            'gastos_count':         len(gastos),
            'sin_categoria_count':  sin_cat,
            'ticket_medio_ingresos': _r(ticket_medio),
            'mejor_fuente':         mejor_fuente,
            'vs_anterior':          vs_anterior,
        },
        'ingresos_por_fuente': ingresos_por_fuente,
        'gastos_por_categoria': gastos_por_cat,
        'submetrics': ingresos_por_fuente + gastos_por_cat,
    }


def compute_evolution(conn, account_id=None):
    """All periods ordered chronologically with their totals."""
    where  = "WHERE p.account_id = ?" if account_id else ""
    params = [account_id] if account_id else []
    rows = conn.execute(
        f"""SELECT p.id, p.name, p.date_from,
                  COALESCE(SUM(CASE WHEN t.is_income=1 THEN t.importe ELSE 0 END), 0) AS ingresos,
                  COALESCE(SUM(CASE WHEN t.is_income=0 THEN ABS(t.importe) ELSE 0 END), 0) AS gastos
           FROM periods p
           LEFT JOIN transactions t ON p.id = t.period_id
           {where}
           GROUP BY p.id
           ORDER BY p.date_from""",
        params,
    ).fetchall()

    return {
        'labels':    [r['name'] for r in rows],
        'ingresos':  [_r(r['ingresos']) for r in rows],
        'gastos':    [_r(r['gastos'])   for r in rows],
        'beneficio': [_r(r['ingresos'] - r['gastos']) for r in rows],
        'period_ids': [r['id'] for r in rows],
    }


# ── Internal helpers ───────────────────────────────────────────────────────────

def _build_where(period_id, filters):
    conditions = ["t.period_id = ?"]
    params: list = [period_id]

    if not filters:
        return " AND ".join(conditions), params

    if filters.get('date_from'):
        conditions.append("t.fecha >= ?")
        params.append(filters['date_from'])
    if filters.get('date_to'):
        conditions.append("t.fecha <= ?")
        params.append(filters['date_to'])
    if filters.get('tipo_tx') == 'income':
        conditions.append("t.is_income = 1")
    elif filters.get('tipo_tx') == 'expense':
        conditions.append("t.is_income = 0")
    cats = filters.get('categories')
    if cats:
        ph = ','.join('?' * len(cats))
        conditions.append(f"t.category_key IN ({ph})")
        params.extend(cats)
    if filters.get('min_importe') is not None:
        conditions.append("ABS(t.importe) >= ?")
        params.append(abs(float(filters['min_importe'])))
    if filters.get('max_importe') is not None:
        conditions.append("ABS(t.importe) <= ?")
        params.append(abs(float(filters['max_importe'])))

    return " AND ".join(conditions), params


def _group_by_category(txs, total, tipo, abs_amount=False):
    buckets = defaultdict(lambda: {'amount': 0.0, 'count': 0, 'label': '', 'tipo': tipo})
    for t in txs:
        key = t['category_key'] or 'sin_categoria'
        amt = abs(t['importe']) if abs_amount else t['importe']
        buckets[key]['amount'] += amt
        buckets[key]['count']  += 1
        buckets[key]['label']   = t['category_label'] or key
        buckets[key]['tipo']    = tipo

    result = []
    for key, data in sorted(buckets.items(), key=lambda x: -x[1]['amount']):
        pct    = (data['amount'] / total * 100) if total else 0
        ticket = data['amount'] / data['count'] if data['count'] else 0
        result.append({
            'key':         key,
            'label':       data['label'],
            'amount':      _r(data['amount']),
            'pct':         _r(pct, 1),
            'count':       data['count'],
            'ticket_medio': _r(ticket),
            'color':       CATEGORY_COLORS.get(key, '#64748b'),
            'tipo':        tipo,
        })
    return result


def _vs_anterior(period_id, tipo, ingresos, gastos, beneficio, conn):
    prev = conn.execute(
        "SELECT id FROM periods WHERE tipo=? AND id < ? ORDER BY date_from DESC LIMIT 1",
        [tipo, period_id],
    ).fetchone()
    if not prev:
        return None

    row = conn.execute(
        """SELECT
               COALESCE(SUM(CASE WHEN is_income=1 THEN importe ELSE 0 END), 0) AS ing,
               COALESCE(SUM(CASE WHEN is_income=0 THEN ABS(importe) ELSE 0 END), 0) AS gas
           FROM transactions WHERE period_id = ?""",
        [prev['id']],
    ).fetchone()
    p_ing = row['ing']
    p_gas = row['gas']
    p_ben = p_ing - p_gas

    def pct_change(new, old):
        if old == 0:
            return None
        return _r((new - old) / abs(old) * 100, 1)

    return {
        'ingresos_pct':  pct_change(ingresos,  p_ing),
        'gastos_pct':    pct_change(gastos,    p_gas),
        'beneficio_pct': pct_change(beneficio, p_ben),
    }


def _r(val, decimals=2):
    return round(float(val), decimals)


def _row_to_dict(row):
    return dict(zip(row.keys(), tuple(row)))
