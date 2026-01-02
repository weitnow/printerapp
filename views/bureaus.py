from .base_view import BaseView
import sqlite3
from tkinter import messagebox, Button
import db  # Import the db module

class BureausView(BaseView):
    name = "bureaus"
    columns = ["BureauID", "Bureau", "Anzahl konfigurierte Slots", "Fachabteilung", "Standort"]
    query = """
    SELECT
    b.BureauID,
    b.Bureau,
    (SELECT COUNT(*) FROM slot_caridocs sc WHERE sc.BureauID = b.BureauID) AS 'Anzahl konfigurierte Slots',
    f.Fachabteilung,
    l.Standort
    FROM bureaus b
    LEFT JOIN fachabteilung f ON b.FachabteilungID = f.FachabteilungID
    LEFT JOIN lieugestion l ON b.StandortID = l.StandortID
    ORDER BY b.BureauID
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
                    b.BureauID,
                    b.Bureau,
                    (SELECT COUNT(*) FROM slot_caridocs sc WHERE sc.BureauID = b.BureauID) AS 'Anzahl konfigurierte Slots',
                    f.Fachabteilung,
                    l.Standort
                FROM bureaus b
                LEFT JOIN fachabteilung f ON b.FachabteilungID = f.FachabteilungID
                LEFT JOIN lieugestion l ON b.StandortID = l.StandortID
                WHERE EXISTS (
                    SELECT 1
                    FROM slot_caridocs sc2
                    WHERE sc2.BureauID = b.BureauID
                    AND sc2.PrinterName = '{self.filtered_printer}'
                )
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
        bureau_id = row[0]
        if messagebox.askyesno("Delete", f"Lösche bureau ID {bureau_id}? \nBureaus sollten nicht gelöscht werden, weil die BureauID in CARI vergeben ist."):
            try:
                with db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "DELETE FROM bureaus WHERE BureauID = ?",
                        (bureau_id,)
                    )
                app.refresh_view()
            except sqlite3.IntegrityError as e:
                messagebox.showerror("Error", 
                    f"Cannot delete bureau: It is still referenced in slot_caridocs.\n\n{str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")