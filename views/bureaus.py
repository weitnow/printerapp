from .base_view import BaseView
import sqlite3
from tkinter import messagebox, Button
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
