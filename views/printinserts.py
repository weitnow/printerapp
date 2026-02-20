from .base_view import BaseView
import sqlite3
from tkinter import messagebox, Button, simpledialog
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

    def add(self, app):
        """Add a new print insert to the database"""
        format_name = simpledialog.askstring(
            "Add Print Insert",
            "Enter format name:",
        )
        if format_name is None:
            return
        format_name = format_name.strip()
        if not format_name:
            messagebox.showwarning("Warning", "Format name cannot be empty.")
            return

        width_str = simpledialog.askstring(
            "Add Print Insert - Width",
            f"Format: {format_name}\n\nEnter width in mm:",
        )
        if width_str is None:
            return

        height_str = simpledialog.askstring(
            "Add Print Insert - Height",
            f"Format: {format_name}\n\nEnter height in mm:",
        )
        if height_str is None:
            return

        try:
            width = float(width_str.replace(",", "."))
            height = float(height_str.replace(",", "."))
        except ValueError:
            messagebox.showwarning("Warning", "Width and height must be numeric.")
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO druckeinlage (FormatDruckeinlage, WidthMM, HeightMM)
                    VALUES (?, ?, ?)
                    """,
                    (format_name, width, height),
                )
            app.refresh_view()
            messagebox.showinfo("Success", "Print insert added successfully.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot add print insert:\n{str(e)}\nFormat may already exist.")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")


    def modify(self, app, selected_rows):
        if not selected_rows:
            return
        if len(selected_rows) > 1:
            messagebox.showwarning("Warning", "Please select only one print insert to modify.")
            return

        col = {name: i for i, name in enumerate(self.columns)}
        row = selected_rows[0]

        format_name = row[col["FormatDruckeinlage"]]
        current_width = row[col["Breite mm"]]
        current_height = row[col["Höhe mm"]]

        new_width_str = simpledialog.askstring(
            "Modify Print Insert - Width",
            f"Format: {format_name}\n\nEnter new width in mm:",
            initialvalue=str(current_width),
        )
        if new_width_str is None:
            return

        new_height_str = simpledialog.askstring(
            "Modify Print Insert - Height",
            f"Format: {format_name}\n\nEnter new height in mm:",
            initialvalue=str(current_height),
        )
        if new_height_str is None:
            return

        try:
            new_width = float(new_width_str.replace(",", "."))
            new_height = float(new_height_str.replace(",", "."))
        except ValueError:
            messagebox.showwarning("Warning", "Width and height must be numeric.")
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE druckeinlage
                    SET WidthMM = ?, HeightMM = ?
                    WHERE FormatDruckeinlage = ?
                    """,
                    (new_width, new_height, format_name),
                )
            app.refresh_view()
            messagebox.showinfo("Success", "Print insert updated successfully.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot update print insert:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")


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
       
