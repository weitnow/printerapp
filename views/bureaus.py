from .base_view import BaseView
import sqlite3
from tkinter import messagebox, Button
import tkinter as tk
from tkinter import ttk
import db  # Import the db module

class BureausView(BaseView):
    name = "bureaus"
    columns = ["BureauID", "Bureau", "Printers*", "CARIdocs*", "Fachabteilung", "Standort"]
    columns_actions = {
        "#3": "show_printers_from_bureaus",
        "#4": "show_caridocs_from_bureaus"
    }
    query = """
    SELECT
    b.BureauID,
    b.Bureau,
    (
        SELECT COUNT(DISTINCT sc.PrinterName)
        FROM slot_caridocs sc 
        WHERE sc.BureauID = b.BureauID
    ) AS 'Printers',
    (
        SELECT COUNT(*) 
        FROM (
            SELECT DISTINCT SlotName, CARIdoc
            FROM slot_caridocs sc 
            WHERE sc.BureauID = b.BureauID
            )
    ) AS 'Anzahl CARI-Docs',
    f.Fachabteilung,
    l.Standort
    FROM bureaus b
    LEFT JOIN fachabteilung f ON b.FachabteilungID = f.FachabteilungID
    LEFT JOIN lieugestion l ON b.StandortID = l.StandortID
    ORDER BY b.BureauID
    """


    def add(self, app):
        """Add a new bureau to the database"""
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()

                cur.execute("SELECT FachabteilungID, Fachabteilung FROM fachabteilung ORDER BY Fachabteilung")
                departments = cur.fetchall()

                cur.execute("SELECT StandortID, Standort FROM lieugestion ORDER BY StandortID")
                locations = cur.fetchall()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load lookup data:\n{str(e)}")
            return

        dialog = tk.Toplevel(app.root)
        dialog.title("Add New Bureau")
        dialog.resizable(False, False)
        dialog.grab_set()

        pad = {"padx": 10, "pady": 5}

        tk.Label(dialog, text="Bureau name:").grid(row=0, column=0, sticky="e", **pad)
        name_var = tk.StringVar()
        tk.Entry(dialog, textvariable=name_var, width=30).grid(row=0, column=1, **pad)

        tk.Label(dialog, text="Department:").grid(row=1, column=0, sticky="e", **pad)
        dept_names = [d[1] for d in departments]
        dept_ids = [d[0] for d in departments]
        dept_var = tk.StringVar()
        dept_cb = ttk.Combobox(dialog, textvariable=dept_var, values=dept_names, state="readonly", width=28)
        dept_cb.grid(row=1, column=1, **pad)

        tk.Label(dialog, text="Location:").grid(row=2, column=0, sticky="e", **pad)
        loc_names = [l[1] for l in locations]
        loc_ids = [l[0] for l in locations]
        loc_var = tk.StringVar()
        loc_cb = ttk.Combobox(dialog, textvariable=loc_var, values=loc_names, state="readonly", width=28)
        loc_cb.grid(row=2, column=1, **pad)

        confirmed = {"value": False}

        def on_confirm():
            confirmed["value"] = True
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="Add", width=10, command=on_confirm).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", width=10, command=on_cancel).pack(side="right", padx=5)

        dialog.wait_window()

        if not confirmed["value"]:
            return

        new_name = name_var.get().strip()
        if not new_name:
            messagebox.showwarning("Warning", "Bureau name cannot be empty.")
            return

        dept_name = dept_var.get()
        loc_name = loc_var.get()

        new_dept_id = None
        new_loc_id = None

        if dept_name:
            try:
                idx = dept_names.index(dept_name)
                new_dept_id = dept_ids[idx]
            except ValueError:
                pass

        if loc_name:
            try:
                idx = loc_names.index(loc_name)
                new_loc_id = loc_ids[idx]
            except ValueError:
                pass

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO bureaus (Bureau, FachabteilungID, StandortID)
                    VALUES (?, ?, ?)
                    """,
                    (new_name, new_dept_id, new_loc_id),
                )

            app.refresh_view()
            messagebox.showinfo("Success", "Bureau added successfully.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot add bureau:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")


    def modify(self, app, selected_rows):
        if not selected_rows:
            return
        if len(selected_rows) > 1:
            messagebox.showwarning("Warning", "Please select only one bureau to modify.")
            return

        row = selected_rows[0]
        col = {name: i for i, name in enumerate(self.columns)}

        bureau_id = row[col["BureauID"]]
        current_name = row[col["Bureau"]]
        current_department = row[col["Fachabteilung"]]
        current_location = row[col["Standort"]]

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()

                cur.execute("SELECT FachabteilungID, Fachabteilung FROM fachabteilung ORDER BY Fachabteilung")
                departments = cur.fetchall()

                cur.execute("SELECT StandortID, Standort FROM lieugestion ORDER BY StandortID")
                locations = cur.fetchall()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load lookup data:\n{str(e)}")
            return

        dialog = tk.Toplevel(app.root)
        dialog.title("Modify Bureau")
        dialog.resizable(False, False)
        dialog.grab_set()

        pad = {"padx": 10, "pady": 5}

        tk.Label(dialog, text=f"Bureau ID: {bureau_id}").grid(row=0, column=0, columnspan=2, sticky="w", **pad)

        tk.Label(dialog, text="Bureau name:").grid(row=1, column=0, sticky="e", **pad)
        name_var = tk.StringVar(value=current_name)
        tk.Entry(dialog, textvariable=name_var, width=30).grid(row=1, column=1, **pad)

        tk.Label(dialog, text="Department:").grid(row=2, column=0, sticky="e", **pad)
        dept_names = [d[1] for d in departments]
        dept_ids = [d[0] for d in departments]
        dept_var = tk.StringVar()
        dept_cb = ttk.Combobox(dialog, textvariable=dept_var, values=dept_names, state="readonly", width=28)
        if current_department in dept_names:
            dept_cb.current(dept_names.index(current_department))
        dept_cb.grid(row=2, column=1, **pad)

        tk.Label(dialog, text="Location:").grid(row=3, column=0, sticky="e", **pad)
        loc_names = [l[1] for l in locations]
        loc_ids = [l[0] for l in locations]
        loc_var = tk.StringVar()
        loc_cb = ttk.Combobox(dialog, textvariable=loc_var, values=loc_names, state="readonly", width=28)
        if current_location in loc_names:
            loc_cb.current(loc_names.index(current_location))
        loc_cb.grid(row=3, column=1, **pad)

        confirmed = {"value": False}

        def on_confirm():
            confirmed["value"] = True
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="Save", width=10, command=on_confirm).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", width=10, command=on_cancel).pack(side="right", padx=5)

        dialog.wait_window()

        if not confirmed["value"]:
            return

        new_name = name_var.get().strip()
        if not new_name:
            messagebox.showwarning("Warning", "Bureau name cannot be empty.")
            return

        dept_name = dept_var.get()
        loc_name = loc_var.get()

        new_dept_id = None
        new_loc_id = None

        if dept_name:
            try:
                idx = dept_names.index(dept_name)
                new_dept_id = dept_ids[idx]
            except ValueError:
                messagebox.showwarning("Warning", "Please select a valid department.")
                return

        if loc_name:
            try:
                idx = loc_names.index(loc_name)
                new_loc_id = loc_ids[idx]
            except ValueError:
                messagebox.showwarning("Warning", "Please select a valid location.")
                return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE bureaus
                    SET Bureau = ?,
                        FachabteilungID = ?,
                        StandortID = ?
                    WHERE BureauID = ?
                    """,
                    (new_name, new_dept_id, new_loc_id, bureau_id),
                )

            app.refresh_view()
            messagebox.showinfo("Success", "Bureau updated successfully.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot update bureau:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")


    def get_query(self):
        """Return query, optionally filtered by printer name"""
        if self.filtered_printer:
            return f"""
                SELECT
                    b.BureauID,
                    b.Bureau,
                    (
                        SELECT COUNT(DISTINCT sc.PrinterName)
                        FROM slot_caridocs sc 
                        WHERE sc.BureauID = b.BureauID
                    ) AS 'Printers',
                    (
                        SELECT COUNT(*) 
                        FROM (
                            SELECT DISTINCT SlotName, CARIdoc
                            FROM slot_caridocs sc 
                            WHERE sc.BureauID = b.BureauID
                            AND sc.PRINTERNAME = '{self.filtered_printer}'
                            )
                    ) AS 'Anzahl CARI-Docs',
                    f.Fachabteilung,
                    l.Standort
                FROM bureaus b
                LEFT JOIN fachabteilung f ON b.FachabteilungID = f.FachabteilungID
                LEFT JOIN lieugestion l ON b.StandortID = l.StandortID
                WHERE EXISTS (
                    SELECT 1
                    FROM slot_caridocs sc2
                    WHERE sc2.BureauID = b.BureauID
                    AND sc2.PrinterName = '{self.filtered_printer}'
                )
            """
        return self.query
    
    def set_filter(self, printer_name=None):
        """Set the printer filter"""
        self.filtered_printer = printer_name
   
    
    def clear_filter(self):
        """Clear the printer filter"""
        self.filtered_printer = None



    def delete(self, app, selected_rows):

        if not selected_rows:
            return

        bureau_ids = [row[0] for row in selected_rows]

        message = (
            "You are about to delete the following Bureau ID(s):\n\n"
            + "\n".join(f"• {bid}" for bid in bureau_ids)
            + "\n\n⚠️ Bureaus should normally NOT be deleted, because the BureauID is "
            "used in CARI.\n\nDo you want to continue?"
        )

        if not messagebox.askyesno("Delete Bureaus", message):
            return

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.executemany(
                    "DELETE FROM bureaus WHERE BureauID = ?",
                    [(bid,) for bid in bureau_ids]
                )

            app.refresh_view()
            messagebox.showinfo(
                "Success",
                f"{len(bureau_ids)} bureau(s) deleted successfully."
            )

        except sqlite3.IntegrityError as e:
            messagebox.showerror(
                "Error",
                "Cannot delete bureau(s) because there are still referenced "
                "Printers and/or CARIdocs. Delete them first.\n\n" + str(e)
            )
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
