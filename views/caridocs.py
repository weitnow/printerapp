from .base_view import BaseView
from tkinter import messagebox
import sqlite3
import db


class CaridocView(BaseView):
    name = "caridocs"
    columns = ["CARIdoc", "CARIDocument", "Format CARIdoc", "Format Druckeinlage", "mm Width", "mm Height" ]
    columns_actions = {}
    query = """
    SELECT
    cd.CARIdoc,
    cd.BeschreibungFormular,
    cd.FormatCARIDoc,
    cd.FormatDruckeinlage,
    de.WidthMM,
    de.HeightMM
    FROM caridocs cd
    LEFT JOIN druckeinlage de on cd.FormatDruckeinlage = de.FormatDruckeinlage

    ORDER BY CARIdoc
    """

    def delete(self, app, selected_rows):
        if not selected_rows:
            return
        
        if not messagebox.askyesno(
            "Delete",
            "Are you sure you want to delete the selected CARIDoc(s)?"
        ):
            return

        try:
            col = {name: i for i, name in enumerate(self.columns)}

            with db.get_connection() as conn:
                cur = conn.cursor()
                deleted = 0
                
                for row in selected_rows:
                    caridoc = (row[col["CARIdoc"]])
                    
                    cur.execute("DELETE FROM caridocs WHERE CARIdoc = ?", 
                    (caridoc,)
                    )

                    deleted += 1

            if deleted:
                app.refresh_view()
                messagebox.showinfo("Success", f"{deleted} CARIDoc(s) deleted successfully.")

        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot delete CARIDoc(s):\n{str(e)}" + 
                                 "\nPlease ensure that the CARIDoc(s) are not in use.")

        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")