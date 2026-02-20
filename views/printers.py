from .base_view import BaseView
import sqlite3

import db  # Import the db module
from functools import partial
from tkinter import ttk
from tkinter import messagebox
import tkinter as tk


# =====================
# Concrete Views
# =====================
class PrintersView(BaseView):
    name = "printers"
    columns = ["PrinterName", "Printerslots*", "CARIdocs*", "Bureaus*", "PrinterModel", "Standort"]
    columns_actions = {
        "#2": "show_printer_slots",
        "#3": "show_caridocs",  
        "#4": "show_bureaus"  
    }
    query = """
         SELECT 
        p.PrinterName,

        -- Anzahl Slots
        (
            SELECT COUNT(*)
            FROM printerslots ps
            WHERE ps.PrinterName = p.PrinterName
        ) AS "Anzahl Slots",

        -- Anzahl CARI-Docs (DISTINCT über mehrere Spalten)
        (
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT SlotName, CARIdoc
                FROM slot_caridocs sc
                WHERE sc.PrinterName = p.PrinterName
            )
        ) AS "Anzahl CARI-Docs",

        -- Anzahl Bureaus (distinct BureauID)
        (
            SELECT COUNT(DISTINCT sc.BureauID)
            FROM slot_caridocs sc
            WHERE sc.PrinterName = p.PrinterName
        ) AS "Anzahl Bureaus",

        p.PrinterModel,
        l.Standort

    FROM printernames p
    LEFT JOIN lieugestion l ON p.StandortID = l.StandortID
    ORDER BY p.PrinterName;
        """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filtered_bureau = None  # Initialize the filter to None
    
    def get_query(self):
        """Return query, optionally filtered by bureau id"""
        if self.filtered_bureau:
            return f"""
                SELECT 
                p.PrinterName,

                -- Anzahl Slots
                (
                    SELECT COUNT(*)
                    FROM printerslots ps
                    WHERE ps.PrinterName = p.PrinterName
                ) AS "Anzahl Slots",

                -- Anzahl CARI-Docs (DISTINCT über mehrere Spalten)
                (
                    SELECT COUNT(*)
                    FROM (
                        SELECT DISTINCT SlotName, CARIdoc
                        FROM slot_caridocs sc
                        WHERE sc.PrinterName = p.PrinterName
                    )
                ) AS "Anzahl CARI-Docs",

                -- Anzahl Bureaus (distinct BureauID)
                (
                    SELECT COUNT(DISTINCT sc.BureauID)
                    FROM slot_caridocs sc
                    WHERE sc.PrinterName = p.PrinterName
                ) AS "Anzahl Bureaus",

                p.PrinterModel,
                l.Standort

            FROM printernames p
            LEFT JOIN lieugestion l ON p.StandortID = l.StandortID
            WHERE EXISTS (
                SELECT 1
                FROM slot_caridocs sc
                WHERE sc.PrinterName = p.PrinterName
                AND sc.BureauID = '{self.filtered_bureau}'
            )
            ORDER BY p.PrinterName;
            """
        # otherwise return full query
        return self.query
    
    def set_filter(self, printer_name=None, slot_name=None, bureau_id=None):
        """Set the bureau filter"""
        self.filtered_bureau = bureau_id
        self.filtered_printer = None
        self.filtered_slot = None
    
    
    def clear_filter(self):
        """Clear the bureau filter"""
        self.filtered_bureau = None

    def on_view_shown(self, app, frame):
        """Called when view is shown - override for custom behavior"""


    def modify(self, app, selected_rows):
        if not selected_rows:
            return
        if len(selected_rows) > 1:
            messagebox.showwarning("Warning", "Please select only one printer to modify.")
            return

        row = selected_rows[0]
        current_printer_name = row[0]
        current_model = row[4]
        current_standort = row[5]

        # --- Fetch available options ---
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT StandortID, Standort FROM lieugestion ORDER BY Standort")
                locations = cur.fetchall()
                cur.execute("SELECT PrinterModel FROM printermodels ORDER BY PrinterModel")
                models = [r[0] for r in cur.fetchall()]
                cur.execute("SELECT StandortID FROM printernames WHERE PrinterName = ?", (current_printer_name,))
                result = cur.fetchone()
                current_standort_id = result[0] if result else None
        except Exception as e:
            messagebox.showerror("Error", f"Could not load data:\n{str(e)}")
            return

        # --- Build dialog ---
        dialog = tk.Toplevel(app.root)
        dialog.title("Modify Printer")
        dialog.resizable(False, False)
        dialog.grab_set()

        pad = {"padx": 10, "pady": 5}

        tk.Label(dialog, text="Printer Name:").grid(row=0, column=0, sticky="e", **pad)
        name_var = tk.StringVar(value=current_printer_name)
        tk.Entry(dialog, textvariable=name_var, width=30).grid(row=0, column=1, **pad)

        tk.Label(dialog, text="Printer Model:").grid(row=1, column=0, sticky="e", **pad)
        model_var = tk.StringVar()
        model_cb = ttk.Combobox(dialog, textvariable=model_var, values=models,
                                state="readonly", width=28)
        if current_model in models:
            model_cb.current(models.index(current_model))
        model_cb.grid(row=1, column=1, **pad)

        tk.Label(dialog, text="Standort:").grid(row=2, column=0, sticky="e", **pad)
        location_names = [loc[1] for loc in locations]
        location_ids   = [loc[0] for loc in locations]
        standort_var = tk.StringVar()
        standort_cb = ttk.Combobox(dialog, textvariable=standort_var, values=location_names,
                                    state="readonly", width=28)
        if current_standort_id in location_ids:
            standort_cb.current(location_ids.index(current_standort_id))
        standort_cb.grid(row=2, column=1, **pad)

        confirmed = {"value": False}

        def on_confirm():
            confirmed["value"] = True
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="Save",   width=10, command=on_confirm).pack(side="left",  padx=5)
        tk.Button(btn_frame, text="Cancel", width=10, command=on_cancel).pack(side="right", padx=5)

        dialog.wait_window()

        if not confirmed["value"]:
            return

        # --- Validate ---
        new_name  = name_var.get().strip()
        new_model = model_var.get()

        if not new_name:
            messagebox.showwarning("Warning", "Printer name cannot be empty.")
            return
        if not new_model:
            messagebox.showwarning("Warning", "Please select a valid printer model.")
            return

        new_standort_name = standort_var.get()
        selected_index = location_names.index(new_standort_name) if new_standort_name in location_names else None
        if selected_index is None:
            messagebox.showwarning("Warning", "Please select a valid location.")
            return
        new_standort_id = location_ids[selected_index]

        # --- Persist ---
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE printernames
                    SET PrinterName  = ?,
                        PrinterModel = ?,
                        StandortID   = ?
                    WHERE PrinterName = ?
                """, (new_name, new_model, new_standort_id, current_printer_name))

            app.refresh_view()
            messagebox.showinfo("Success", "Printer updated successfully.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot update printer:\n{str(e)}\n"
                                        "A printer with that name may already exist.")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
            

        
    def delete(self, app, selected_rows):

        if not selected_rows:
            return

        # PrinterName is column 0
        printer_names = [row[0] for row in selected_rows]

        placeholders = ",".join("?" for _ in printer_names)

        # --- Check slot counts for all selected printers ---
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(f"""
                    SELECT PrinterName, COUNT(*)
                    FROM printerslots
                    WHERE PrinterName IN ({placeholders})
                    GROUP BY PrinterName
                """, printer_names)

                slot_counts = dict(cur.fetchall())

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not check printer slots:\n{str(e)}"
            )
            return

        # --- Build confirmation message ---
        lines = [
            f"• {name} ({slot_counts.get(name, 0)} slot(s))"
            for name in printer_names
        ]

        message = (
            f"You are about to delete {len(printer_names)} printer(s):\n\n"
            + "\n".join(lines)
        )

        if any(slot_counts.values()):
            message += (
                "\n\nDeleting the printers will also delete all their slots "
                "and CARIdoc assignments."
            )

        # --- Ask for confirmation ---
        if not messagebox.askyesno("Delete Printers", message):
            return

        # --- Delete printers (cascade handles the rest) ---
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    f"DELETE FROM printernames WHERE PrinterName IN ({placeholders})",
                    printer_names
                )

            app.refresh_view()
            messagebox.showinfo(
                "Success",
                f"{len(printer_names)} printer(s) deleted successfully."
            )

        except sqlite3.IntegrityError as e:
            messagebox.showerror(
                "Error",
                f"Cannot delete printer(s):\n{str(e)}"
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Unexpected error:\n{str(e)}"
            )


    def build_context_menu(self, app, menu, selected_rows):
        """Add PrintersView-specific context menu items"""
        if not selected_rows:
            return

        #TODO: change function, this is only for testing
        menu.add_command(
            label="Add printer",
            command=lambda: [
                self.clear_filter(),
                app.refresh_view()
            ]
        )
