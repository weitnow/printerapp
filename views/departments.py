from .base_view import BaseView
import sqlite3
from tkinter import messagebox, Button
import db  # Import the db module

class DepartmentView(BaseView):
    name = "departments"
    columns = ["FachabteilungID", "Fachabteilung"]
    columns_actions = {}
    query = """
    SELECT
    FachabteilungID,
    Fachabteilung
    FROM fachabteilung

    ORDER BY FachabteilungID
    """



    def delete(self, app, selected_rows):
        if not selected_rows:
            return
        
        if not messagebox.askyesno(
            "Delete",
            "Are you sure you want to delete the selected Department(s)?"
        ):
            return

        try:
            col = {name: i for i, name in enumerate(self.columns)}

            with db.get_connection() as conn:
                cur = conn.cursor()
                deleted = 0
                
                for row in selected_rows:
                    department_id = (row[col["FachabteilungID"]])

                    cur.execute("DELETE FROM fachabteilung WHERE FachabteilungID = ?",
                    (department_id,)
                    )

                    deleted += 1

            if deleted:
                app.refresh_view()
                messagebox.showinfo("Success", f"{deleted} Department(s) deleted successfully.")

        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot delete Department(s):\n{str(e)}" + 
                                 "\nPlease ensure that the Department(s) are not in use.")

        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
       
