from .base_view import BaseView
import sqlite3
from tkinter import messagebox, simpledialog, ttk
import tkinter as tk
import db  # Import the db module

class SlotPrinter(BaseView):
    name = "printer_slots"
    columns = ["PrinterName", "SlotName*", "PaperFormat", "TwoSided", "Autoprint", "Bemerkung"]
    columns_actions = {
        "#2": "show_caridocs_of_slot"
    }
    query = """
    SELECT
        PrinterName,
        SlotName,
        PaperFormat,
        TwoSided,
        Autoprint,
        Bemerkung
    FROM printerslots
    ORDER BY PrinterName, SlotName
    """
    
    def __init__(self):
        super().__init__()
        self.filtered_printer = None

    def get_query(self):
        """Return query, optionally filtered by printer name"""
        if self.filtered_printer:
            return f"""
                SELECT
                    PrinterName,
                    SlotName,
                    PaperFormat,
                    TwoSided,
                    Autoprint,
                    Bemerkung
                FROM printerslots
                WHERE PrinterName = '{self.filtered_printer}'
                ORDER BY SlotName
            """
        return self.query
    
  
    
    def set_filter(self, printer_name):
        """Set the printer filter"""
        self.filtered_printer = printer_name
    
    def clear_filter(self):
        """Clear the printer filter"""
        self.filtered_printer = None
    
    def add(self, app):
        """Add a new printer slot to the database"""
        # --- Fetch available printers ---
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT PrinterName FROM printernames ORDER BY PrinterName")
                printers = [r[0] for r in cur.fetchall()]
        except Exception as e:
            messagebox.showerror("Error", f"Could not load data:\n{str(e)}")
            return

        if not printers:
            messagebox.showwarning("Warning", "No printers available. Please add a printer first.")
            return

        # --- Build dialog ---
        dialog = tk.Toplevel(app.root)
        dialog.title("Add Printer Slot")
        dialog.resizable(False, False)
        dialog.grab_set()

        pad = {"padx": 10, "pady": 5}

        tk.Label(dialog, text="Printer:").grid(row=0, column=0, sticky="e", **pad)
        printer_var = tk.StringVar(value=self.filtered_printer if self.filtered_printer else "")
        printer_cb = ttk.Combobox(dialog, textvariable=printer_var, values=printers,
                                  state="readonly", width=28)
        if self.filtered_printer and self.filtered_printer in printers:
            printer_cb.current(printers.index(self.filtered_printer))
        printer_cb.grid(row=0, column=1, **pad)

        tk.Label(dialog, text="Slot Name:").grid(row=1, column=0, sticky="e", **pad)
        slot_var = tk.StringVar()
        tk.Entry(dialog, textvariable=slot_var, width=30).grid(row=1, column=1, **pad)

        tk.Label(dialog, text="Paper Format:").grid(row=2, column=0, sticky="e", **pad)
        format_var = tk.StringVar()
        tk.Entry(dialog, textvariable=format_var, width=30).grid(row=2, column=1, **pad)

        tk.Label(dialog, text="Two Sided:").grid(row=3, column=0, sticky="e", **pad)
        twosided_var = tk.StringVar(value="0")
        ttk.Combobox(dialog, textvariable=twosided_var, values=["0", "1"],
                     state="readonly", width=28).grid(row=3, column=1, **pad)

        tk.Label(dialog, text="Autoprint:").grid(row=4, column=0, sticky="e", **pad)
        autoprint_var = tk.StringVar(value="0")
        ttk.Combobox(dialog, textvariable=autoprint_var, values=["0", "1"],
                     state="readonly", width=28).grid(row=4, column=1, **pad)

        tk.Label(dialog, text="Remark (optional):").grid(row=5, column=0, sticky="e", **pad)
        remark_var = tk.StringVar()
        tk.Entry(dialog, textvariable=remark_var, width=30).grid(row=5, column=1, **pad)

        confirmed = {"value": False}

        def on_confirm():
            confirmed["value"] = True
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="Add", width=10, command=on_confirm).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", width=10, command=on_cancel).pack(side="right", padx=5)

        dialog.wait_window()

        if not confirmed["value"]:
            return

        # --- Validate ---
        printer_name = printer_var.get()
        slot_name = slot_var.get().strip()
        paper_format = format_var.get().strip()
        two_sided = twosided_var.get()
        autoprint = autoprint_var.get()
        remark = remark_var.get().strip()

        if not printer_name:
            messagebox.showwarning("Warning", "Please select a printer.")
            return
        if not slot_name:
            messagebox.showwarning("Warning", "Slot name cannot be empty.")
            return
        if not paper_format:
            messagebox.showwarning("Warning", "Paper format cannot be empty.")
            return

        # --- Persist ---
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO printerslots (PrinterName, SlotName, PaperFormat, TwoSided, Autoprint, Bemerkung)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (printer_name, slot_name, paper_format, two_sided, autoprint, remark if remark else None))

            app.refresh_view()
            messagebox.showinfo("Success", "Printer slot added successfully.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot add slot:\n{str(e)}\nThis slot may already exist for this printer.")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")

    def modify(self, app, selected_rows):
        if not selected_rows:
            return
        if len(selected_rows) > 1:
            messagebox.showwarning("Warning", "Please select only one slot to modify.")
            return

        col = {name: i for i, name in enumerate(self.columns)}
        row = selected_rows[0]

        printer_name = row[col["PrinterName"]]
        slot_name = row[col["SlotName*"]]
        current_format = row[col["PaperFormat"]]
        current_two_sided = row[col["TwoSided"]]
        current_autoprint = row[col["Autoprint"]]
        current_remark = row[col["Bemerkung"]]

        new_format = simpledialog.askstring(
            "Modify Slot - Paper Format",
            f"Printer: {printer_name}\nSlot: {slot_name}\n\nEnter new paper format:",
            initialvalue=current_format,
        )
        if new_format is None:
            return
        new_format = new_format.strip()
        if not new_format:
            messagebox.showwarning("Warning", "Paper format cannot be empty.")
            return

        new_remark = simpledialog.askstring(
            "Modify Slot - Remark",
            f"Printer: {printer_name}\nSlot: {slot_name}\n\nEnter new remark (optional):",
            initialvalue=current_remark or "",
        )
        if new_remark is None:
            # Allow cancel of remark edit without aborting whole modify
            new_remark = current_remark

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE printerslots
                    SET PaperFormat = ?,
                        Bemerkung = ?
                    WHERE PrinterName = ?
                      AND SlotName = ?
                    """,
                    (new_format, new_remark, printer_name, slot_name),
                )

            app.refresh_view()
            messagebox.showinfo("Success", "Slot updated successfully.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot update slot:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
    
    def delete(self, app, selected_rows):
        if not selected_rows:
            return

        # Each row: (PrinterName, SlotName, ...)
        slots = [(row[0], row[1]) for row in selected_rows]

        # --- Build confirmation message ---
        lines = [
            f"• {printer} → {slot}"
            for printer, slot in slots
        ]

        message = (
            f"You are about to delete {len(slots)} slot(s):\n\n"
            + "\n".join(lines)
            + "\n\nDeleting slots will also delete all assigned CARIdocs."
        )

        if not messagebox.askyesno("Delete Slots", message):
            return

        # --- Delete slots (cascade handles slot_caridocs) ---
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()

                cur.executemany(
                    "DELETE FROM printerslots WHERE PrinterName = ? AND SlotName = ?",
                    slots
                )

            app.refresh_view()
            messagebox.showinfo(
                "Success",
                f"{len(slots)} slot(s) deleted successfully."
            )

        except sqlite3.IntegrityError as e:
            messagebox.showerror(
                "Error",
                f"Cannot delete slot(s):\n{str(e)}"
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Unexpected error:\n{str(e)}"
            )
