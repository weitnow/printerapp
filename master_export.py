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
    CASE WHEN ps.Autoprint = 1 THEN 'TRUE' ELSE 'FALSE' END as Autoprint,
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
# Now includes Bemerkung from printerslots (Autoprint=True slots)
query_printers_without_bureaus = """
SELECT 
    l.Standort as Standort,
    NULL as Bureau,
    NULL as 'Bureau-ID',
    pn.PrinterName as Druckername,
    ps.SlotName as 'Schacht Name',
    NULL as CARIdoc,
    ps.PaperFormat as Format,
    CASE WHEN ps.TwoSided = 1 THEN '2-sided' ELSE '' END as '2-sided',
    CASE WHEN ps.Autoprint = 1 THEN 'TRUE' ELSE 'FALSE' END as Autoprint,
    NULL as Fachabteilung,
    pn.PrinterModel as 'Drucker Modell',
    ps.Bemerkung as Bemerkung   -- Bemerkung taken from printerslots
FROM 
    printerslots ps
    JOIN printernames pn ON ps.PrinterName = pn.PrinterName
    LEFT JOIN lieugestion l ON pn.StandortID = l.StandortID
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
    'FALSE' as Autoprint,
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
df_printers = pd.concat([df1, df2, df3], ignore_index=True)

# --- STEP 6: Sort the combined data ---
df_printers = df_printers.sort_values(
    by=['Standort', 'Bureau', 'Druckername', 'Schacht Name', 'CARIdoc'],
    na_position='last'
)

# --- STEP 7: Export CARIdocs (Forms) for second sheet ---
query_caridocs = """
SELECT 
    c.CARIdoc as Formular,
    c.FormatCARIDoc as 'Format CARI-Doc',
    c.FormatDruckeinlage as 'Format Druckeinlage',
    c.BeschreibungFormular as 'Beschreibung Formular',
    c.CanonPrinterSettings as 'Canon Printer Settings'
FROM 
    caridocs c
ORDER BY 
    c.CARIdoc
"""

df_forms = pd.read_sql_query(query_caridocs, conn)

# --- STEP 8: Close database connection ---
conn.close()

# --- STEP 9: Write to Excel with both sheets ---
with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
    df_printers.to_excel(writer, index=False, sheet_name='Druckerliste')
    df_forms.to_excel(writer, index=False, sheet_name='Forms')

print(f"✅ Export completed successfully!")
print(f"Created: {output_xlsx}")
print(f"\n📄 Sheet 1 - Druckerliste:")
print(f"  Total rows: {len(df_printers)}")
print(f"  - Rows with bureau-printer connections: {len(df1)}")
print(f"  - Rows with printers without bureaus: {len(df2)}")
print(f"  - Rows with bureaus without printers: {len(df3)}")
print(f"\n📄 Sheet 2 - Forms:")
print(f"  Total CARIdocs: {len(df_forms)}")
print(f"\nColumn structure (Sheet 1):")
print(df_printers.columns.tolist())
print(f"\nColumn structure (Sheet 2):")
print(df_forms.columns.tolist())