from tkinter import ttk, messagebox
from abc import ABC, abstractmethod



# =====================
# Base View Definition
# =====================
class BaseView(ABC):
    name: str = ""
    columns: list[str] = []
    query: str = ""


    def fetch(self, conn):
        cur = conn.cursor()
        cur.execute(self.query) # query ausführen
        return cur.fetchall() #


    def configure(self, app, row):
        messagebox.showinfo(
        "Configure",
        "\n".join(f"{c}: {v}" for c, v in zip(self.columns, row))
        )


    @abstractmethod
    def delete(self, app, row):
        pass