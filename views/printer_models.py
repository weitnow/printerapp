from .base_view import BaseView
import sqlite3
from tkinter import messagebox, Button, simpledialog
import db  # Import the db module


class PrinterModels(BaseView):
    name = "printer_models"
    columns = ["PrinterModel"]
    columns_actions = {}
    query = """
    SELECT
    PrinterModel
    FROM printermodels

    ORDER BY PrinterModel
    """

    def add(self, app):
        """Add a new printer model to the database"""
        new_model = simpledialog.askstring(
            "Add Printer Model",
            "Enter new printer model name:",
        )

        if new_model is None:
            return
        if not new_model.strip():
            messagebox.showwarning("Warning", "Printer model name cannot be empty.")
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO printermodels (PrinterModel) VALUES (?)",
                    (new_model.strip(),),
                )
            app.refresh_view()
            messagebox.showinfo("Success", "Printer model added successfully.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot add printer model:\n{str(e)}\nModel may already exist.")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")

    def modify(self, app, selected_rows):
        if not selected_rows:
            return
        if len(selected_rows) > 1:
            messagebox.showwarning("Warning", "Please select only one printer model to modify.")
            return

        col = {name: i for i, name in enumerate(self.columns)}
        row = selected_rows[0]
        current_model = row[col["PrinterModel"]]

        new_model = simpledialog.askstring(
            "Modify Printer Model",
            "The change will be applied to all printers using this model.\nEnter new printer model name:",
            initialvalue=current_model
        )

        if new_model is None:  # User cancelled
            return
        if not new_model.strip():
            messagebox.showwarning("Warning", "Printer model name cannot be empty.")
            return
        if new_model.strip() == current_model:
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE printermodels SET PrinterModel = ? WHERE PrinterModel = ?",
                    (new_model.strip(), current_model)
                )
            app.refresh_view()
            messagebox.showinfo("Success", "Printer model updated successfully.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot update printer model:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")


    
    def delete(self, app, selected_rows):
        if not selected_rows:
            return
        
        if not messagebox.askyesno(
            "Delete",
            "Are you sure you want to delete the selected Printer Model(s)?"
        ):
            return

        try:
            col = {name: i for i, name in enumerate(self.columns)}

            with db.get_connection() as conn:
                cur = conn.cursor()
                deleted = 0
                
                for row in selected_rows:
                    printer_model = (row[col["PrinterModel"]])

                    cur.execute("DELETE FROM printermodels WHERE PrinterModel = ?",
                    (printer_model,)
                    )

                    deleted += 1

            if deleted:
                app.refresh_view()
                messagebox.showinfo("Success", f"{deleted} Printer Model(s) deleted successfully.")

        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot delete Printer Model(s):\n{str(e)}" + 
                                 "\nPlease ensure that the Printer Model(s) are not in use.")

        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")


