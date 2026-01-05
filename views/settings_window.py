import threading
import tkinter as tk
from tkinter import messagebox, filedialog

from xlsx_import import run_import


class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Settings")
        self.geometry("700x250")
        self.resizable(False, False)

        # Optional: make it modal
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ========================
        # IMPORT XLSX
        # ========================
        self._row(
            frame,
            "Import XLSX:",
            "Import",
            self.import_xlsx
        )

        # ========================
        # EXPORT XLSX
        # ========================
        self._row(
            frame,
            "Export XLSX:",
            "Export",
            self.export_xlsx
        )

        # ========================
        # DATABASE FILE
        # ========================
        self._row(
            frame,
            "Database file:",
            "Use it",
            self.use_database
        )

    def _row(self, parent, label, button_text, command):
        row = tk.Frame(parent)
        row.pack(fill="x", pady=6)

        tk.Label(row, text=label, width=15, anchor="w").pack(side="left")

        entry = tk.Entry(row)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        tk.Button(row, text=button_text, command=lambda e=entry: command(e)).pack(side="left")

    # ========================
    # Callbacks
    # ========================

    def import_xlsx(self, entry):
        # Optional: let user pick a file
        filename = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if not filename:
            return

        entry.delete(0, tk.END)
        entry.insert(0, filename)

        # Run import in a separate thread to avoid freezing UI
        def import_thread():
            try:
                run_import(xlsx_file=filename)
                messagebox.showinfo("Import", "✅ Import finished successfully!")
            except Exception as e:
                messagebox.showerror("Import Error", str(e))

            threading.Thread(target=import_thread, daemon=True).start()

    def export_xlsx(self, entry):
        messagebox.showinfo("Export", entry.get())

    def use_database(self, entry):
        messagebox.showinfo("Database", entry.get())
