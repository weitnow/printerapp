import sqlite3

db_file = "printers.db"                 # change to your DB file
output_file = "db_constraints.txt"  # output file name

conn = sqlite3.connect(db_file)
cur = conn.cursor()

lines = []

# Get all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]

for table in tables:
    lines.append("="*40)
    lines.append(f"TABLE: {table}")
    lines.append("="*40 + "\n")

    # Schema / CREATE TABLE
    cur.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'")
    schema = cur.fetchone()[0]
    lines.append("Schema:")
    lines.append(schema + "\n")

    # Columns (type, nullability, default, PK)
    lines.append("Columns:")
    cur.execute(f"PRAGMA table_info({table})")
    for col in cur.fetchall():
        # tuple: (cid, name, type, notnull, dflt_value, pk)
        lines.append(str(col))
    lines.append("")

    # Foreign keys
    lines.append("Foreign Keys:")
    cur.execute(f"PRAGMA foreign_key_list({table})")
    lines.append(str(cur.fetchall()) + "\n")

    # Unique indexes
    lines.append("Unique Indexes:")
    cur.execute(f"PRAGMA index_list({table})")
    for idx in cur.fetchall():
        if idx[2] == 1:  # unique index flag
            lines.append(str(idx))
    lines.append("")

# Write to TXT file
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Finished! Results written to {output_file}")
