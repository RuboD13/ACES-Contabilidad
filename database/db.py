import sqlite3
import json
import os
from config import DB_PATH, SEED_RULES


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


_SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT DEFAULT '',
    color       TEXT DEFAULT '#6366f1',
    icon        TEXT DEFAULT 'book',
    iban        TEXT DEFAULT '',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS periods (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id      INTEGER NOT NULL DEFAULT 1 REFERENCES accounts(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    date_from       TEXT NOT NULL,
    date_to         TEXT NOT NULL,
    tipo            TEXT NOT NULL DEFAULT 'banco',
    saldo_inicial   REAL,
    saldo_final_csv REAL,
    csv_filename    TEXT,
    imported_at     TEXT DEFAULT (datetime('now')),
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    period_id           INTEGER NOT NULL REFERENCES periods(id) ON DELETE CASCADE,
    fecha               TEXT NOT NULL,
    concepto            TEXT NOT NULL,
    importe             REAL NOT NULL,
    saldo               REAL,
    is_income           INTEGER NOT NULL,
    category_key        TEXT DEFAULT 'sin_categoria',
    rule_id             INTEGER REFERENCES categorization_rules(id),
    is_manual_override  INTEGER DEFAULT 0,
    confidence          REAL DEFAULT 0.0,
    notes               TEXT,
    factura_status      TEXT DEFAULT 'sin_factura',
    raw_data            TEXT DEFAULT NULL,
    created_at          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categorization_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category_key    TEXT NOT NULL,
    category_label  TEXT NOT NULL,
    category_type   TEXT NOT NULL,
    keywords        TEXT NOT NULL DEFAULT '[]',
    priority        INTEGER DEFAULT 100,
    is_active       INTEGER DEFAULT 1,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tags (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    color         TEXT DEFAULT '#6366f1',
    account_id    INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    keywords      TEXT DEFAULT '[]',
    is_auto_apply INTEGER DEFAULT 0,
    is_system     INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transaction_tags (
    transaction_id INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    tag_id         INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (transaction_id, tag_id)
);

CREATE TABLE IF NOT EXISTS facturas (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER REFERENCES transactions(id) ON DELETE SET NULL,
    account_id     INTEGER NOT NULL DEFAULT 1 REFERENCES accounts(id),
    filename       TEXT NOT NULL,
    original_name  TEXT NOT NULL,
    file_size      INTEGER DEFAULT 0,
    mime_type      TEXT DEFAULT '',
    fecha_factura  TEXT DEFAULT '',
    numero_factura TEXT DEFAULT '',
    proveedor      TEXT DEFAULT '',
    importe        REAL,
    trimestre      TEXT DEFAULT '',
    notes          TEXT DEFAULT '',
    uploaded_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS action_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id  INTEGER DEFAULT 1,
    action_type TEXT NOT NULL,
    description TEXT NOT NULL,
    tx_id       INTEGER,
    details     TEXT DEFAULT NULL,
    created_at  TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_action_log_account ON action_log(account_id);

CREATE INDEX IF NOT EXISTS idx_tx_period   ON transactions(period_id);
CREATE INDEX IF NOT EXISTS idx_tx_fecha    ON transactions(fecha);
CREATE INDEX IF NOT EXISTS idx_tx_category ON transactions(category_key);
CREATE INDEX IF NOT EXISTS idx_periods_account ON periods(account_id);
CREATE INDEX IF NOT EXISTS idx_facturas_account ON facturas(account_id);
CREATE INDEX IF NOT EXISTS idx_facturas_tx ON facturas(transaction_id);
"""


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    try:
        # Migrate first so existing tables have the new columns before indexes are created
        _migrate(conn)
        conn.commit()
        conn.executescript(_SCHEMA)
        _seed_default_account(conn)
        _seed_rules(conn)
        conn.commit()
    finally:
        conn.close()


def _migrate(conn):
    """Add columns/tables that didn't exist in earlier versions. Safe no-op on fresh install."""
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    if 'periods' not in tables:
        return  # fresh install — CREATE TABLE will add all columns directly
    period_cols = [r[1] for r in conn.execute("PRAGMA table_info(periods)").fetchall()]
    if 'account_id' not in period_cols:
        conn.execute("ALTER TABLE periods ADD COLUMN account_id INTEGER DEFAULT 1")

    # accounts table migrations
    if 'accounts' in tables:
        acct_cols = [r[1] for r in conn.execute("PRAGMA table_info(accounts)").fetchall()]
        if 'iban' not in acct_cols:
            conn.execute("ALTER TABLE accounts ADD COLUMN iban TEXT DEFAULT ''")

    # transactions table migrations
    if 'transactions' in tables:
        tx_cols = [r[1] for r in conn.execute("PRAGMA table_info(transactions)").fetchall()]
        if 'raw_data' not in tx_cols:
            conn.execute("ALTER TABLE transactions ADD COLUMN raw_data TEXT DEFAULT NULL")
        if 'factura_status' not in tx_cols:
            conn.execute("ALTER TABLE transactions ADD COLUMN factura_status TEXT DEFAULT 'sin_factura'")
    # action_log table migrations
    if 'action_log' in tables:
        log_cols = [r[1] for r in conn.execute("PRAGMA table_info(action_log)").fetchall()]
        if 'details' not in log_cols:
            conn.execute("ALTER TABLE action_log ADD COLUMN details TEXT DEFAULT NULL")
    # tags table migrations
    if 'tags' in tables:
        tag_cols = [r[1] for r in conn.execute("PRAGMA table_info(tags)").fetchall()]
        if 'keywords' not in tag_cols:
            conn.execute("ALTER TABLE tags ADD COLUMN keywords TEXT DEFAULT '[]'")
        if 'is_auto_apply' not in tag_cols:
            conn.execute("ALTER TABLE tags ADD COLUMN is_auto_apply INTEGER DEFAULT 0")
        if 'is_system' not in tag_cols:
            conn.execute("ALTER TABLE tags ADD COLUMN is_system INTEGER DEFAULT 0")
    # New tables added later — already handled by CREATE TABLE IF NOT EXISTS in _SCHEMA


def _seed_default_account(conn):
    if conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO accounts (id, name, description, color, icon) VALUES (1,?,?,?,?)",
            ('ACES Alquiler', 'Cuenta principal', '#6366f1', 'buildings'),
        )


def _seed_rules(conn):
    existing = {r[0] for r in conn.execute("SELECT category_key FROM categorization_rules").fetchall()}
    for rule in SEED_RULES:
        if rule['key'] not in existing:
            conn.execute(
                """INSERT INTO categorization_rules
                   (category_key, category_label, category_type, keywords, priority)
                   VALUES (?, ?, ?, ?, ?)""",
                (rule['key'], rule['label'], rule['type'],
                 json.dumps(rule['keywords'], ensure_ascii=False), rule['priority']),
            )


# ── helpers ────────────────────────────────────────────────────────────────────

def get_all_accounts(conn):
    return conn.execute("SELECT * FROM accounts ORDER BY name").fetchall()


def get_account(conn, account_id):
    return conn.execute("SELECT * FROM accounts WHERE id=?", [account_id]).fetchone()


def get_all_periods(conn, account_id=None):
    if account_id:
        return conn.execute(
            "SELECT * FROM periods WHERE account_id=? ORDER BY date_from DESC", [account_id]
        ).fetchall()
    return conn.execute("SELECT * FROM periods ORDER BY date_from DESC").fetchall()


def get_period(conn, period_id):
    return conn.execute("SELECT * FROM periods WHERE id=?", [period_id]).fetchone()


def get_latest_period(conn, account_id=None):
    if account_id:
        return conn.execute(
            "SELECT * FROM periods WHERE account_id=? ORDER BY imported_at DESC LIMIT 1",
            [account_id],
        ).fetchone()
    return conn.execute(
        "SELECT * FROM periods ORDER BY imported_at DESC LIMIT 1"
    ).fetchone()


def get_active_rules(conn):
    return conn.execute(
        "SELECT * FROM categorization_rules WHERE is_active=1 ORDER BY priority"
    ).fetchall()


def log_action_db(conn, action_type, description, account_id=1, tx_id=None, details=None):
    """Insert an entry in action_log. Does NOT commit — caller must commit."""
    conn.execute(
        "INSERT INTO action_log (account_id, action_type, description, tx_id, details) VALUES (?,?,?,?,?)",
        (account_id, action_type, description, tx_id,
         json.dumps(details, ensure_ascii=False) if details else None)
    )
