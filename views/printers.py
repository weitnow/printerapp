from .base_view import BaseView
import sqlite3
from tkinter import messagebox
import db  # Import the db module
from functools import partial

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
