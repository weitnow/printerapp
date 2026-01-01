from .base_view import BaseView
import sqlite3
from tkinter import messagebox
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