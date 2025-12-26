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