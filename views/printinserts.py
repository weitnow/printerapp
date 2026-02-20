from .base_view import BaseView
import sqlite3
from tkinter import messagebox, Button
import db  # Import the db module

class PrintInsertView(BaseView):
    name = "printinserts"
    columns = ["FormatDruckeinlage", "Breite mm", "Höhe mm"]
    columns_actions = {}
    query = """
    SELECT
    FormatDruckeinlage,
    WidthMM,
    HeightMM
    FROM druckeinlage

    ORDER BY FormatDruckeinlage
    """


    



    def delete(self, app, selected_rows):
        if not selected_rows:
            return
        
        if not messagebox.askyesno(
            "Delete",
            "Are you sure you want to delete the selected Print Insert(s)?"
        ):
            return

        try:
            col = {name: i for i, name in enumerate(self.columns)}

            with db.get_connection() as conn:
                cur = conn.cursor()
                deleted = 0
                
                for row in selected_rows:
                    print_insert = (row[col["FormatDruckeinlage"]])

                    cur.execute("DELETE FROM druckeinlage WHERE FormatDruckeinlage = ?",
                    (print_insert,)
                    )

                    deleted += 1

            if deleted:
                app.refresh_view()
                messagebox.showinfo("Success", f"{deleted} Print Insert(s) deleted successfully.")

        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot delete Print Insert(s):\n{str(e)}" + 
                                 "\nPlease ensure that the Print Insert(s) are not in use.")

        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
       
