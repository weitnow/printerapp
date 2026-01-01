from .base_view import BaseView
import sqlite3
from tkinter import messagebox
import db  # Import the db module

# =====================
# Concrete Views
# =====================
class PrintersView(BaseView):
    name = "printers"
    columns = ["PrinterName", "Anzahl konfigurierte Slots", "Anzahl zugewiesene CARI-Bureau(s)", "PrinterModel", "Standort"]
    query = """
    SELECT 
    p.PrinterName,
    (SELECT COUNT(*) FROM printerslots ps WHERE ps.PrinterName = p.PrinterName) AS 'Anzahl Slots',
    (SELECT COUNT(*) FROM slot_caridocs sc WHERE sc.PrinterName = p.PrinterName) AS 'Anzahl CARI-Bureas',
    p.PrinterModel,
    l.Standort
    FROM printernames p
    LEFT JOIN lieugestion l ON p.StandortID = l.StandortID
    ORDER BY p.PrinterName
    """

    def on_double_click(self, app, row, col):
        """Handle double-click event - navigate to printer slots view"""
        if col == "#3":
            print("Implement viewing assigned CARI Bureaus here.")
            return  # Ignore double-clicks on "Anzahl zugewiesene CARI-Bureau(s)" column
        printer_name = row[0]  # PrinterName is the first column
        self.show_printer_slots(app, printer_name)

    def show_printer_slots(self, app, printer_name):
        """Switch to printer slots view filtered by printer name"""
        # Switch to the slot_printer view
        app.switch_view("printer slots", filter_printer=printer_name)

    def delete(self, app, row):
        printer_name = row[1]  # PrinterName is the second column
        
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