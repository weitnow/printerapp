from .base_view import BaseView
import sqlite3
from tkinter import messagebox, Button, simpledialog
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

    def add(self, app):
        """Add a new department to the database"""
        new_name = simpledialog.askstring(
            "Add Department",
            "Enter new department name:",
        )

        if new_name is None:
            return
        if not new_name.strip():
            messagebox.showwarning("Warning", "Department name cannot be empty.")
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO fachabteilung (Fachabteilung) VALUES (?)",
                    (new_name.strip(),),
                )
            app.refresh_view()
            messagebox.showinfo("Success", "Department added successfully.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot add department:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")


    def modify(self, app, selected_rows):
        if not selected_rows:
            return
        if len(selected_rows) > 1:
            messagebox.showwarning("Warning", "Please select only one department to modify.")
            return

        col = {name: i for i, name in enumerate(self.columns)}
        row = selected_rows[0]
        department_id = row[col["FachabteilungID"]]
        current_name = row[col["Fachabteilung"]]

        new_name = simpledialog.askstring(
            "Modify Department",
            "Enter new department name:",
            initialvalue=current_name,
        )

        if new_name is None:
            return
        if not new_name.strip():
            messagebox.showwarning("Warning", "Department name cannot be empty.")
            return
        if new_name.strip() == current_name:
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE fachabteilung SET Fachabteilung = ? WHERE FachabteilungID = ?",
                    (new_name.strip(), department_id),
                )
            app.refresh_view()
            messagebox.showinfo("Success", "Department updated successfully.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot update Department:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")



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
       
