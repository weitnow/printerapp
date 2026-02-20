from .base_view import BaseView
import sqlite3
from tkinter import messagebox, simpledialog
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
        elif self.filtered_printer and self.filtered_bureau:
            return base.format(distinct="") + f"""
            WHERE pn.PrinterName = '{self.filtered_printer}'
            AND b.BureauID = {self.filtered_bureau}
            ORDER BY pn.PrinterName, ps.SlotName
            """
        elif self.filtered_printer: #check this
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
        self.filtered_bureau = bureau_id
        self.filtered_slot = slot_name
    
    def clear_filter(self):
        """Clear the printer filter"""
        self.filtered_printer = None
        self.filtered_slot = None
        self.filtered_bureau = None


    def modify(self, app, selected_rows):
        if not selected_rows:
            return
        if len(selected_rows) > 1:
            messagebox.showwarning("Warning", "Please select only one assignment to modify.")
            return

        col = {name: i for i, name in enumerate(self.columns)}
        row = selected_rows[0]

        printer_name = (row[col["PrinterName"]] if "PrinterName" in col else None) or app.last_selected_printer or self.filtered_printer
        slot_name = row[col["SlotName"]] if "SlotName" in col else None
        caridoc = row[col["CARIdoc"]] if "CARIdoc" in col else None
        bureau_id = (row[col["BureauID"]] if "BureauID" in col else None) or self.filtered_bureau

        if not all([printer_name, slot_name, caridoc, bureau_id]):
            messagebox.showwarning(
                "Modify not possible",
                "This assignment cannot be uniquely identified. Please navigate from a printer and bureau, then try again.",
            )
            return

        current_slot_remark = row[col["SlotRemark"]] if "SlotRemark" in col else ""
        current_bureau_remark = row[col["BureauRemark"]] if "BureauRemark" in col else ""

        new_slot_remark = simpledialog.askstring(
            "Modify Slot Remark",
            f"Printer: {printer_name}\nSlot: {slot_name}\nCARIdoc: {caridoc}\n\nEnter new slot remark:",
            initialvalue=current_slot_remark or "",
        )
        if new_slot_remark is None:
            return

        new_bureau_remark = current_bureau_remark
        if "BureauRemark" in col:
            new_bureau_remark = simpledialog.askstring(
                "Modify Bureau Remark",
                f"BureauID: {bureau_id}\n\nEnter new bureau remark:",
                initialvalue=current_bureau_remark or "",
            )
            if new_bureau_remark is None:
                new_bureau_remark = current_bureau_remark

        try:
            with db.get_connection() as conn:
                cur = conn.cursor()

                cur.execute(
                    """
                    UPDATE printerslots
                    SET Bemerkung = ?
                    WHERE PrinterName = ?
                      AND SlotName = ?
                    """,
                    (new_slot_remark, printer_name, slot_name),
                )

                cur.execute(
                    """
                    UPDATE slot_caridocs
                    SET Bemerkung = ?
                    WHERE PrinterName = ?
                      AND SlotName = ?
                      AND CARIdoc = ?
                      AND BureauID = ?
                    """,
                    (new_bureau_remark, printer_name, slot_name, caridoc, bureau_id),
                )

            app.refresh_view()
            messagebox.showinfo("Success", "Remarks updated successfully.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Cannot update remarks:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")

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
                    bureau_id    = (row[col["BureauID"]] if "BureauID" in col else None) or self.filtered_bureau

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

                        if "BureauID" in missing_fields:
                            message += "\n\nGo back to printers, select a Bureau, then a CARIdoc."

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


        
