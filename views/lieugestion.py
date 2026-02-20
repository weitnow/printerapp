from .base_view import BaseView
import sqlite3
from tkinter import messagebox, Button
import db  # Import the db module
import tkinter.simpledialog as simpledialog


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


    def modify(self, app, selected_rows):
        if not selected_rows:
            return
        if len(selected_rows) > 1:
            messagebox.showwarning("Warning", "Please select only one location to modify.")
            return

        col = {name: i for i, name in enumerate(self.columns)}
        row = selected_rows[0]
        location_id = row[col["StandortID"]]
        current_name = row[col["Standort"]]

        new_name = simpledialog.askstring(
            "Modify Location",
            "Enter new location name:",
            initialvalue=current_name
        )

        if new_name is None:  # User cancelled
            return
        if not new_name.strip():
            messagebox.showwarning("Warning", "Location name cannot be empty.")
            return
        if new_name.strip() == current_name:
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE lieugestion SET Standort = ? WHERE StandortID = ?",
                    (new_name.strip(), location_id)
                )
            app.refresh_view()
            messagebox.showinfo("Success", "Location updated successfully.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot update location:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")



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
       
