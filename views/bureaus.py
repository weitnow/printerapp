from .base_view import BaseView
import sqlite3
from tkinter import messagebox
from db import DB_FILE

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
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute(
            "DELETE FROM bureaus WHERE BureauID = ?",
            (bureau_id,)
            )
            conn.commit()
            conn.close()
            app.refresh_view()