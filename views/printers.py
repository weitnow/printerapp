from .base_view import BaseView
import sqlite3
from tkinter import messagebox
from db import DB_FILE

# =====================
# Concrete Views
# =====================
class PrintersView(BaseView):
    name = "printers"
    columns = ["Standort", "PrinterName", "PrinterModel"]
    query = """
    SELECT 
    l.Standort,
    p.PrinterName,
    p.PrinterModel
    FROM printernames p
    LEFT JOIN lieugestion l ON p.StandortID = l.StandortID
    ORDER BY l.Standort, p.PrinterName
    """


    def delete(self, app, row):
        printer = row[0]
        if messagebox.askyesno("Delete", f"Delete printer '{printer}'?"):
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute(
            "DELETE FROM printernames WHERE PrinterName = ?",
            (printer,)
            )
            conn.commit()
            conn.close()
            app.refresh_view()