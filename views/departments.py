from .base_view import BaseView
import sqlite3
from tkinter import messagebox, Button
import db  # Import the db module

class DepartmentView(BaseView):
    name = "departments"
    columns = ["BureauID", "Bureau", "Printers*", "CARIdocs*", "Fachabteilung", "Standort"]
    columns_actions = {}
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


    



    def delete(self, app, selected_rows):
        pass
       
