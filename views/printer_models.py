from .base_view import BaseView
import sqlite3
from tkinter import messagebox, Button
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



       
