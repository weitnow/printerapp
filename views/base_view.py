from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
import db # Import the db module


# =====================
# Base View Definition
# =====================
class BaseView(ABC):
    name: str = ""
    columns: list[str] = []
    query: str = ""

    def __init__(self):
        super().__init__()
        self.filtered_printer = None
        self.back_button = None

    def fetch(self, conn):
        """Fetch data using the provided connection"""
        cur = conn.cursor()
        cur.execute(self.query) # query ausführen
        return cur.fetchall() #


    def configure(self, app, row):
        """Default configure implementation - can be overridden"""
        messagebox.showinfo(
        "Configure",
        "\n".join(f"{c}: {v}" for c, v in zip(self.columns, row))
        )

    def on_double_click(self, app, row_value, col):
        """
        Generic double-click handler:
        - row: tuple of row values
        - col: Treeview column id (#1, #2, ...)
        """

        # check is there is a attribute columns_actions
        if not hasattr(self, 'columns_actions'):
            print("No columns_actions for this view defined.")
            return

        action_name = self.columns_actions.get(col)
        if not action_name:
            print(f"No action defined for column {col}.")
            return  # No action defined for this column
        
        handler = getattr(self, action_name, None)
        if callable(handler):
            handler(app, row_value, col)

    ### --- methodes to switch views --- ###

    #used in printers.py
    def show_printer_slots(self, app, row_value, col):
        """Switch to printer slots view filtered by printer name"""
        printer_name = row_value[0]  # PrinterName is the first column
        app.switch_view("printer slots", filter_printer=printer_name)

    #used in printers.py
    def show_caridocs(self, app, row_value, col):
        """Switch to caridoc view filtered by printer name"""
        printer_name = row_value[0]  # PrinterName is the first column
        app.switch_view("slot_cari_docs", filter_printer=printer_name
        )

    #used in printers.py#
    def show_bureaus(self, app, row_value, col):
        """Switch to caridoc bureaus view filtered by printer name"""
        printer_name = row_value[0]  # PrinterName is the first column
        app.switch_view("bureaus", filter_printer=printer_name
        )

    #used in slot_printer.py
    def show_caridocs_of_slot(self, app, row_value, col): 
        """Switch to caridoc view filtered by printer name and slot name"""
        printer_name = row_value[0]  # PrinterName is the first column
        slot_name = row_value[1]     # SlotName is the second column
        app.switch_view("slot_cari_docs", filter_printer=printer_name, filter_slot=slot_name)

    ### --- --- --- --- --- --- --- --- --- ###


    @abstractmethod
    def delete(self, app, row):
        """Delete method must be implemented by each view"""
        pass

    def get_query(self):
        """Override this method if you need dynamic queries"""
        return self.query

    def on_view_shown(self, app, frame):
        """Called when view is shown - override for custom behavior"""
        pass
    
    def on_view_hidden(self, app):
        """Called when view is hidden - override for cleanup"""
        pass