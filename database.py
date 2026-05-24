# database.py
import sqlite3
from flask import g

DATABASE = 'flowforge.db'


def get_db():
    """Return a database connection tied to the Flask request context.
    The connection is opened once per request and automatically closed
    by close_db() when the request/app context tears down.
    """
    if 'db' not in g:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        # Enforce foreign-key constraints at the connection level
        conn.execute('PRAGMA foreign_keys = ON')
        g.db = conn
    return g.db


def close_db(e=None):
    """Close the database connection at the end of the request context."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Create all tables if they don't exist, and run any required
    schema migrations safely (will never delete existing data).
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # ── Core Tables ───────────────────────────────────────────────

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            title   TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT NOT NULL,
            sku            TEXT UNIQUE NOT NULL,
            purchase_price REAL NOT NULL DEFAULT 0,
            unit_price     REAL NOT NULL,
            gst_percent    REAL DEFAULT 0,
            stock_qty      INTEGER DEFAULT 0,
            min_stock      INTEGER DEFAULT 10,
            description    TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendors (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT NOT NULL,
            email   TEXT,
            phone   TEXT,
            address TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT NOT NULL,
            email   TEXT,
            phone   TEXT,
            address TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id  INTEGER NOT NULL,
            status       TEXT DEFAULT 'pending',
            total_amount REAL DEFAULT 0,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity   INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY (order_id)   REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id    INTEGER NOT NULL,
            status       TEXT DEFAULT 'pending',
            total_amount REAL DEFAULT 0,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchase_order_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id       INTEGER NOT NULL,
            product_id  INTEGER NOT NULL,
            quantity    INTEGER NOT NULL,
            unit_price  REAL NOT NULL,
            gst_percent REAL DEFAULT 0,
            FOREIGN KEY (po_id)       REFERENCES purchase_orders(id),
            FOREIGN KEY (product_id)  REFERENCES products(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            status      TEXT DEFAULT 'pending',
            subtotal    REAL DEFAULT 0,
            gst_amount  REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id)    REFERENCES orders(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id              INTEGER PRIMARY KEY,
            company_name    TEXT DEFAULT 'My Company',
            company_email   TEXT,
            company_phone   TEXT,
            company_address TEXT,
            gstin           TEXT,
            invoice_prefix  TEXT DEFAULT 'INV-',
            logo_filename   TEXT
        )
    ''')

    # ── Default Settings Row ──────────────────────────────────────
    cursor.execute('''
        INSERT OR IGNORE INTO settings (id, company_name, invoice_prefix)
        VALUES (1, 'My Company', 'INV-')
    ''')

    # ── Safe Schema Migrations (zero data loss) ───────────────────
    # Add min_stock column to products table if it doesn't exist yet.
    # This handles existing databases that were created before this column.
    existing_columns = [
        row[1] for row in cursor.execute('PRAGMA table_info(products)').fetchall()
    ]
    if 'min_stock' not in existing_columns:
        cursor.execute(
            'ALTER TABLE products ADD COLUMN min_stock INTEGER DEFAULT 10'
        )

    conn.commit()
    conn.close()