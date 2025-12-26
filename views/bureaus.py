from .base_view import BaseView
import sqlite3
from tkinter import messagebox
import db  # Import the db module

class BureausView(BaseView):
    name = "bureaus"
    columns = ["BureauID", "Bureau", "Fachabteilung", "Standort"]
    query = """
    SELECT
    b.BureauID,
    b.Bureau,
    f.Fachabteilung,
    l.Standort
    FROM bureaus b
    LEFT JOIN fachabteilung f ON b.FachabteilungID = f.FachabteilungID
    LEFT JOIN lieugestion l ON b.StandortID = l.StandortID
    ORDER BY b.Bureau
    """

    def delete(self, app, row):
        bureau_id = row[0]
        if messagebox.askyesno("Delete", f"Delete bureau ID {bureau_id}?"):
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