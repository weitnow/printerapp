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


    @abstractmethod
    def delete(self, app, row):
        """Delete method must be implemented by each view"""
        pass

    def get_query(self):
        """Override this method if you need dynamic queries"""
        return self.query
    
    def on_double_click(self, app, row, col):
        """Override this method to handle double-click events"""
        pass

    def on_view_shown(self, app, frame):
        """Called when view is shown - override for custom behavior"""
        pass
    
    def on_view_hidden(self, app):
        """Called when view is hidden - override for cleanup"""
        pass