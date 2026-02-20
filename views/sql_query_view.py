from views.base_view import BaseView
from tkinter import ttk, messagebox
import tkinter as tk
import db


class SQLQueryView(BaseView):
    name = "sql_query"
    columns = []  # No treeview columns - we own the UI via dynamic_frame
    query = "SELECT 1"  # Dummy query so refresh_view doesn't crash

    def __init__(self):
        super().__init__()
        self._frame_built = False
        self._result_tree = None
        self._sql_input = None
        self._info_label = None

    # ------------------------------------------------------------------ #
    #  BaseView abstract method stubs                                      #
    # ------------------------------------------------------------------ #

    def delete(self, app, selected_rows):
        messagebox.showinfo("Info", "Use SQL commands to delete records.")

    def modify(self, app, selected_rows):
        messagebox.showinfo("Info", "Use SQL commands to modify records.")

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    def on_view_shown(self, app, frame):
        """Build the SQL tool UI inside dynamic_frame."""
        # Clear any previous contents
        for widget in frame.winfo_children():
            widget.destroy()
        self._frame_built = False

        self._build_ui(app, frame)
        self._frame_built = True

        # Pack the dynamic_frame so it's visible (app may have hidden it)
        frame.pack(fill="both", expand=True,
                   before=self._get_treeview_frame(app))

        # Hide the main treeview - we don't need it
        self._set_treeview_visible(app, False)

    def on_view_hidden(self, app):
        """Restore the main treeview when leaving this view."""
        self._set_treeview_visible(app, True)

    # ------------------------------------------------------------------ #
    #  UI construction                                                     #
    # ------------------------------------------------------------------ #

    def _build_ui(self, app, frame):
        frame.configure(relief="flat")

        # ── SQL input label ──
        tk.Label(frame, text="SQL Command:", anchor="w",
                 font=("Segoe UI", 9, "bold")).pack(fill="x", padx=6, pady=(6, 0))

        # ── Text box ──
        self._sql_input = tk.Text(frame, height=6,
                                  font=("Courier New", 10),
                                  relief="solid", borderwidth=1)
        self._sql_input.pack(fill="x", padx=6, pady=(2, 4))
        self._sql_input.bind("<Control-Return>", lambda e: self._run_query(app))

        # ── Button row ──
        btn_row = tk.Frame(frame)
        btn_row.pack(fill="x", padx=6, pady=(0, 4))

        tk.Button(btn_row, text="▶  Run  (Ctrl+Enter)",
                  bg="#4CAF50", fg="white", font=("Segoe UI", 9, "bold"),
                  command=lambda: self._run_query(app)).pack(side="left")
        tk.Button(btn_row, text="Clear Input",
                  command=self._clear_input).pack(side="left", padx=(6, 0))
        tk.Button(btn_row, text="Clear Results",
                  command=self._clear_results).pack(side="left", padx=(6, 0))

        # ── Quick-query buttons ──
        quick_frame = tk.LabelFrame(frame, text="Quick Queries", padx=4, pady=2)
        quick_frame.pack(fill="x", padx=6, pady=(0, 4))

        quick_queries = [
            ("Tables",        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"),
            ("Schema",        "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name;"),
            ("Printers",      "SELECT * FROM printernames LIMIT 50;"),
            ("Slots",         "SELECT * FROM printerslots LIMIT 50;"),
            ("Slot-CARIdocs", "SELECT * FROM slot_caridocs LIMIT 50;"),
        ]
        for label, sql in quick_queries:
            tk.Button(quick_frame, text=label, font=("Segoe UI", 8),
                      command=lambda s=sql: self._set_query(s)).pack(side="left", padx=2)

        # ── Results treeview ──
        results_frame = tk.Frame(frame, relief="solid", borderwidth=1)
        results_frame.pack(fill="both", expand=True, padx=6, pady=(0, 4))

        self._result_tree = ttk.Treeview(results_frame, show="headings",
                                         selectmode="extended")
        vsb = ttk.Scrollbar(results_frame, orient="vertical",
                             command=self._result_tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal",
                             command=self._result_tree.xview)
        self._result_tree.configure(yscrollcommand=vsb.set,
                                    xscrollcommand=hsb.set)
        self._result_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        results_frame.rowconfigure(0, weight=1)
        results_frame.columnconfigure(0, weight=1)

        # ── Info / status bar ──
        self._info_label = tk.Label(frame, text="", anchor="w",
                                    font=("Segoe UI", 8), fg="gray")
        self._info_label.pack(fill="x", padx=6, pady=(0, 4))

    # ------------------------------------------------------------------ #
    #  Query execution                                                     #
    # ------------------------------------------------------------------ #

    def _run_query(self, app):
        sql = self._sql_input.get("1.0", "end").strip()
        if not sql:
            return

        self._clear_results()

        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql)

                if cursor.description:                      # SELECT-like
                    cols = [d[0] for d in cursor.description]
                    rows = cursor.fetchall()

                    self._result_tree["columns"] = cols
                    for col in cols:
                        self._result_tree.heading(col, text=col, anchor="w")
                        self._result_tree.column(col, width=120,
                                                 minwidth=50, anchor="w",
                                                 stretch=True)
                    for i, row in enumerate(rows):
                        tag = "even" if i % 2 == 0 else "odd"
                        self._result_tree.insert("", "end",
                                                 values=row, tags=(tag,))

                    self._result_tree.tag_configure("even", background="white")
                    self._result_tree.tag_configure("odd",  background="#f2f2f2")

                    self._info_label.config(
                        text=f"✔  {len(rows)} row(s) returned.", fg="green")

                else:                                       # DML / DDL
                    conn.commit()
                    self._info_label.config(
                        text=f"✔  OK — {cursor.rowcount} row(s) affected.",
                        fg="green")
                    # Refresh the main app view if data may have changed
                    app.refresh_view()

        except Exception as e:
            self._info_label.config(text=f"✘  {e}", fg="red")

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _set_query(self, sql: str):
        self._sql_input.delete("1.0", "end")
        self._sql_input.insert("1.0", sql)

    def _clear_input(self):
        if self._sql_input:
            self._sql_input.delete("1.0", "end")

    def _clear_results(self):
        if self._result_tree:
            self._result_tree.delete(*self._result_tree.get_children())
            self._result_tree["columns"] = []
        if self._info_label:
            self._info_label.config(text="")

    def _get_treeview_frame(self, app):
        """Return the treeview's parent frame so we can pack before it."""
        return app.tree.master

    def _set_treeview_visible(self, app, visible: bool):
        treeview_frame = self._get_treeview_frame(app)
        if visible:
            treeview_frame.pack(fill="both", expand=True)
        else:
            treeview_frame.pack_forget()