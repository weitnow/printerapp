from .base_view import BaseView
import sqlite3
from tkinter import messagebox, Button
import db  # Import the db module


class LieugestionView(BaseView):
    name = "lieugestion"
    columns = ["StandortID", "Standort"]
    columns_actions = {}
    query = """
    SELECT
    StandortID,
    Standort
    FROM lieugestion

    ORDER BY StandortID
    """

    def delete(self, app, selected_rows):
        if not selected_rows:
            return
        
        if not messagebox.askyesno(
            "Delete",
            "Are you sure you want to delete the selected location(s)?"
        ):
            return

        try:
            col = {name: i for i, name in enumerate(self.columns)}

            with db.get_connection() as conn:
                cur = conn.cursor()
                deleted = 0
                
                for row in selected_rows:
                    location_id = (row[col["StandortID"]])

                    cur.execute("DELETE FROM lieugestion WHERE StandortID = ?",
                    (location_id,)
                    )

                    deleted += 1

            if deleted:
                app.refresh_view()
                messagebox.showinfo("Success", f"{deleted} location(s) deleted successfully.")

        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot delete location(s):\n{str(e)}" + 
                                 "\nPlease ensure that the location(s) are not in use.")

        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
       
