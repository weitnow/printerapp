import sqlite3
from contextlib import contextmanager

DB_FILE = "printers.db"

@contextmanager
def get_connection():
    """Get database connection with foreign keys enabled"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # DEBUG: Verify foreign keys are enabled
    result = conn.execute("PRAGMA foreign_keys").fetchone()
    print(f"Foreign keys enabled: {result[0]}")  # Should print: Foreign keys enabled: 1
    
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()