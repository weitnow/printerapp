from .base_view import BaseView
import sqlite3
from tkinter import messagebox
import db  # Import the db module

class SlotPrinter(BaseView):
    name = "printer slots"
    columns = ["PrinterName", "SlotName*", "PaperFormat", "TwoSided", "Autoprint", "Bemerkung"]
    columns_actions = {
        "#2": "show_caridocs_of_slot"
    }
    query = """
    SELECT
        PrinterName,
        SlotName,
        PaperFormat,
        TwoSided,
        Autoprint,
        Bemerkung
    FROM printerslots
    ORDER BY PrinterName, SlotName
    """
    
    def __init__(self):
        super().__init__()
        self.filtered_printer = None

    def get_query(self):
        """Return query, optionally filtered by printer name"""
        if self.filtered_printer:
            return f"""
                SELECT
                    PrinterName,
                    SlotName,
                    PaperFormat,
                    TwoSided,
                    Autoprint,
                    Bemerkung
                FROM printerslots
                WHERE PrinterName = '{self.filtered_printer}'
                ORDER BY SlotName
            """
        return self.query
    
  
    
    def set_filter(self, printer_name):
        """Set the printer filter"""
        self.filtered_printer = printer_name
    
    def clear_filter(self):
        """Clear the printer filter"""
        self.filtered_printer = None
    
    def delete(self, app, row):
        printer_name = row[0]  # PrinterName
        slot_name = row[1]     # SlotName
        
        if messagebox.askyesno("Delete Slot", 
                              f"Delete slot '{slot_name}' from printer '{printer_name}'?"):
            try:
                with db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "DELETE FROM printerslots WHERE PrinterName = ? AND SlotName = ?",
                        (printer_name, slot_name)
                    )
                app.refresh_view()
                messagebox.showinfo("Success", f"Slot '{slot_name}' deleted successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete slot: {str(e)}")