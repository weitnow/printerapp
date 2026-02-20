from .base_view import BaseView
from tkinter import messagebox, simpledialog
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

    def modify(self, app, selected_rows):
        if not selected_rows:
            return
        if len(selected_rows) > 1:
            messagebox.showwarning("Warning", "Please select only one CARIdoc to modify.")
            return

        col = {name: i for i, name in enumerate(self.columns)}
        row = selected_rows[0]

        caridoc = row[col["CARIdoc"]]
        current_description = row[col["CARIDocument"]]

        new_description = simpledialog.askstring(
            "Modify CARIdoc description",
            f"CARIdoc: {caridoc}\n\nEnter new description:",
            initialvalue=current_description,
        )
        if new_description is None:
            return
        if not new_description.strip():
            messagebox.showwarning("Warning", "Description cannot be empty.")
            return
        if new_description.strip() == current_description:
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE caridocs SET BeschreibungFormular = ? WHERE CARIdoc = ?",
                    (new_description.strip(), caridoc),
                )
            app.refresh_view()
            messagebox.showinfo("Success", "CARIdoc updated successfully.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot update CARIdoc:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")

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