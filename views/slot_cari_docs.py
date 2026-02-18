from .base_view import BaseView
import sqlite3
from tkinter import messagebox
import db  # Import the db module


class SlotCariDoc(BaseView):
    name = "all_slots"
    columns = [
        "PrinterName", "PrinterModel", "SlotName", "PaperFormat",
        "TwoSided", "Autoprint", "SlotRemark", "CARIdoc", "CARIDocument",
        "Bureau", "BureauID", "Department", "Location",
        "BureauRemark"
    ]

    query = """
    SELECT
        pn.PrinterName,
        pn.PrinterModel,
        ps.SlotName,
        ps.PaperFormat,
        ps.TwoSided,
        ps.Autoprint,
        ps.Bemerkung AS SlotBemerkung,
        sc.CARIdoc,
        cd.BeschreibungFormular,
        b.Bureau,
        b.BureauID,
        f.Fachabteilung,
        l.Standort,
        sc.Bemerkung AS BureauBemerkung
    FROM printernames pn
    LEFT JOIN printerslots ps ON pn.PrinterName = ps.PrinterName
    LEFT JOIN slot_caridocs sc
        ON ps.PrinterName = sc.PrinterName
        AND ps.SlotName = sc.SlotName
    LEFT JOIN caridocs cd ON sc.CARIdoc = cd.CARIdoc
    LEFT JOIN bureaus b ON sc.BureauID = b.BureauID
    LEFT JOIN fachabteilung f ON b.FachabteilungID = f.FachabteilungID
    LEFT JOIN lieugestion l ON b.StandortID = l.StandortID
    ORDER BY pn.PrinterName, ps.SlotName
    """
    
    def __init__(self):
        super().__init__()

    def get_query(self):
        base = """
            SELECT {distinct}
                sc.CARIdoc,
                cd.BeschreibungFormular,
                pn.PrinterName,
                ps.SlotName,
                ps.Bemerkung AS SlotBemerkung,
                ps.PaperFormat,
                ps.TwoSided,
                ps.Autoprint,
                f.Fachabteilung
            FROM printernames pn
            LEFT JOIN printerslots ps ON pn.PrinterName = ps.PrinterName
            LEFT JOIN slot_caridocs sc
                ON ps.PrinterName = sc.PrinterName
                AND ps.SlotName = sc.SlotName
            LEFT JOIN caridocs cd ON sc.CARIdoc = cd.CARIdoc
            LEFT JOIN bureaus b ON sc.BureauID = b.BureauID
            LEFT JOIN fachabteilung f ON b.FachabteilungID = f.FachabteilungID
            LEFT JOIN lieugestion l ON b.StandortID = l.StandortID
        """

        if self.filtered_printer and self.filtered_slot:
            return base.format(distinct="DISTINCT") + f"""
            WHERE pn.PrinterName = '{self.filtered_printer}'
            AND ps.SlotName = '{self.filtered_slot}'
            ORDER BY ps.SlotName
            """
        elif self.filtered_printer:
            return base.format(distinct="DISTINCT") + f"""
            WHERE pn.PrinterName = '{self.filtered_printer}'
            ORDER BY ps.SlotName
            """
        elif self.filtered_bureau:
            return base.format(distinct="") + f"""
            WHERE b.BureauID = {self.filtered_bureau}
            ORDER BY pn.PrinterName, ps.SlotName
            """
        # otherwise return full query
        return self.query
    
    def set_filter(self, printer_name=None, slot_name=None, bureau_id=None):
        """Set the printer, slot, and bureau filters"""
        self.filtered_printer = printer_name
        self.filtered_slot = slot_name
        self.filtered_bureau = bureau_id
    
    def clear_filter(self):
        """Clear the printer filter"""
        self.filtered_printer = None
        self.filtered_slot = None
        self.filtered_bureau = None

    def on_view_shown(self, app, frame):
        """Called when view is shown - update columns if filtered"""
        if self.filtered_printer or self.filtered_bureau: 
            # change column headers to show filtered printer name
            self.columns = [
                "CARIdoc", "CARIDocument", "PrinterName", "SlotName", "SlotRemark", "PaperFormat",
                "TwoSided", "Autoprint",  "Department"
            ]
        
            # apply new columns
            app._configure_columns()

    
    def on_view_hidden(self, app):
        """Called when view is hidden - reset column headers"""
        # reset column headers
        self.columns = [
            "PrinterName", "PrinterModel", "SlotName", "PaperFormat",
            "TwoSided", "Autoprint", "SlotRemark", "CARIdoc", "CARIDocument",
            "Bureau", "BureauID", "Department", "Location",
            "BureauRemark"
        ]


    def delete(self, app, selected_rows):
        if not selected_rows:
            return

        if not messagebox.askyesno(
            "Delete",
            "Are you sure you want to delete the selected CARIdoc assignment(s)?"
        ):
            return

        try:
            col = {name: i for i, name in enumerate(self.columns)}

            with db.get_connection() as conn:
                cur = conn.cursor()
                deleted = 0

                for row in selected_rows:
                    printer_name = (row[col["PrinterName"]] if "PrinterName" in col else None) or app.last_selected_printer or self.filtered_printer
                    slot_name    = row[col["SlotName"]]
                    caridoc      = row[col["CARIdoc"]]
                    bureau_id    = (row[col["BureauID"]] if "BureauID" in col else None) or app.last_selected_bureau or self.filtered_bureau

                    missing_fields = []

                    if printer_name is None:
                        missing_fields.append("Printer")
                    if slot_name is None:
                        missing_fields.append("Slot")
                    if caridoc is None:
                        missing_fields.append("CARIdoc")
                    if bureau_id is None:
                        missing_fields.append("BureauID")

                    if missing_fields:
                        message = (
                            "One or more rows are missing required data and could not be deleted.\n\n"
                            "Missing fields:\n"
                            + "\n".join(f"  • {field}" for field in missing_fields)
                        )

                        messagebox.showwarning("Skipped", message)
                        return

                    cur.execute("""
                        DELETE FROM slot_caridocs
                        WHERE PrinterName = ?
                        AND SlotName = ?
                        AND CARIdoc = ?
                        AND BureauID = ?
                    """, (printer_name, slot_name, caridoc, bureau_id))
                    deleted += 1

            if deleted:
                app.refresh_view()
                messagebox.showinfo("Success", f"{deleted} assignment(s) deleted successfully.")

        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot delete assignment(s):\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")

        
