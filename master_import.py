import pandas as pd
import sqlite3

# --- CONFIG ---
xlsx_file = "Druckerliste_CARI.xlsx"
db_file = "printers.db"
sheet_name_printers = 0
sheet_name_forms = 1  # Second sheet with form data

# --- STEP 1: Read Excel ---
df_printers = pd.read_excel(xlsx_file, sheet_name=sheet_name_printers)
df_forms = pd.read_excel(xlsx_file, sheet_name=sheet_name_forms)

# --- STEP 2: Connect to SQLite ---
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# --- STEP 2.5: Drop all tables if they exist ---
cursor.execute("DROP TABLE IF EXISTS slot_caridocs")
cursor.execute("DROP TABLE IF EXISTS printerslots")
cursor.execute("DROP TABLE IF EXISTS bureaus")
cursor.execute("DROP TABLE IF EXISTS printernames")
cursor.execute("DROP TABLE IF EXISTS printermodels")
cursor.execute("DROP TABLE IF EXISTS fachabteilung")
cursor.execute("DROP TABLE IF EXISTS lieugestion")
cursor.execute("DROP TABLE IF EXISTS caridocs")
cursor.execute("DROP TABLE IF EXISTS druckeinlage")
cursor.execute("DROP TABLE IF EXISTS printersettings")


# --- STEP 3: Create tables with improved constraints ---
conn.execute("PRAGMA foreign_keys = ON;")

# Standorte (Locations)
cursor.execute("""
CREATE TABLE IF NOT EXISTS lieugestion (
    StandortID INTEGER PRIMARY KEY,
    Standort TEXT NOT NULL UNIQUE,
    CHECK (length(trim(Standort)) > 0)  -- No empty/whitespace-only strings
)
""")

# Fachabteilungen (Departments)
cursor.execute("""
CREATE TABLE IF NOT EXISTS fachabteilung (
    FachabteilungID INTEGER PRIMARY KEY,
    Fachabteilung TEXT NOT NULL UNIQUE,
    CHECK (length(trim(Fachabteilung)) > 0)  -- No empty/whitespace-only strings
)
""")

# Printer Models
cursor.execute("""
CREATE TABLE IF NOT EXISTS printermodels (
    PrinterModel TEXT PRIMARY KEY,
    CHECK (length(trim(PrinterModel)) > 0)  -- No empty/whitespace-only strings
)
""")

# Druckeinlagen (Print Forms) - NULL or positive values only
cursor.execute("""
CREATE TABLE IF NOT EXISTS druckeinlage (
    FormatDruckeinlage TEXT PRIMARY KEY,
    WidthMM REAL CHECK (WidthMM IS NULL OR WidthMM > 0),   -- NULL or positive only
    HeightMM REAL CHECK (HeightMM IS NULL OR HeightMM > 0), -- NULL or positive only
    CHECK (length(trim(FormatDruckeinlage)) > 0)  -- No empty format names
)
""")

# Printer Settings (Canon)
cursor.execute("""
CREATE TABLE IF NOT EXISTS printersettings (
    CanonPrinterSettings TEXT PRIMARY KEY,
    SettingsPNG BLOB,  -- Binary data for settings image
    CHECK (length(trim(CanonPrinterSettings)) > 0)  -- No empty setting names
)
""")

# CARIdocs (Forms)
cursor.execute("""
CREATE TABLE IF NOT EXISTS caridocs (
    CARIdoc TEXT PRIMARY KEY,
    FormatCARIDoc TEXT,
    FormatDruckeinlage TEXT,
    BeschreibungFormular TEXT,
    CanonPrinterSettings TEXT,
    
    CHECK (length(trim(CARIdoc)) > 0),  -- No empty CARIdoc names
               
    FOREIGN KEY (FormatDruckeinlage)
        REFERENCES druckeinlage(FormatDruckeinlage)
        ON DELETE RESTRICT,

    FOREIGN KEY (CanonPrinterSettings)
        REFERENCES printersettings(CanonPrinterSettings)
        ON DELETE RESTRICT
)
""")

# Printer Names
cursor.execute("""
CREATE TABLE IF NOT EXISTS printernames (
    PrinterName TEXT PRIMARY KEY,
    PrinterModel TEXT NOT NULL,
    StandortID INTEGER,  -- Optional: printers without location allowed
    
    CHECK (length(trim(PrinterName)) > 0),  -- No empty printer names
               
    FOREIGN KEY (PrinterModel)
        REFERENCES printermodels(PrinterModel)
        ON DELETE RESTRICT,

    FOREIGN KEY (StandortID)
        REFERENCES lieugestion(StandortID)
        ON DELETE RESTRICT
)
""")

# Printer Slots (Schächte)
cursor.execute("""
CREATE TABLE IF NOT EXISTS printerslots (
    PrinterName TEXT NOT NULL,
    SlotName TEXT NOT NULL,
    PaperFormat TEXT,
    TwoSided BOOLEAN NOT NULL DEFAULT 0,  -- Default to one-sided
    Autoprint BOOLEAN NOT NULL DEFAULT 0,   -- Default to no autoprint
    Bemerkung TEXT,
    
    CHECK (length(trim(PrinterName)) > 0),  -- No empty names
    CHECK (length(trim(SlotName)) > 0),     -- No empty slot names
               
    PRIMARY KEY (PrinterName, SlotName),
               
    FOREIGN KEY (PrinterName)
        REFERENCES printernames(PrinterName)
        ON DELETE CASCADE  -- Delete slots when printer is deleted
)
""")

# Bureaus - Bureau names are globally unique
cursor.execute("""
CREATE TABLE IF NOT EXISTS bureaus (
    BureauID INTEGER PRIMARY KEY,
    Bureau TEXT NOT NULL UNIQUE,  -- Bureau names are unique across all locations
    FachabteilungID INTEGER NOT NULL,
    StandortID INTEGER NOT NULL,
    
    CHECK (length(trim(Bureau)) > 0),  -- No empty bureau names
               
    FOREIGN KEY (FachabteilungID)
        REFERENCES fachabteilung(FachabteilungID)
        ON DELETE RESTRICT,

    FOREIGN KEY (StandortID)
        REFERENCES lieugestion(StandortID)
        ON DELETE RESTRICT
)
""")

# Slot-CARIdoc assignments (many-to-many relationship)
cursor.execute("""
CREATE TABLE IF NOT EXISTS slot_caridocs (
    PrinterName TEXT NOT NULL,
    SlotName TEXT NOT NULL,
    CARIdoc TEXT NOT NULL,
    BureauID INTEGER NOT NULL,
    Bemerkung TEXT,
    
    CHECK (length(trim(PrinterName)) > 0),  -- No empty names
    CHECK (length(trim(SlotName)) > 0),
    CHECK (length(trim(CARIdoc)) > 0),
               
    PRIMARY KEY (PrinterName, SlotName, CARIdoc, BureauID),
               
    FOREIGN KEY (PrinterName, SlotName)
        REFERENCES printerslots(PrinterName, SlotName)
        ON DELETE CASCADE,  -- if printerslots is deleted, the caridoc where the printerslot was assigned will be deleted automatically

    FOREIGN KEY (CARIdoc)
        REFERENCES caridocs(CARIdoc)
        ON DELETE RESTRICT,  -- Don't allow CARIdoc deletion if in use

    FOREIGN KEY (BureauID)
        REFERENCES bureaus(BureauID)
        ON DELETE RESTRICT   -- Don't allow bureau deletion if in use
)
""")

# --- STEP 3.5: Create trigger to enforce Standort consistency ---
# This ensures a printer can only be used by bureaus from ONE location
cursor.execute("""
CREATE TRIGGER IF NOT EXISTS enforce_printer_standort_consistency
BEFORE INSERT ON slot_caridocs
FOR EACH ROW
BEGIN
    -- Check if this printer already has assignments to a different location
    SELECT CASE
        WHEN EXISTS (
            SELECT 1
            FROM slot_caridocs sc
            JOIN bureaus b1 ON sc.BureauID = b1.BureauID
            JOIN bureaus b2 ON b2.BureauID = NEW.BureauID
            WHERE sc.PrinterName = NEW.PrinterName
              AND b1.StandortID != b2.StandortID
        )
        THEN RAISE(ABORT, 'Printer cannot be assigned to bureaus from different locations')
    END;
END;
""")

# --- STEP 4: Import CARIdocs from second sheet ---
for _, row in df_forms.iterrows():
    caridoc = row.get('Formular')
    format_caridoc = row.get('Format CARI-Doc')
    format_druckeinlage = row.get('Format Druckeinlage')
    beschreibung = row.get('Beschreibung Formular')
    canon_settings = row.get('Canon Printer Settings')

    if pd.isna(caridoc) or str(caridoc).strip() == '':
        print("⚠️ WARNUNG: Formular ohne CARIdoc-Name gefunden, wird übersprungen.")
        continue

    # --- Druckeinlage ---
    if pd.notna(format_druckeinlage) and str(format_druckeinlage).strip() != '':
        cursor.execute("""
            INSERT OR IGNORE INTO druckeinlage (FormatDruckeinlage)
            VALUES (?)
        """, (format_druckeinlage,))

    # --- Printer settings ---
    if pd.notna(canon_settings) and str(canon_settings).strip() != '':
        cursor.execute("""
            INSERT OR IGNORE INTO printersettings
            (CanonPrinterSettings, SettingsPNG)
            VALUES (?, NULL)
        """, (canon_settings,))

    # --- CARIdoc ---
    cursor.execute("""
        INSERT OR IGNORE INTO caridocs
        (CARIdoc, FormatCARIDoc, FormatDruckeinlage, BeschreibungFormular, CanonPrinterSettings)
        VALUES (?, ?, ?, ?, ?)
    """, (caridoc, format_caridoc, format_druckeinlage, beschreibung, canon_settings))


# --- STEP 5: Import Standorte ---
df_standorte = df_printers[['Standort']].drop_duplicates().dropna().reset_index(drop=True)
df_standorte = df_standorte[df_standorte['Standort'].str.strip() != '']  # Filter empty strings
for idx, row in df_standorte.iterrows():
    cursor.execute("INSERT INTO lieugestion (StandortID, Standort) VALUES (?, ?)",
                   (idx+1, row['Standort']))
standort_map = {row['Standort']: idx+1 for idx, row in df_standorte.iterrows()}

# --- STEP 6: Import Fachabteilungen ---
df_fach = df_printers[['Fachabteilung']].drop_duplicates().dropna().reset_index(drop=True)
df_fach = df_fach[df_fach['Fachabteilung'].str.strip() != '']  # Filter empty strings
for idx, row in df_fach.iterrows():
    cursor.execute("INSERT INTO fachabteilung (FachabteilungID, Fachabteilung) VALUES (?, ?)",
                   (idx+1, row['Fachabteilung']))
fach_map = {row['Fachabteilung']: idx+1 for idx, row in df_fach.iterrows()}

# --- STEP 7: Import PrinterModels ---
df_models = df_printers[['Drucker Modell']].drop_duplicates().dropna()
df_models = df_models[df_models['Drucker Modell'].str.strip() != '']  # Filter empty strings
for model in df_models['Drucker Modell']:
    cursor.execute("INSERT INTO printermodels (PrinterModel) VALUES (?)", (model,))

# --- STEP 8: Import Printers ---
df_printers_list = df_printers[['Druckername', 'Drucker Modell']].drop_duplicates().dropna(subset=['Druckername'])
df_printers_list = df_printers_list[df_printers_list['Druckername'].str.strip() != '']  # Filter empty strings
for _, row in df_printers_list.iterrows():
    cursor.execute("INSERT INTO printernames (PrinterName, PrinterModel) VALUES (?, ?)",
                   (row['Druckername'], row['Drucker Modell']))

# --- STEP 9: Import Bureaus ---
df_bureaus = df_printers[['Bureau', 'Bureau-ID', 'Fachabteilung', 'Standort']].drop_duplicates()
df_bureaus = df_bureaus[pd.notna(df_bureaus['Bureau'])]
df_bureaus = df_bureaus[df_bureaus['Bureau'].str.strip() != '']  # Filter empty strings

for _, row in df_bureaus.iterrows():
    fach_id = fach_map.get(row['Fachabteilung'])
    standort_id = standort_map.get(row['Standort'])
    cursor.execute("""
        INSERT INTO bureaus (BureauID, Bureau, FachabteilungID, StandortID)
        VALUES (?, ?, ?, ?)
    """, (row['Bureau-ID'], row['Bureau'], fach_id, standort_id))

# --- STEP 10: Import Slots + Bemerkungen + CARIdocs ---
for _, row in df_printers.iterrows():
    printer_name = row['Druckername']
    slot_name = row['Schacht Name']
    caridoc = row['CARIdoc']
    paperformat = row['Format']
    two_sided = True if str(row['2-sided']).strip().lower() in ['2-sided', 'true', '1'] else False
    autoprint = True if str(row['Autoprint']).strip().lower() in ['true', '1', 'yes', 'x'] else False
    bureau_id = row.get('Bureau-ID', None)
    bemerkung = row['Bemerkung'] if pd.notna(row['Bemerkung']) else None

    # Skip rows with empty printer or slot names
    if pd.isna(printer_name) or str(printer_name).strip() == '':
        continue
    if pd.isna(slot_name) or str(slot_name).strip() == '':
        continue

    # Insert slot first
    cursor.execute("""
        INSERT OR IGNORE INTO printerslots 
        (PrinterName, SlotName, PaperFormat, TwoSided, Autoprint, Bemerkung)
        VALUES (?, ?, ?, ?, ?, NULL)
    """, (printer_name, slot_name, paperformat, two_sided, autoprint))

    # TEMP CHECKS - Foreign Key Validation
    # These checks verify that all foreign key relationships are valid before inserting data
    # This prevents constraint violations and provides clear error messages during import

    # --- CHECK 1: Verify the printer slot was successfully created ---
    # This validates that the previous INSERT OR IGNORE into printerslots worked
    cursor.execute(
        "SELECT 1 FROM printerslots WHERE PrinterName=? AND SlotName=?",
        (printer_name, slot_name)
    )
    if cursor.fetchone() is None:
        # If the slot doesn't exist, something went wrong with the INSERT
        raise SystemExit(f"❌ Slot fehlt: {printer_name} / {slot_name}")

    # --- CHECK 2: Verify CARIdoc exists (only if one is specified) ---
    # Only validate if this row actually references a CARIdoc
    # Rows without a CARIdoc are allowed (non-bureau slots)
    if pd.notna(caridoc) and str(caridoc).strip() != '':
        cursor.execute(
            "SELECT 1 FROM caridocs WHERE CARIdoc=?",
            (caridoc,)
        )
        if cursor.fetchone() is None:
            # CARIdoc should have been imported from the second Excel sheet
            raise SystemExit(f"❌ CARIdoc fehlt: {caridoc}")

    # --- CHECK 3: Verify BureauID exists (only if one is specified) ---
    # Only validate if this row actually references a Bureau
    # Rows without a Bureau are allowed (generic/non-bureau printer slots)
    if pd.notna(bureau_id):
        cursor.execute(
            "SELECT 1 FROM bureaus WHERE BureauID=?",
            (bureau_id,)
        )
        if cursor.fetchone() is None:
            # BureauID should have been imported earlier from the Excel
            raise SystemExit(f"❌ BureauID fehlt: {bureau_id}")

    # END TEMP CHECKS
    # If we reach here, all foreign key relationships are valid

    # --- CASE 1: Bureau slot => Bemerkung belongs in slot_caridocs
    if pd.notna(caridoc) and str(caridoc).strip() != '' and pd.notna(bureau_id):
        cursor.execute("""
            INSERT OR IGNORE INTO slot_caridocs
            (PrinterName, SlotName, CARIdoc, BureauID, Bemerkung)
            VALUES (?, ?, ?, ?, ?)
        """, (printer_name, slot_name, caridoc, bureau_id, bemerkung))

    # --- CASE 2: Non-bureau slot => Bemerkung belongs in printerslots
    elif bemerkung:
        cursor.execute("""
            UPDATE printerslots 
            SET Bemerkung = ?
            WHERE PrinterName = ? AND SlotName = ?
        """, (bemerkung, printer_name, slot_name))

# --- STEP 10.5: Konsistenzprüfung Drucker ↔ Standort über Bureaus ---
# Note: This check is now also enforced by the trigger at the database level
cursor.execute("""
SELECT
    sc.PrinterName,
    COUNT(DISTINCT b.StandortID) AS Anzahl_Standorte
FROM slot_caridocs sc
JOIN bureaus b ON sc.BureauID = b.BureauID
GROUP BY sc.PrinterName
HAVING COUNT(DISTINCT b.StandortID) > 1;
""")

problemfaelle = cursor.fetchall()

if problemfaelle:
    print("❌ FEHLER: Drucker mit mehreren Standorten gefunden!")
    for printer, count in problemfaelle:
        print(f" - {printer}: {count} Standorte")
    conn.rollback()
    conn.close()
    raise SystemExit("Import abgebrochen wegen inkonsistenter Standort-Zuordnung")

# --- STEP 10.7: Standort für Drucker ohne Bureau aus Excel setzen --- 
df_printer_standorte = df_printers[['Druckername', 'Standort']] \
    .dropna() \
    .drop_duplicates(subset=['Druckername'])

for _, row in df_printer_standorte.iterrows():
    printer = row['Druckername']
    standort_id = standort_map.get(row['Standort'])

    cursor.execute("""
        UPDATE printernames
        SET StandortID = ?
        WHERE PrinterName = ? AND StandortID IS NULL
    """, (standort_id, printer))

# --- STEP 11: Commit & Close ---
conn.commit()
conn.close()

print("✅ Drop Table and Import completed successfully!")
print("✅ Database schema includes comprehensive constraints:")
print("   - NOT NULL constraints on required fields")
print("   - CHECK constraints for data validation")
print("   - UNIQUE constraints on bureau names")
print("   - Foreign key constraints with proper CASCADE/RESTRICT")
print("   - Trigger to enforce printer-location consistency")