from tkinter import ttk, messagebox
from abc import ABC, abstractmethod


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
        self.filtered_bureau = None
        self.filtered_slot = None
        self.back_button = None

    def fetch(self, conn):
        """Fetch data using the provided connection"""
        cur = conn.cursor()
        cur.execute(self.query) # query ausführen
        return cur.fetchall() #


    def show_details(self, app, row):
        """Default configure implementation - can be overridden"""
        messagebox.showinfo(
        "Details",
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
        app.switch_view("printer_slots", filter_printer=printer_name, last_selected_printer=printer_name)

    #used in printers.py
    def show_caridocs(self, app, row_value, col):
        """Switch to caridoc view filtered by printer name"""
        printer_name = row_value[0]  # PrinterName is the first column
        app.switch_view("slot_cari_docs", filter_printer=printer_name, last_selected_printer=printer_name
        )

    #used in printers.py
    def show_bureaus(self, app, row_value, col):
        """Switch to caridoc bureaus view filtered by printer name"""
        printer_name = row_value[0]  # PrinterName is the first column
        app.switch_view("bureaus", filter_printer=printer_name, last_selected_printer=printer_name
        )
    #used in printers.py
    def show_printer_caridocs_bureaus(self, app, row_value, col):
        """Switch to caridoc view filtered by printer name"""
        printer_name = row_value[0]  # PrinterName is the first column
        app.switch_view("slot_cari_docs", filter_printer=printer_name, last_selected_printer=printer_name)

    #used in bureaus.py
    def show_caridocs_from_bureaus(self, app, row_value, col):
        # if there is a set printer name filter, use it
        bureau_id = row_value[0]  # BureauID is the first column
        if self.filtered_printer:                                
            app.switch_view("slot_cari_docs", filter_printer=self.filtered_printer, filter_bureau=bureau_id, last_selected_bureau=bureau_id)
        else:
            app.switch_view("slot_cari_docs", filter_bureau=bureau_id, last_selected_bureau=bureau_id)

    #used in bureaus.py
    def show_printers_from_bureaus(self, app, row_value, col):
        """Switch to printer view filtered by bureau id"""
        bureau_id = row_value[0]  # BureauID is the first column
        app.switch_view("printers", filter_bureau=bureau_id, last_selected_bureau=bureau_id)

    #used in slot_printer.py
    def show_caridocs_of_slot(self, app, row_value, col): 
        """Switch to caridoc view filtered by printer name and slot name"""
        printer_name = row_value[0]  # PrinterName is the first column
        slot_name = row_value[1]     # SlotName is the second column
        app.switch_view("slot_cari_docs", filter_printer=printer_name, filter_slot=slot_name)

    
    ### --- --- --- --- --- --- --- --- --- ###


    @abstractmethod
    def delete(self, app, selected_rows):
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


