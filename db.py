import sqlite3

DB_FILE = "printers.db"

def get_connection():
    return sqlite3.connect(DB_FILE)
