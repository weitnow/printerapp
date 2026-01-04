from .base_view import BaseView
import sqlite3
from tkinter import messagebox
import db  # Import the db module


class SlotCariDoc(BaseView):
    name = "all_slots"
    columns = [
        "PrinterName", "PrinterModel", "SlotName", "PaperFormat",
        "TwoSided", "Autoprint", "SlotBemerkung", "CARIdoc",
        "Bureau", "BureauID", "Fachabteilung", "Standort",
        "BureauBemerkung"
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
    LEFT JOIN bureaus b ON sc.BureauID = b.BureauID
    LEFT JOIN fachabteilung f ON b.FachabteilungID = f.FachabteilungID
    LEFT JOIN lieugestion l ON b.StandortID = l.StandortID
    ORDER BY pn.PrinterName, ps.SlotName
    """
    
    def __init__(self):
        super().__init__()
        self.filtered_printer = None

    def get_query(self):
        """Return query, optionally filtered by printer name"""
        if self.filtered_printer:
            return f"""
            SELECT
                sc.CARIdoc,
                ps.SlotName,
                ps.PaperFormat,
                ps.TwoSided,
                ps.Autoprint,
                ps.Bemerkung AS SlotBemerkung,
                f.Fachabteilung
            FROM printernames pn
            LEFT JOIN printerslots ps ON pn.PrinterName = ps.PrinterName
            LEFT JOIN slot_caridocs sc
                ON ps.PrinterName = sc.PrinterName
                AND ps.SlotName = sc.SlotName
            LEFT JOIN bureaus b ON sc.BureauID = b.BureauID
            LEFT JOIN fachabteilung f ON b.FachabteilungID = f.FachabteilungID
            LEFT JOIN lieugestion l ON b.StandortID = l.StandortID
            WHERE pn.PrinterName = '{self.filtered_printer}'
            ORDER BY ps.SlotName                  
            """
        return self.query
    
    def set_filter(self, printer_name):
        """Set the printer filter"""
        self.filtered_printer = printer_name
    
    def clear_filter(self):
        """Clear the printer filter"""
        self.filtered_printer = None

    def on_view_shown(self, app, frame):
        """Called when view is shown - update columns if filtered"""
        if self.filtered_printer:
            # change column headers to show filtered printer name
            self.columns = [
                "CARIdoc", "SlotName", "PaperFormat",
                "TwoSided", "Autoprint", "SlotBemerkung", "Fachabteilung"
            ]
            # apply new columns
            app._configure_columns()

    
    def on_view_hidden(self, app):
        """Called when view is hidden - reset column headers"""
        # reset column headers
        self.columns = [
            "PrinterName", "PrinterModel", "SlotName", "PaperFormat",
            "TwoSided", "Autoprint", "SlotBemerkung", "CARIdoc",
            "Bureau", "BureauID", "Fachabteilung", "Standort",
            "BureauBemerkung"
        ]


    def delete(self, app, row):
        messagebox.showwarning(
            "Delete",
            "Deletion for slot view must be handled per-table (not implemented)."
        )
