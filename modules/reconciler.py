"""
Computes the cuadre (reconciliation) for a period.

Formula:
    saldo_calculado = saldo_inicial + SUM(all transaction importes)
    diferencia      = saldo_calculado - saldo_final_csv

For 'banco' periods: saldo_final_csv comes from the last CSV row's saldo column.
For 'caja' periods:  saldo_final_csv is entered manually by the user.
"""


def compute_reconciliation(period, conn):
    """
    Args:
        period: sqlite3.Row from the periods table
        conn:   open DB connection

    Returns:
        dict with reconciliation data, or None if not enough data.
    """
    saldo_inicial = period['saldo_inicial'] or 0.0
    saldo_final_csv = period['saldo_final_csv']

    row = conn.execute(
        """SELECT
               COALESCE(SUM(CASE WHEN is_income = 1 THEN importe ELSE 0 END), 0) AS total_ingresos,
               COALESCE(SUM(CASE WHEN is_income = 0 THEN importe ELSE 0 END), 0) AS total_gastos_raw,
               COUNT(*) AS total_tx
           FROM transactions WHERE period_id = ?""",
        [period['id']],
    ).fetchone()

    total_ingresos  = round(row['total_ingresos'], 2)
    total_gastos    = round(abs(row['total_gastos_raw']), 2)   # stored as negatives
    total_movimiento = total_ingresos - total_gastos           # net movement

    saldo_calculado = round(saldo_inicial + total_movimiento, 2)

    if saldo_final_csv is not None:
        diferencia   = round(saldo_calculado - saldo_final_csv, 2)
        is_reconciled = abs(diferencia) < 0.02  # allow tiny float rounding
    else:
        diferencia    = None
        is_reconciled = False

    return {
        'period_id':      period['id'],
        'tipo':           period['tipo'],
        'saldo_inicial':  round(saldo_inicial, 2),
        'total_ingresos': total_ingresos,
        'total_gastos':   total_gastos,
        'saldo_calculado': saldo_calculado,
        'saldo_final_csv': saldo_final_csv,
        'diferencia':     diferencia,
        'is_reconciled':  is_reconciled,
        'total_tx':       row['total_tx'],
    }
