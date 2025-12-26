from .base_view import BaseView
import sqlite3
from tkinter import messagebox
import db  # Import the db module

class SlotPrinter(BaseView):
    name = "printer slots"
    columns = ["PrinterName", "SlotName", "PaperFormat", "TwoSided", "Autoprint", "Bemerkung"]
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

    def delete(self, app, row):
        pass