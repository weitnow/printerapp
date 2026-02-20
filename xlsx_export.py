import pandas as pd
import sqlite3
from pathlib import Path
from typing import Tuple, Optional

def export_printer_data(
    db_file: str = "printers.db",
    output_xlsx: str = "Druckerliste_CARI_export.xlsx",
    progress_callback: Optional[callable] = None
) -> Tuple[bool, str, dict]:
    """
    Export printer and form data from SQLite database to Excel.
    
    Args:
        db_file: Path to the SQLite database file
        output_xlsx: Path for the output Excel file
        progress_callback: Optional callback function(message: str) for progress updates
    
    Returns:
        Tuple of (success: bool, message: str, stats: dict)
    """
    
    def log(message: str):
        """Helper to log messages via callback or print"""
        if progress_callback:
            progress_callback(message)
        else:
            print(message)
    
    try:
        # Validate database file exists
        if not Path(db_file).exists():
            return False, f"Database file not found: {db_file}", {}
        
        log(f"Connecting to database: {db_file}")
        conn = sqlite3.connect(db_file)
        
        # Query 1: Bureau-printer-slot-caridoc combinations
        log("Executing query 1: Bureau-printer combinations...")
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
            sc.Bemerkung as Bemerkung
        FROM 
            slot_caridocs sc
            JOIN printerslots ps ON sc.PrinterName = ps.PrinterName AND sc.SlotName = ps.SlotName
            JOIN printernames pn ON ps.PrinterName = pn.PrinterName
            JOIN bureaus b ON sc.BureauID = b.BureauID
            LEFT JOIN fachabteilung f ON b.FachabteilungID = f.FachabteilungID
            LEFT JOIN lieugestion l ON b.StandortID = l.StandortID
        """
        df1 = pd.read_sql_query(query_with_caridocs, conn)
        
        # Query 2: Printers/slots without bureau connection
        log("Executing query 2: Printers without bureaus...")
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
            ps.Bemerkung as Bemerkung
        FROM 
            printerslots ps
            JOIN printernames pn ON ps.PrinterName = pn.PrinterName
            LEFT JOIN lieugestion l ON pn.StandortID = l.StandortID
        WHERE NOT EXISTS (
            SELECT 1 FROM slot_caridocs sc 
            WHERE sc.PrinterName = ps.PrinterName AND sc.SlotName = ps.SlotName
        )
        """
        df2 = pd.read_sql_query(query_printers_without_bureaus, conn)
        
        # Query 3: Bureaus without printer connection
        log("Executing query 3: Bureaus without printers...")
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
        df3 = pd.read_sql_query(query_bureaus_without_printers, conn)
        
        # Combine all dataframes
        log("Combining results...")
        df_printers = pd.concat([df1, df2, df3], ignore_index=True)
        
        # Sort the combined data
        log("Sorting data...")
        df_printers = df_printers.sort_values(
            by=['Standort', 'Bureau', 'Druckername', 'Schacht Name', 'CARIdoc'],
            na_position='last'
        )
        
        # Export CARIdocs (Forms)
        log("Exporting forms data...")
        # Export in the exact column layout that xlsx_import.py expects
        # for the forms sheet: Formular, Format CARI-Doc, Format Druckeinlage,
        # Beschreibung Formular.
        query_caridocs = """
        SELECT 
            c.CARIdoc           AS Formular,
            c.FormatCARIDoc     AS 'Format CARI-Doc',
            c.FormatDruckeinlage AS 'Format Druckeinlage',
            c.BeschreibungFormular AS 'Beschreibung Formular'
        FROM 
            caridocs c
        ORDER BY 
            c.CARIdoc
        """
        df_forms = pd.read_sql_query(query_caridocs, conn)
        
        # Close database connection
        conn.close()
        log("Database connection closed")
        
        # Write to Excel
        log(f"Writing to Excel file: {output_xlsx}")
        with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
            df_printers.to_excel(writer, index=False, sheet_name='Druckerliste')
            df_forms.to_excel(writer, index=False, sheet_name='Forms')
        
        # Prepare statistics
        stats = {
            'total_rows': len(df_printers),
            'bureau_printer_connections': len(df1),
            'printers_without_bureaus': len(df2),
            'bureaus_without_printers': len(df3),
            'total_caridocs': len(df_forms),
            'columns_sheet1': df_printers.columns.tolist(),
            'columns_sheet2': df_forms.columns.tolist()
        }
        
        success_msg = f"✅ Export completed successfully!\nCreated: {output_xlsx}"
        log(success_msg)
        
        return True, success_msg, stats
        
    except sqlite3.Error as e:
        error_msg = f"Database error: {str(e)}"
        log(f"❌ {error_msg}")
        return False, error_msg, {}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log(f"❌ {error_msg}")
        return False, error_msg, {}


def print_statistics(stats: dict):
    """Print export statistics to console"""
    print(f"\n📄 Sheet 1 - Druckerliste:")
    print(f"  Total rows: {stats['total_rows']}")
    print(f"  - Rows with bureau-printer connections: {stats['bureau_printer_connections']}")
    print(f"  - Rows with printers without bureaus: {stats['printers_without_bureaus']}")
    print(f"  - Rows with bureaus without printers: {stats['bureaus_without_printers']}")
    print(f"\n📄 Sheet 2 - Forms:")
    print(f"  Total CARIdocs: {stats['total_caridocs']}")
    print(f"\nColumn structure (Sheet 1):")
    print(stats['columns_sheet1'])
    print(f"\nColumn structure (Sheet 2):")
    print(stats['columns_sheet2'])


def main():
    """Main function for standalone execution"""
    db_file = "printers.db"
    output_xlsx = "Druckerliste_CARI_export.xlsx"
    
    success, message, stats = export_printer_data(db_file, output_xlsx)
    
    if success and stats:
        print_statistics(stats)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())