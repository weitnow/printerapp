from .base_view import BaseView
import sqlite3
from tkinter import messagebox, Button
import db  # Import the db module

class SlotPrinter(BaseView):
    name = "printer slots"
    columns = ["PrinterName", "SlotName", "PaperFormat", "TwoSided", "Autoprint", "Bemerkung"]
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
        self.back_button = None

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

    def on_view_shown(self, app, frame):
        """Called when view is shown - add back button if filtered"""
        if self.filtered_printer:
            # Add a back button at the top
            self.back_button = Button(
                frame,
                text=f"← Back to all printers (currently showing: {self.filtered_printer})",
                command=lambda: self.go_back(app)
            )
            self.back_button.pack(side="top", fill="x", padx=5, pady=5)
    
    def on_view_hidden(self, app):
        """Called when view is hidden - cleanup"""
        if self.back_button:
            self.back_button.destroy()
            self.back_button = None
    
    def go_back(self, app):
        """Go back to printers view and clear filter"""
        self.clear_filter()
        app.switch_view("printers")
    
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