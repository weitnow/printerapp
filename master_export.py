import pandas as pd
import sqlite3

# --- CONFIG ---
db_file = "printers.db"
output_xlsx = "Druckerliste_CARI_export.xlsx"

# --- STEP 1: Connect to SQLite ---
conn = sqlite3.connect(db_file)

# --- STEP 2: Query 1 - Bureau-printer-slot-caridoc combinations ---
# Uses Bemerkung from slot_caridocs (normal slots)
query_with_caridocs = """
SELECT 
    l.Standort as Standort,
    b.Bureau as Bureau,
    b.BureauID as 'Bureau-ID',
    pn.PrinterName as Druckername,
    ps.SlotName as 'Schacht Name',
    sc.CARIdoc as CARIdoc,
    ps.PaperFormat as Format,
    CASE WHEN ps.TwoSided = 1 THEN '2-sided' ELSE '' END as '2-sided',
    CASE WHEN ps.Inspect = 1 THEN 'TRUE' ELSE 'FALSE' END as Inspect,
    f.Fachabteilung as Fachabteilung,
    pn.PrinterModel as 'Drucker Modell',
    sc.Bemerkung as Bemerkung   -- Bemerkung from slot_caridocs (bureau slots)
FROM 
    slot_caridocs sc
    JOIN printerslots ps ON sc.PrinterName = ps.PrinterName AND sc.SlotName = ps.SlotName
    JOIN printernames pn ON ps.PrinterName = pn.PrinterName
    JOIN bureaus b ON sc.BureauID = b.BureauID
    LEFT JOIN fachabteilung f ON b.FachabteilungID = f.FachabteilungID
    LEFT JOIN lieugestion l ON b.StandortID = l.StandortID
"""

# --- STEP 3: Query 2 - Printers/slots without any bureau connection ---
# Now includes Bemerkung from printerslots (Inspect=True slots)
query_printers_without_bureaus = """
SELECT 
    NULL as Standort,
    NULL as Bureau,
    NULL as 'Bureau-ID',
    pn.PrinterName as Druckername,
    ps.SlotName as 'Schacht Name',
    NULL as CARIdoc,
    ps.PaperFormat as Format,
    CASE WHEN ps.TwoSided = 1 THEN '2-sided' ELSE '' END as '2-sided',
    CASE WHEN ps.Inspect = 1 THEN 'TRUE' ELSE 'FALSE' END as Inspect,
    NULL as Fachabteilung,
    pn.PrinterModel as 'Drucker Modell',
    ps.Bemerkung as Bemerkung   -- 🔥 NEW: Bemerkung taken from printerslots
FROM 
    printerslots ps
    JOIN printernames pn ON ps.PrinterName = pn.PrinterName
WHERE NOT EXISTS (
    SELECT 1 FROM slot_caridocs sc 
    WHERE sc.PrinterName = ps.PrinterName AND sc.SlotName = ps.SlotName
)
"""

# --- STEP 4: Query 3 - Bureaus without any printer connection ---
query_bureaus_without_printers = """
SELECT 
    l.Standort as Standort,
    b.Bureau as Bureau,
    b.BureauID as 'Bureau-ID',
    NULL as Druckername,
    NULL as 'Schacht Name',
    NULL as CARIdoc,
    NULL as Format,
    '' as '2-sided',
    'FALSE' as Inspect,
    f.Fachabteilung as Fachabteilung,
    NULL as 'Drucker Modell',
    NULL as Bemerkung
FROM 
    bureaus b
    LEFT JOIN fachabteilung f ON b.FachabteilungID = f.FachabteilungID
    LEFT JOIN lieugestion l ON b.StandortID = l.StandortID
WHERE NOT EXISTS (
    SELECT 1 FROM slot_caridocs sc WHERE sc.BureauID = b.BureauID
)
"""

# --- STEP 5: Execute all queries and combine ---
df1 = pd.read_sql_query(query_with_caridocs, conn)
df2 = pd.read_sql_query(query_printers_without_bureaus, conn)
df3 = pd.read_sql_query(query_bureaus_without_printers, conn)

# Combine all dataframes
df = pd.concat([df1, df2, df3], ignore_index=True)

# --- STEP 6: Sort the combined data ---
df = df.sort_values(
    by=['Standort', 'Bureau', 'Druckername', 'Schacht Name', 'CARIdoc'],
    na_position='last'
)

# --- STEP 7: Close database connection ---
conn.close()

# --- STEP 8: Write to Excel ---
df.to_excel(output_xlsx, index=False, sheet_name='Druckerliste')

print(f"Export completed successfully!")
print(f"Created: {output_xlsx}")
print(f"Total rows: {len(df)}")
print(f"  - Rows with bureau-printer connections: {len(df1)}")
print(f"  - Rows with printers without bureaus: {len(df2)}")
print(f"  - Rows with bureaus without printers: {len(df3)}")
print(f"\nColumn structure:")
print(df.columns.tolist())
