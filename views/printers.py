from .base_view import BaseView
import sqlite3
from tkinter import messagebox
import db  # Import the db module
from functools import partial

# =====================
# Concrete Views
# =====================
class PrintersView(BaseView):
    name = "printers"
    columns = ["PrinterName", "Printerslots*", "CARIdocs*", "Bureaus*", "PrinterModel", "Standort"]
    columns_actions = {
        "#2": "show_printer_slots",
        "#3": "show_caridocs",  
        "#4": "show_bureaus"  
    }
    query = """
         SELECT 
        p.PrinterName,

        -- Anzahl Slots
        (
            SELECT COUNT(*)
            FROM printerslots ps
            WHERE ps.PrinterName = p.PrinterName
        ) AS "Anzahl Slots",

        -- Anzahl CARI-Docs (DISTINCT über mehrere Spalten)
        (
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT SlotName, CARIdoc
                FROM slot_caridocs sc
                WHERE sc.PrinterName = p.PrinterName
            )
        ) AS "Anzahl CARI-Docs",

        -- Anzahl Bureaus (distinct BureauID)
        (
            SELECT COUNT(DISTINCT sc.BureauID)
            FROM slot_caridocs sc
            WHERE sc.PrinterName = p.PrinterName
        ) AS "Anzahl Bureaus",

        p.PrinterModel,
        l.Standort

    FROM printernames p
    LEFT JOIN lieugestion l ON p.StandortID = l.StandortID
    ORDER BY p.PrinterName;
        """

    def delete(self, app, row_value):
        printer_name = row_value[0]  # PrinterName is the first column
        
        # First, check if printer has slots
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM printerslots 
                    WHERE PrinterName = ?
                """, (printer_name,))
                slot_count = cur.fetchone()[0]
        except Exception as e:
            messagebox.showerror("Error", f"Could not check printer slots: {str(e)}")
            return
        
        # Build warning message based on slot count
        if slot_count > 0:
            message = (f"Printer '{printer_name}' has {slot_count} slot(s) assigned.\n\n"
                      f"Deleting the printer will also delete all its slots and their assignments.\n\n"
                      f"Do you want to continue?")
        else:
            message = f"Delete printer '{printer_name}'?"
        
        # Ask for confirmation
        if messagebox.askyesno("Delete Printer", message):
            try:
                with db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "DELETE FROM printernames WHERE PrinterName = ?",
                        (printer_name,)
                    )
                app.refresh_view()
                messagebox.showinfo("Success", f"Printer '{printer_name}' deleted successfully.")
            except sqlite3.IntegrityError as e:
                messagebox.showerror("Error", 
                    f"Cannot delete printer: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")