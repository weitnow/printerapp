import pandas as pd
import sqlite3


# ============================================================
# Public API (used by Tkinter)
# ============================================================

def run_import(xlsx_file: str, db_file: str = "printers.db") -> None:
    """
    Import printer data from XLSX into SQLite database.

    Raises:
        RuntimeError on validation or consistency errors
        Any other exception on unexpected failure
    """
    try:
        _run_import_internal(xlsx_file, db_file)
    except Exception:
        # Let caller (GUI / CLI) decide how to handle it
        raise


# ============================================================
# Internal implementation
# ============================================================

def _run_import_internal(xlsx_file: str, db_file: str) -> None:
    sheet_name_printers = 0
    sheet_name_forms = 1

    # --- STEP 1: Read Excel ---
    df_printers = pd.read_excel(xlsx_file, sheet_name=sheet_name_printers)
    df_forms = pd.read_excel(xlsx_file, sheet_name=sheet_name_forms)

    # --- STEP 2: Connect to SQLite ---
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        _drop_tables(cursor)
        _create_schema(cursor)

        _import_caridocs(cursor, df_forms)
        standort_map = _import_standorte(cursor, df_printers)
        fach_map = _import_fachabteilungen(cursor, df_printers)
        _import_printermodels(cursor, df_printers)
        _import_printers(cursor, df_printers)
        _import_bureaus(cursor, df_printers, fach_map, standort_map)
        _import_slots_and_assignments(cursor, df_printers)

        _validate_printer_standorte(cursor)
        _update_printer_standorte(cursor, df_printers, standort_map)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ============================================================
# Schema
# ============================================================

def _drop_tables(cursor):
    cursor.executescript("""
    DROP TABLE IF EXISTS slot_caridocs;
    DROP TABLE IF EXISTS printerslots;
    DROP TABLE IF EXISTS bureaus;
    DROP TABLE IF EXISTS printernames;
    DROP TABLE IF EXISTS printermodels;
    DROP TABLE IF EXISTS fachabteilung;
    DROP TABLE IF EXISTS lieugestion;
    DROP TABLE IF EXISTS caridocs;
    DROP TABLE IF EXISTS druckeinlage;
    DROP TABLE IF EXISTS printersettings;
    """)


def _create_schema(cursor):
    cursor.executescript("""
    CREATE TABLE lieugestion (
        StandortID INTEGER PRIMARY KEY,
        Standort TEXT NOT NULL UNIQUE CHECK (length(trim(Standort)) > 0)
    );

    CREATE TABLE fachabteilung (
        FachabteilungID INTEGER PRIMARY KEY,
        Fachabteilung TEXT NOT NULL UNIQUE CHECK (length(trim(Fachabteilung)) > 0)
    );

    CREATE TABLE printermodels (
        PrinterModel TEXT PRIMARY KEY CHECK (length(trim(PrinterModel)) > 0)
    );

    CREATE TABLE druckeinlage (
        FormatDruckeinlage TEXT PRIMARY KEY,
        WidthMM REAL CHECK (WidthMM IS NULL OR WidthMM > 0),
        HeightMM REAL CHECK (HeightMM IS NULL OR HeightMM > 0)
    );

    CREATE TABLE printersettings (
        CanonPrinterSettings TEXT PRIMARY KEY,
        SettingsPNG BLOB
    );

    CREATE TABLE caridocs (
        CARIdoc TEXT PRIMARY KEY,
        FormatCARIDoc TEXT,
        FormatDruckeinlage TEXT,
        BeschreibungFormular TEXT,
        CanonPrinterSettings TEXT,
        FOREIGN KEY (FormatDruckeinlage) REFERENCES druckeinlage,
        FOREIGN KEY (CanonPrinterSettings) REFERENCES printersettings
    );

    CREATE TABLE printernames (
        PrinterName TEXT PRIMARY KEY,
        PrinterModel TEXT NOT NULL,
        StandortID INTEGER,
        FOREIGN KEY (PrinterModel) REFERENCES printermodels,
        FOREIGN KEY (StandortID) REFERENCES lieugestion
    );

    CREATE TABLE printerslots (
        PrinterName TEXT,
        SlotName TEXT,
        PaperFormat TEXT,
        TwoSided BOOLEAN DEFAULT 0,
        Autoprint BOOLEAN DEFAULT 0,
        Bemerkung TEXT,
        PRIMARY KEY (PrinterName, SlotName),
        FOREIGN KEY (PrinterName) REFERENCES printernames ON DELETE CASCADE
    );

    CREATE TABLE bureaus (
        BureauID INTEGER PRIMARY KEY,
        Bureau TEXT UNIQUE,
        FachabteilungID INTEGER,
        StandortID INTEGER,
        FOREIGN KEY (FachabteilungID) REFERENCES fachabteilung,
        FOREIGN KEY (StandortID) REFERENCES lieugestion
    );

    CREATE TABLE slot_caridocs (
        PrinterName TEXT,
        SlotName TEXT,
        CARIdoc TEXT,
        BureauID INTEGER,
        Bemerkung TEXT,
        PRIMARY KEY (PrinterName, SlotName, CARIdoc, BureauID),
        FOREIGN KEY (PrinterName, SlotName)
            REFERENCES printerslots(PrinterName, SlotName)
            ON DELETE CASCADE,
        FOREIGN KEY (CARIdoc) REFERENCES caridocs,
        FOREIGN KEY (BureauID) REFERENCES bureaus
    );
    """)


# ============================================================
# Import helpers
# ============================================================

def _import_caridocs(cursor, df):
    for _, row in df.iterrows():
        caridoc = row.get("Formular")
        if pd.isna(caridoc):
            continue

        cursor.execute(
            "INSERT OR IGNORE INTO caridocs (CARIdoc) VALUES (?)",
            (caridoc,)
        )


def _import_standorte(cursor, df):
    unique = df[["Standort"]].dropna().drop_duplicates()
    mapping = {}

    for idx, row in unique.iterrows():
        cursor.execute(
            "INSERT INTO lieugestion (StandortID, Standort) VALUES (?, ?)",
            (idx + 1, row["Standort"])
        )
        mapping[row["Standort"]] = idx + 1

    return mapping


def _import_fachabteilungen(cursor, df):
    unique = df[["Fachabteilung"]].dropna().drop_duplicates()
    mapping = {}

    for idx, row in unique.iterrows():
        cursor.execute(
            "INSERT INTO fachabteilung (FachabteilungID, Fachabteilung) VALUES (?, ?)",
            (idx + 1, row["Fachabteilung"])
        )
        mapping[row["Fachabteilung"]] = idx + 1

    return mapping


def _import_printermodels(cursor, df):
    for model in df["Drucker Modell"].dropna().unique():
        cursor.execute(
            "INSERT OR IGNORE INTO printermodels VALUES (?)",
            (model,)
        )


def _import_printers(cursor, df):
    for _, row in df[["Druckername", "Drucker Modell"]].dropna().drop_duplicates().iterrows():
        cursor.execute(
            "INSERT INTO printernames (PrinterName, PrinterModel) VALUES (?, ?)",
            (row["Druckername"], row["Drucker Modell"])
        )


def _import_bureaus(cursor, df, fach_map, standort_map):
    for _, row in df[["Bureau", "Bureau-ID", "Fachabteilung", "Standort"]].dropna().drop_duplicates().iterrows():
        cursor.execute(
            "INSERT INTO bureaus VALUES (?, ?, ?, ?)",
            (
                row["Bureau-ID"],
                row["Bureau"],
                fach_map[row["Fachabteilung"]],
                standort_map[row["Standort"]],
            )
        )


def _import_slots_and_assignments(cursor, df):
    for _, row in df.iterrows():
        printer_name = row.get('Druckername')
        slot_name = row.get('Schacht Name')
        caridoc = row.get('CARIdoc')
        paperformat = row.get('Format')
        bureau_id = row.get('Bureau-ID')
        bemerkung = row.get('Bemerkung') if pd.notna(row.get('Bemerkung')) else None

        two_sided = (
            str(row.get('2-sided')).strip().lower()
            in ['2-sided', 'true', '1']
        )

        autoprint = (
            str(row.get('Autoprint')).strip().lower()
            in ['true', '1', 'yes', 'x']
        )

        # --- Skip invalid rows ---
        if pd.isna(printer_name) or str(printer_name).strip() == '':
            continue
        if pd.isna(slot_name) or str(slot_name).strip() == '':
            continue

        # --- Insert slot ---
        cursor.execute("""
            INSERT OR IGNORE INTO printerslots
            (PrinterName, SlotName, PaperFormat, TwoSided, Autoprint, Bemerkung)
            VALUES (?, ?, ?, ?, ?, NULL)
        """, (printer_name, slot_name, paperformat, two_sided, autoprint))

        # --- CASE 1: Bureau slot => slot_caridocs ---
        if (
            pd.notna(caridoc)
            and str(caridoc).strip() != ''
            and pd.notna(bureau_id)
        ):
            cursor.execute("""
                INSERT OR IGNORE INTO slot_caridocs
                (PrinterName, SlotName, CARIdoc, BureauID, Bemerkung)
                VALUES (?, ?, ?, ?, ?)
            """, (printer_name, slot_name, caridoc, bureau_id, bemerkung))

        # --- CASE 2: Non-bureau slot => printerslots.Bemerkung ---
        elif bemerkung:
            cursor.execute("""
                UPDATE printerslots
                SET Bemerkung = ?
                WHERE PrinterName = ? AND SlotName = ?
            """, (bemerkung, printer_name, slot_name))



# ============================================================
# Validation
# ============================================================

def _validate_printer_standorte(cursor):
    cursor.execute("""
    SELECT PrinterName
    FROM slot_caridocs sc
    JOIN bureaus b ON sc.BureauID = b.BureauID
    GROUP BY PrinterName
    HAVING COUNT(DISTINCT b.StandortID) > 1
    """)
    if cursor.fetchall():
        raise RuntimeError(
            "Import aborted: printer assigned to multiple locations"
        )


def _update_printer_standorte(cursor, df, standort_map):
    unique = df[["Druckername", "Standort"]].dropna().drop_duplicates()

    for _, row in unique.iterrows():
        cursor.execute(
            """
            UPDATE printernames
            SET StandortID = ?
            WHERE PrinterName = ? AND StandortID IS NULL
            """,
            (standort_map[row["Standort"]], row["Druckername"])
        )


# ============================================================
# CLI CLI entry point
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python master_import.py <xlsx_file>")
        sys.exit(1)

    run_import(sys.argv[1])
    print("✅ Import completed successfully")
