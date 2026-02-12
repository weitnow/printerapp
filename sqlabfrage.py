import sqlite3

conn = sqlite3.connect("printers.db")
cur = conn.cursor()

cur.execute("""
SELECT
    sc.PrinterName,
    COUNT(DISTINCT b.StandortID) AS Anzahl_Standorte
FROM slot_caridocs sc
JOIN bureaus b ON sc.BureauID = b.BureauID
GROUP BY sc.PrinterName
HAVING COUNT(DISTINCT b.StandortID) > 1;
""")

for row in cur.fetchall():
    print(row)

conn.close()
