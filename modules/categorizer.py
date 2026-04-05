"""
Rule-based transaction categorizer.

Rules are loaded from the DB ordered by priority (lower = first).
For each transaction, the sign of importe pre-filters rules to the
correct type (income/expense) to avoid cross-type false matches.
Manual overrides (is_manual_override = 1) are never re-categorized.
"""

import json


def categorize_transaction(concepto, is_income, rules):
    """
    Categorize a single transaction.

    Args:
        concepto:  str — transaction description
        is_income: bool — True if importe > 0
        rules:     list of sqlite3.Row from categorization_rules (already filtered active+sorted)

    Returns:
        dict {category_key, rule_id, confidence}
    """
    target_type = 'income' if is_income else 'expense'
    normalized = _normalize(concepto)

    for rule in rules:
        if rule['category_type'] != target_type:
            continue
        keywords = json.loads(rule['keywords'])
        for kw in keywords:
            if _normalize(kw) in normalized:
                return {
                    'category_key': rule['category_key'],
                    'rule_id':      rule['id'],
                    'confidence':   1.0,
                }

    return {
        'category_key': 'sin_categoria',
        'rule_id':      None,
        'confidence':   0.0,
    }


def categorize_batch(transactions, rules):
    """
    Categorize a list of transaction dicts in-place.
    Each dict must have 'concepto' and 'importe'.
    Returns the same list with 'category_key', 'rule_id', 'confidence' added.
    """
    for tx in transactions:
        is_income = tx['importe'] > 0
        result = categorize_transaction(tx['concepto'], is_income, rules)
        tx.update(result)
    return transactions


def recategorize_period(period_id, conn):
    """
    Re-run categorization for all non-manually-overridden transactions
    in a given period. Commits the changes.
    """
    rules = conn.execute(
        "SELECT * FROM categorization_rules WHERE is_active = 1 ORDER BY priority ASC"
    ).fetchall()

    txs = conn.execute(
        """SELECT id, concepto, importe FROM transactions
           WHERE period_id = ? AND is_manual_override = 0""",
        [period_id],
    ).fetchall()

    for tx in txs:
        is_income = tx['importe'] > 0
        result = categorize_transaction(tx['concepto'], is_income, rules)
        conn.execute(
            """UPDATE transactions
               SET category_key = ?, rule_id = ?, confidence = ?
               WHERE id = ?""",
            (result['category_key'], result['rule_id'], result['confidence'], tx['id']),
        )
    conn.commit()


def _normalize(s):
    s = s.lower()
    for a, b in [('á','a'),('é','e'),('í','i'),('ó','o'),('ú','u'),('ñ','n'),('ç','c')]:
        s = s.replace(a, b)
    return s
