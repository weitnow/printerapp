from .base_view import BaseView
import sqlite3
from tkinter import messagebox, Button
import db  # Import the db module

class DepartmentView(BaseView):
    name = "departments"
    columns = ["FachabteilungID", "Fachabteilung"]
    columns_actions = {}
    query = """
    SELECT
    FachabteilungID,
    Fachabteilung
    FROM fachabteilung

    ORDER BY FachabteilungID
    """


    



    def delete(self, app, selected_rows):
        pass
       
