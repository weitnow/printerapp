from .base_view import BaseView
import sqlite3
from tkinter import messagebox
import db  # Import the db module

class SlotPrinter(BaseView):
    name = "printer_slots"
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
    
    def delete(self, app, selected_rows):
        if not selected_rows:
            return

        # Each row: (PrinterName, SlotName, ...)
        slots = [(row[0], row[1]) for row in selected_rows]

        # --- Build confirmation message ---
        lines = [
            f"• {printer} → {slot}"
            for printer, slot in slots
        ]

        message = (
            f"You are about to delete {len(slots)} slot(s):\n\n"
            + "\n".join(lines)
            + "\n\nDeleting slots will also delete all assigned CARIdocs."
        )

        if not messagebox.askyesno("Delete Slots", message):
            return

        # --- Delete slots (cascade handles slot_caridocs) ---
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()

                cur.executemany(
                    "DELETE FROM printerslots WHERE PrinterName = ? AND SlotName = ?",
                    slots
                )

            app.refresh_view()
            messagebox.showinfo(
                "Success",
                f"{len(slots)} slot(s) deleted successfully."
            )

        except sqlite3.IntegrityError as e:
            messagebox.showerror(
                "Error",
                f"Cannot delete slot(s):\n{str(e)}"
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Unexpected error:\n{str(e)}"
            )
