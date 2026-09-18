import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from ..config import settings

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    email TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vendors (
    vendor_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    trusted_domains TEXT NOT NULL, -- JSON array
    contact_phone TEXT NOT NULL,
    contact_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vendor_accounts (
    id TEXT PRIMARY KEY,
    vendor_id TEXT NOT NULL,
    bank_name TEXT NOT NULL,
    routing_number TEXT NOT NULL,
    account_number_last4 TEXT NOT NULL,
    full_account_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    FOREIGN KEY(vendor_id) REFERENCES vendors(vendor_id)
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    po_number TEXT PRIMARY KEY,
    vendor_id TEXT NOT NULL,
    vendor_name TEXT NOT NULL,
    amount TEXT NOT NULL,
    currency TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_history (
    payment_id TEXT PRIMARY KEY,
    vendor_id TEXT NOT NULL,
    amount TEXT NOT NULL,
    currency TEXT NOT NULL,
    paid_date TEXT NOT NULL,
    invoice_ref TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    case_number TEXT UNIQUE NOT NULL,
    vendor_id TEXT,
    vendor_name TEXT,
    invoice_reference TEXT,
    amount TEXT NOT NULL,
    currency TEXT NOT NULL,
    state TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    rule_version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_objects (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    byte_size INTEGER NOT NULL,
    local_path TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS normalized_fields (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    name TEXT NOT NULL,
    raw_value TEXT,
    normalized_value TEXT,
    evidence_id TEXT,
    extraction_method TEXT NOT NULL,
    source_locator TEXT,
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    title TEXT NOT NULL,
    explanation TEXT NOT NULL,
    evidence_ids TEXT NOT NULL, -- JSON array
    origin TEXT NOT NULL,
    metadata TEXT NOT NULL, -- JSON
    created_at TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    state TEXT NOT NULL,
    reason_codes TEXT NOT NULL, -- JSON array
    required_actions TEXT NOT NULL, -- JSON array
    ai_summary TEXT,
    ai_confidence TEXT,
    ai_intent_analysis TEXT, -- JSON
    ai_contradictions TEXT, -- JSON array
    generated_at TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS verification_callbacks (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    verified_by TEXT NOT NULL,
    callback_phone_used TEXT NOT NULL,
    vendor_contact_spoken TEXT NOT NULL,
    confirmation_method TEXT NOT NULL,
    is_confirmed INTEGER NOT NULL,
    notes TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    case_id TEXT,
    actor_id TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    payload_redacted TEXT NOT NULL, -- JSON
    previous_event_hash TEXT,
    event_hash TEXT NOT NULL
);
"""

def init_db(db_path: Path | None = None) -> None:
    path = db_path or settings.database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(path)) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()

@contextmanager
def get_db(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    path = db_path or settings.database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
