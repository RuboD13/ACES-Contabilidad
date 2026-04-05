"""
Flexible file parser — accepts CSV, XLS and XLSX with date + amount columns.

Detection strategy (applied in order until one succeeds):
  1. Exact match on known Spanish/Catalan bank column names
  2. Partial keyword match on column headers
  3. Data-inference: scan first data rows to find date/number columns

After parsing, detect_periods() groups transactions by calendar month.
"""

import io
import os
import re
from datetime import datetime
from collections import defaultdict

# ── Public entry point ─────────────────────────────────────────────────────────

def parse_csv(file_storage):
    """Alias kept for compatibility — dispatches to parse_file."""
    return parse_file(file_storage)


def parse_file(file_storage):
    """
    Parse an uploaded CSV, XLS or XLSX file (any format).

    Returns:
        dict {transactions, saldo_inicial, saldo_final,
              date_from, date_to, warnings, detected_columns}
    """
    ext = os.path.splitext(file_storage.filename or '')[1].lower()
    if ext in ('.xls', '.xlsx'):
        return _parse_excel(file_storage, ext)

    raw_bytes = file_storage.read()
    encoding  = _detect_encoding(raw_bytes)
    text      = raw_bytes.decode(encoding, errors='replace')
    lines     = [l.rstrip('\r') for l in text.splitlines()]

    header_idx, col_map, sep = _find_header_any(lines)

    if header_idx is None:
        raise ValueError(
            "No se pudo detectar la estructura del CSV. "
            "Asegúrate de que el archivo tiene columnas de fecha e importe."
        )

    # Extract original column headers for raw_data storage
    headers = [c.strip().strip('"').strip("'") for c in lines[header_idx].split(sep)]
    transactions, warnings = _parse_rows(lines, header_idx + 1, col_map, sep, headers=headers)

    if not transactions:
        raise ValueError("El CSV no contiene filas con fecha e importe válidos.")

    transactions.sort(key=lambda x: x['fecha'])

    saldo_inicial = None
    saldo_final   = None
    if transactions[0].get('saldo') is not None:
        saldo_inicial = round(transactions[0]['saldo'] - transactions[0]['importe'], 2)
    if transactions[-1].get('saldo') is not None:
        saldo_final = transactions[-1]['saldo']

    return {
        'transactions':      transactions,
        'saldo_inicial':     saldo_inicial,
        'saldo_final':       saldo_final,
        'date_from':         transactions[0]['fecha'],
        'date_to':           transactions[-1]['fecha'],
        'warnings':          warnings,
        'detected_columns':  col_map,
    }


def detect_periods(transactions):
    """
    Group a sorted list of transactions by calendar month.
    Returns a list of period dicts ordered chronologically.
    """
    by_month = defaultdict(list)
    for tx in transactions:
        by_month[tx['fecha'][:7]].append(tx)   # key = YYYY-MM

    periods = []
    for month_key in sorted(by_month.keys()):
        txs  = by_month[month_key]
        year, month = month_key.split('-')
        periods.append({
            'name':              f"{_MESES[int(month)]} {year}",
            'date_from':         min(t['fecha'] for t in txs),
            'date_to':           max(t['fecha'] for t in txs),
            'transaction_count': len(txs),
            'ingresos':          round(sum(t['importe'] for t in txs if t['importe'] > 0), 2),
            'gastos':            round(abs(sum(t['importe'] for t in txs if t['importe'] < 0)), 2),
        })
    return periods


# ── Encoding detection ─────────────────────────────────────────────────────────

def _detect_encoding(raw_bytes):
    for enc in ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252'):
        try:
            raw_bytes.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return 'latin-1'


# ── Separator detection ────────────────────────────────────────────────────────

def _best_separator(line):
    """Pick separator from the header line (no decimal numbers there)."""
    return ';' if line.count(';') >= line.count(',') else ','


# ── Header detection — three strategies ───────────────────────────────────────

# Strategy 1: exact column name sets
_EXACT_FECHA    = {'data', 'fecha', 'fecha operacion', 'fecha valor', 'f.operacion',
                   'f. operacion', 'fecha movimiento', 'date'}
_EXACT_IMPORT   = {'import', 'importe', 'importe (eur)', 'importe(eur)', 'importe eur',
                   'amount', 'monto', 'importe €', 'euros', 'importe en euros'}
_EXACT_CONCEPTO = {'concepte', 'concepto', 'descripcion', 'descripción', 'description',
                   'texto', 'motivo', 'detalle', 'concepto/descripcion', 'concepto / descripcion'}
_EXACT_SALDO    = {'saldo', 'saldo (eur)', 'saldo(eur)', 'disponible', 'saldo €',
                   'balance', 'saldo disponible', 'saldo contable'}
_EXACT_CARGO    = {'cargo', 'cargos', 'debe', 'debito', 'débito', 'salida', 'salidas'}
_EXACT_ABONO    = {'abono', 'abonos', 'haber', 'credito', 'crédito', 'entrada', 'entradas'}

# Strategy 2: partial keyword match (substring)
_PARTIAL_FECHA    = ['fecha', 'date', 'data', 'dia ', 'dia_', 'f.ope']
_PARTIAL_IMPORT   = ['importe', 'import', 'monto', 'amount', 'valor', 'euros']
_PARTIAL_CONCEPTO = ['concepto', 'descripci', 'descrip', 'detail', 'texto', 'motivo']
_PARTIAL_SALDO    = ['saldo', 'balance', 'disponib']
_PARTIAL_CARGO    = ['cargo', 'debe', 'debito', 'debito', 'salida']
_PARTIAL_ABONO    = ['abono', 'haber', 'credito', 'entrada']


def _normalize(s):
    s = s.lower().strip().strip('"').strip("'")
    for a, b in [('á','a'),('é','e'),('í','i'),('ó','o'),('ú','u'),('ñ','n'),('ç','c')]:
        s = s.replace(a, b)
    return s


def _find_header_any(lines):
    """Try all three strategies; return (header_idx, col_map, sep) or (None,None,None)."""
    for strategy in (_strategy_exact, _strategy_partial, _strategy_data_inference):
        result = strategy(lines)
        if result[0] is not None:
            return result
    return None, None, None


def _strategy_exact(lines):
    for idx, line in enumerate(lines[:40]):
        sep  = _best_separator(line)
        cols = [_normalize(c) for c in line.split(sep)]
        cm   = _build_col_map(cols, _EXACT_FECHA, _EXACT_IMPORT, _EXACT_CONCEPTO,
                               _EXACT_SALDO, _EXACT_CARGO, _EXACT_ABONO, exact=True)
        if cm:
            return idx, cm, sep
    return None, None, None


def _strategy_partial(lines):
    for idx, line in enumerate(lines[:40]):
        sep  = _best_separator(line)
        cols = [_normalize(c) for c in line.split(sep)]
        cm   = _build_col_map(cols, _PARTIAL_FECHA, _PARTIAL_IMPORT, _PARTIAL_CONCEPTO,
                               _PARTIAL_SALDO, _PARTIAL_CARGO, _PARTIAL_ABONO, exact=False)
        if cm:
            return idx, cm, sep
    return None, None, None


def _strategy_data_inference(lines):
    """Scan data rows to infer which column contains dates and which contains numbers."""
    for header_idx in range(min(30, len(lines))):
        line = lines[header_idx]
        sep  = _best_separator(line)
        n    = len(line.split(sep))
        if n < 2:
            continue

        data_rows = [l for l in lines[header_idx + 1: header_idx + 8] if l.strip()]
        if len(data_rows) < 2:
            continue

        date_score   = [0] * n
        amount_score = [0] * n
        text_len     = [0] * n

        for row in data_rows:
            parts = row.split(sep)
            for i, part in enumerate(parts[:n]):
                clean = part.strip().strip('"')
                if _parse_date(clean):
                    date_score[i] += 1
                if _parse_amount(clean) is not None:
                    amount_score[i] += 1
                text_len[i] += len(clean)

        best_date   = max(range(n), key=lambda i: date_score[i])
        if date_score[best_date] < 2:
            continue

        candidates = [i for i in range(n) if i != best_date]
        best_amount = max(candidates, key=lambda i: amount_score[i], default=None)
        if best_amount is None or amount_score[best_amount] < 2:
            continue

        cm = {'fecha': best_date, 'importe': best_amount}
        used = {best_date, best_amount}
        remaining = [i for i in range(n) if i not in used]
        # Prefer non-date columns for concepto (avoids "fecha valor" being picked)
        non_date = [i for i in remaining if date_score[i] == 0]
        pool = non_date if non_date else remaining
        if pool:
            cm['concepto'] = max(pool, key=lambda i: text_len[i])
        # saldo: numeric column not already assigned
        for i in range(n):
            if i not in used and i != cm.get('concepto') and amount_score[i] >= 2:
                cm['saldo'] = i
                break

        return header_idx, cm, sep

    return None, None, None


def _build_col_map(cols, fecha_set, import_set, concepto_set, saldo_set,
                    cargo_set, abono_set, exact=True):
    cm = {}

    def match(col, names):
        return (col in names) if exact else any(kw in col for kw in names)

    for i, col in enumerate(cols):
        if 'fecha'   not in cm and match(col, fecha_set):    cm['fecha']   = i
        elif 'importe' not in cm and match(col, import_set): cm['importe'] = i
        elif 'concepto' not in cm and match(col, concepto_set): cm['concepto'] = i
        elif 'saldo'  not in cm and match(col, saldo_set):   cm['saldo']   = i
        elif 'cargo'  not in cm and match(col, cargo_set):   cm['cargo']   = i
        elif 'abono'  not in cm and match(col, abono_set):   cm['abono']   = i

    # Cargo/abono pair → synthetic importe
    if 'importe' not in cm and ('cargo' in cm or 'abono' in cm):
        cm['_use_cargo_abono'] = True

    # Need at least fecha + (importe or cargo/abono)
    if 'fecha' not in cm:
        return None
    if 'importe' not in cm and '_use_cargo_abono' not in cm:
        return None

    # Assign concepto fallback: first unused column
    if 'concepto' not in cm:
        used = set(cm.values())
        for i in range(len(cols)):
            if i not in used:
                cm['concepto'] = i
                break

    return cm


# ── Row parsing ────────────────────────────────────────────────────────────────

_DATE_FORMATS = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y',
                 '%Y/%m/%d', '%m/%d/%Y', '%d.%m.%Y']


def _parse_date(raw):
    raw = raw.strip().strip('"').strip("'")
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


def _build_concepto(row, col_map):
    """
    Build a description string by concatenating ALL non-special text cells in a row.
    Skips: fecha, importe, saldo, cargo, abono columns, date-formatted cells,
    pure-number cells, and empty/NaN cells.
    Deduplicates while preserving order.
    """
    special = {v for k, v in col_map.items() if isinstance(v, int)
                and k in ('fecha', 'importe', 'saldo', 'cargo', 'abono')}
    parts = []
    for i, cell in enumerate(row):
        if i in special:
            continue
        cell = cell.strip().strip('"').strip("'")
        if not cell or cell.lower() in ('nan', 'none', ''):
            continue
        # Skip date-formatted values (e.g. "2025-12-31 00:00:00")
        check = cell.split(' ')[0] if ' ' in cell else cell
        if _parse_date(check):
            continue
        # Skip pure-number cells (already captured as importe/saldo)
        if _parse_amount(cell) is not None and not any(c.isalpha() for c in cell):
            continue
        parts.append(cell)
    seen, deduped = set(), []
    for p in parts:
        if p not in seen:
            seen.add(p); deduped.append(p)
    return ' · '.join(deduped)


def _parse_amount(raw):
    raw = raw.strip().strip('"').strip("'").replace('\xa0', '').replace(' ', '')
    if not raw:
        return None
    # Strip currency symbols
    raw = raw.replace('€', '').replace('$', '').strip()
    if not raw:
        return None
    if ',' in raw and '.' in raw:
        # Spanish: 1.234,56
        raw = raw.replace('.', '').replace(',', '.')
    elif ',' in raw:
        raw = raw.replace(',', '.')
    raw = re.sub(r'[^\d.\-+]', '', raw)
    if not raw or raw in ('.', '-', '+'):
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _parse_rows(lines, start_idx, col_map, sep, headers=None):
    transactions = []
    warnings     = []
    use_ca       = col_map.get('_use_cargo_abono', False)

    for line_num, line in enumerate(lines[start_idx:], start=start_idx + 2):
        line = line.strip()
        if not line:
            continue

        parts = line.split(sep)
        max_idx = max(v for k, v in col_map.items() if isinstance(v, int))
        while len(parts) <= max_idx:
            parts.append('')

        raw_fecha = parts[col_map['fecha']] if 'fecha' in col_map else ''
        raw_saldo = parts[col_map['saldo']] if 'saldo' in col_map else ''

        fecha = _parse_date(raw_fecha)
        if not fecha:
            # silently skip non-date rows (totals, blank separators, etc.)
            continue

        if use_ca:
            cargo = _parse_amount(parts[col_map['cargo']])  if 'cargo' in col_map else None
            abono = _parse_amount(parts[col_map['abono']])  if 'abono' in col_map else None
            cargo = cargo or 0.0
            abono = abono or 0.0
            importe = abono - cargo
            if importe == 0 and cargo == 0 and abono == 0:
                continue
        else:
            raw_importe = parts[col_map['importe']] if 'importe' in col_map else ''
            importe = _parse_amount(raw_importe)
            if importe is None:
                warnings.append(f"Fila {line_num}: importe no reconocido '{raw_importe}' — omitida")
                continue

        saldo    = _parse_amount(raw_saldo) if raw_saldo.strip() else None
        concepto = _build_concepto(parts, col_map)

        # Build raw_data: all original column header → value pairs
        raw_data = None
        if headers:
            raw_data = {}
            for i, h in enumerate(headers):
                val = parts[i].strip().strip('"').strip("'") if i < len(parts) else ''
                if h and val and val.lower() not in ('nan', 'none'):
                    raw_data[h] = val

        transactions.append({
            'fecha':    fecha,
            'concepto': concepto,
            'importe':  importe,
            'saldo':    saldo,
            'raw_data': raw_data,
        })

    return transactions, warnings


# ── Excel parser ──────────────────────────────────────────────────────────────

def _parse_excel(file_storage, ext):
    """Parse .xls / .xlsx via pandas, reusing the same output format."""
    try:
        import pandas as pd
    except ImportError:
        raise ValueError("pandas no está instalado. Ejecuta setup.bat para instalarlo.")

    raw = file_storage.read()
    engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'

    try:
        # Read all as strings so we control date/number parsing ourselves
        df = pd.read_excel(io.BytesIO(raw), engine=engine,
                           header=None, dtype=str, na_filter=False)
    except ImportError:
        pkg = 'openpyxl' if ext == '.xlsx' else 'xlrd'
        raise ValueError(
            f"Falta el módulo '{pkg}'. Ejecuta: python -m pip install {pkg}"
        )
    except Exception as e:
        raise ValueError(f"No se pudo leer el archivo Excel: {e}")

    if df.empty:
        raise ValueError("El archivo Excel está vacío.")

    # Convert DataFrame to a list-of-lists (same as CSV lines split by sep)
    matrix = [[str(v).strip() for v in row] for _, row in df.iterrows()]

    # Reuse the same header-detection strategies, adapted for matrix rows
    header_idx, col_map = _find_header_in_matrix(matrix)
    if header_idx is None:
        raise ValueError(
            "No se pudo detectar columnas de fecha e importe en el archivo Excel."
        )

    # Extract original column headers for raw_data storage
    headers = [str(c).strip() for c in matrix[header_idx]]
    transactions, warnings = _parse_matrix_rows(matrix, header_idx + 1, col_map, headers=headers)

    if not transactions:
        raise ValueError("El archivo Excel no contiene filas con fecha e importe válidos.")

    transactions.sort(key=lambda x: x['fecha'])

    saldo_inicial = None
    saldo_final   = None
    if transactions[0].get('saldo') is not None:
        saldo_inicial = round(transactions[0]['saldo'] - transactions[0]['importe'], 2)
    if transactions[-1].get('saldo') is not None:
        saldo_final = transactions[-1]['saldo']

    return {
        'transactions':     transactions,
        'saldo_inicial':    saldo_inicial,
        'saldo_final':      saldo_final,
        'date_from':        transactions[0]['fecha'],
        'date_to':          transactions[-1]['fecha'],
        'warnings':         warnings,
        'detected_columns': col_map,
    }


def _find_header_in_matrix(matrix):
    """Like _find_header_any but operates on List[List[str]] (no separator needed)."""
    for strategy in (_strat_exact_mat, _strat_partial_mat, _strat_data_mat):
        result = strategy(matrix)
        if result[0] is not None:
            return result
    return None, None


def _strat_exact_mat(matrix):
    for idx, row in enumerate(matrix[:40]):
        cols = [_normalize(c) for c in row]
        cm = _build_col_map(cols, _EXACT_FECHA, _EXACT_IMPORT, _EXACT_CONCEPTO,
                            _EXACT_SALDO, _EXACT_CARGO, _EXACT_ABONO, exact=True)
        if cm:
            return idx, cm
    return None, None


def _strat_partial_mat(matrix):
    for idx, row in enumerate(matrix[:40]):
        cols = [_normalize(c) for c in row]
        cm = _build_col_map(cols, _PARTIAL_FECHA, _PARTIAL_IMPORT, _PARTIAL_CONCEPTO,
                            _PARTIAL_SALDO, _PARTIAL_CARGO, _PARTIAL_ABONO, exact=False)
        if cm:
            return idx, cm
    return None, None


def _strat_data_mat(matrix):
    for header_idx in range(min(20, len(matrix))):
        row = matrix[header_idx]
        n   = len(row)
        if n < 2:
            continue
        data_rows = [r for r in matrix[header_idx + 1: header_idx + 8] if any(c.strip() for c in r)]
        if len(data_rows) < 2:
            continue

        date_score   = [0] * n
        amount_score = [0] * n
        text_len     = [0] * n

        for dr in data_rows:
            for i, part in enumerate(dr[:n]):
                clean = part.strip()
                if _parse_date(clean):
                    date_score[i] += 1
                if _parse_amount(clean) is not None:
                    amount_score[i] += 1
                text_len[i] += len(clean)

        best_date = max(range(n), key=lambda i: date_score[i])
        if date_score[best_date] < 2:
            continue
        candidates = [i for i in range(n) if i != best_date]
        best_amount = max(candidates, key=lambda i: amount_score[i], default=None)
        if best_amount is None or amount_score[best_amount] < 2:
            continue

        cm = {'fecha': best_date, 'importe': best_amount}
        used = {best_date, best_amount}
        remaining = [i for i in range(n) if i not in used]
        # Prefer non-date columns for concepto (avoids "fecha valor" being picked)
        non_date = [i for i in remaining if date_score[i] == 0]
        pool = non_date if non_date else remaining
        if pool:
            cm['concepto'] = max(pool, key=lambda i: text_len[i])
        for i in range(n):
            if i not in used and i != cm.get('concepto') and amount_score[i] >= 2:
                cm['saldo'] = i
                break
        return header_idx, cm
    return None, None


def _parse_matrix_rows(matrix, start_idx, col_map, headers=None):
    """Same as _parse_rows but operates on List[List[str]] instead of split lines."""
    transactions = []
    warnings     = []
    use_ca       = col_map.get('_use_cargo_abono', False)
    max_idx      = max(v for k, v in col_map.items() if isinstance(v, int))

    for row_num, row in enumerate(matrix[start_idx:], start=start_idx + 2):
        while len(row) <= max_idx:
            row.append('')

        raw_fecha = row[col_map['fecha']] if 'fecha' in col_map else ''
        raw_saldo = row[col_map['saldo']] if 'saldo' in col_map else ''

        # pandas may give '2025-01-05 00:00:00' for date cells — trim time
        raw_fecha = raw_fecha.split(' ')[0] if ' ' in raw_fecha else raw_fecha

        fecha = _parse_date(raw_fecha)
        if not fecha:
            continue

        if use_ca:
            cargo   = _parse_amount(row[col_map['cargo']])  if 'cargo' in col_map else None
            abono   = _parse_amount(row[col_map['abono']])  if 'abono' in col_map else None
            importe = (abono or 0) - (cargo or 0)
            if importe == 0:
                continue
        else:
            raw_imp = row[col_map['importe']] if 'importe' in col_map else ''
            importe = _parse_amount(raw_imp)
            if importe is None:
                warnings.append(f"Fila {row_num}: importe no reconocido — omitida")
                continue

        saldo    = _parse_amount(raw_saldo) if raw_saldo.strip() else None
        concepto = _build_concepto(row, col_map)

        # Build raw_data: all original column header → value pairs
        raw_data = None
        if headers:
            raw_data = {}
            for i, h in enumerate(headers):
                val = str(row[i]).strip() if i < len(row) else ''
                if h and val and val.lower() not in ('nan', 'none', ''):
                    raw_data[h] = val

        transactions.append({
            'fecha':    fecha,
            'concepto': concepto,
            'importe':  importe,
            'saldo':    saldo,
            'raw_data': raw_data,
        })

    return transactions, warnings


# ── Period names ───────────────────────────────────────────────────────────────

_MESES = ['','Enero','Febrero','Marzo','Abril','Mayo','Junio',
          'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
