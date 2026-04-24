import sqlite3
import json
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "orders.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            customer_phone TEXT,
            language TEXT,
            items TEXT,
            address TEXT,
            status TEXT DEFAULT 'confirmed',
            raw_transcript TEXT,
            confirmed_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_order(order_id: str, order_data: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT OR REPLACE INTO orders
        (id, customer_phone, language, items, address, status, raw_transcript, confirmed_at)
        VALUES (?, ?, ?, ?, ?, 'confirmed', ?, ?)
    """, (
        order_id,
        order_data.get("customer_phone", "unknown"),
        order_data.get("language", "en-IN"),
        json.dumps(order_data.get("items", [])),
        order_data.get("address", ""),
        order_data.get("raw_transcript", ""),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

def get_orders(limit=50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM orders ORDER BY confirmed_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["items"] = json.loads(d["items"]) if d["items"] else []
        result.append(d)
    return result
