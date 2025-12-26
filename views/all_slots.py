from .base_view import BaseView
from tkinter import messagebox


class AllSlotsView(BaseView):
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

    def fetch(self, conn):
        """Liefert immer mindestens eine Zeile zurück, damit Treeview korrekt aufgebaut wird."""
        cur = conn.cursor()
        try:
            cur.execute(self.query)
            rows = cur.fetchall()
            # Mindestens eine leere Zeile zurückgeben, falls keine Daten
            if not rows:
                rows = [tuple("" for _ in self.columns)]
            return rows
        except Exception as e:
            print("Fehler beim Laden der Slots:", e)
            # Fallback: leere Zeile
            return [tuple("" for _ in self.columns)]

    def delete(self, app, row):
        messagebox.showwarning(
            "Delete",
            "Deletion for slot view must be handled per-table (not implemented)."
        )
