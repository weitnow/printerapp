from views.base_view import BaseView
from tkinter import ttk, messagebox, simpledialog
import tkinter as tk
import db
import json
import os


SAVED_QUERIES_FILE = "saved_queries.json"


class SQLQueryView(BaseView):
    name = "sql_query"
    columns = []
    query = "SELECT 1"

    def __init__(self):
        super().__init__()
        self._frame_built = False
        self._result_tree = None
        self._sql_input = None
        self._info_label = None
        self._saved_queries_listbox = None
        self._saved_queries: dict[str, str] = self._load_queries_from_file()

    # ------------------------------------------------------------------ #
    #  BaseView abstract method stubs                                      #
    # ------------------------------------------------------------------ #

    def add(self, app):
        messagebox.showinfo("Info", "Use SQL commands to add records.")

    def delete(self, app, selected_rows):
        messagebox.showinfo("Info", "Use SQL commands to delete records.")

    def modify(self, app, selected_rows):
        messagebox.showinfo("Info", "Use SQL commands to modify records.")

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    def on_view_shown(self, app, frame):
        for widget in frame.winfo_children():
            widget.destroy()
        self._frame_built = False

        self._build_ui(app, frame)
        self._frame_built = True

        frame.pack(fill="both", expand=True,
                   before=self._get_treeview_frame(app))
        self._set_treeview_visible(app, False)

    def on_view_hidden(self, app):
        self._set_treeview_visible(app, True)

    # ------------------------------------------------------------------ #
    #  UI construction                                                     #
    # ------------------------------------------------------------------ #

    def _build_ui(self, app, frame):
        frame.configure(relief="flat")

        # ── Outer paned layout: left = saved queries, right = editor+results ──
        paned = tk.PanedWindow(frame, orient="horizontal", sashrelief="raised",
                               sashwidth=5)
        paned.pack(fill="both", expand=True, padx=6, pady=6)

        # ── LEFT PANEL: Saved queries ──
        left = tk.Frame(paned, width=200)
        paned.add(left, minsize=150)

        tk.Label(left, text="Saved Queries", font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill="x", pady=(4, 2))

        list_frame = tk.Frame(left)
        list_frame.pack(fill="both", expand=True)

        sb = ttk.Scrollbar(list_frame, orient="vertical")
        sb.pack(side="right", fill="y")

        self._saved_queries_listbox = tk.Listbox(
            list_frame, yscrollcommand=sb.set,
            selectmode="single", activestyle="dotbox",
            font=("Segoe UI", 9)
        )
        self._saved_queries_listbox.pack(side="left", fill="both", expand=True)
        sb.config(command=self._saved_queries_listbox.yview)

        # Double-click loads query into editor
        self._saved_queries_listbox.bind("<Double-1>",
                                         lambda e: self._load_selected_query())

        btn_row = tk.Frame(left)
        btn_row.pack(fill="x", pady=(4, 0))

        tk.Button(btn_row, text="Load",   width=6,
                  command=self._load_selected_query).pack(side="left")
        tk.Button(btn_row, text="Rename", width=6,
                  command=self._rename_selected_query).pack(side="left", padx=2)
        tk.Button(btn_row, text="Delete", width=6, fg="red",
                  command=self._delete_selected_query).pack(side="left")

        self._refresh_query_list()

        # ── RIGHT PANEL: Editor + Results ──
        right = tk.Frame(paned)
        paned.add(right, minsize=400)

        # ── SQL input label + Save button ──
        header = tk.Frame(right)
        header.pack(fill="x", pady=(4, 0))

        tk.Label(header, text="SQL Command:",
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Button(header, text="💾  Save Query",
                  font=("Segoe UI", 8),
                  command=self._save_current_query).pack(side="right")

        # ── Text box ──
        self._sql_input = tk.Text(right, height=7,
                                  font=("Courier New", 10),
                                  relief="solid", borderwidth=1)
        self._sql_input.pack(fill="x", pady=(2, 4))
        self._sql_input.bind("<Control-Return>", lambda e: self._run_query(app))

        # ── Button row ──
        btn_row2 = tk.Frame(right)
        btn_row2.pack(fill="x", pady=(0, 4))

        tk.Button(btn_row2, text="▶  Run  (Ctrl+Enter)",
                  bg="#4CAF50", fg="white", font=("Segoe UI", 9, "bold"),
                  command=lambda: self._run_query(app)).pack(side="left")
        tk.Button(btn_row2, text="Clear Input",
                  command=self._clear_input).pack(side="left", padx=(6, 0))
        tk.Button(btn_row2, text="Clear Results",
                  command=self._clear_results).pack(side="left", padx=(6, 0))

        # ── Quick-query buttons ──
        quick_frame = tk.LabelFrame(right, text="Quick Queries", padx=4, pady=2)
        quick_frame.pack(fill="x", pady=(0, 4))

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
        results_frame = tk.Frame(right, relief="solid", borderwidth=1)
        results_frame.pack(fill="both", expand=True, pady=(0, 4))

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
        self._info_label = tk.Label(right, text="", anchor="w",
                                    font=("Segoe UI", 8), fg="gray")
        self._info_label.pack(fill="x", pady=(0, 2))

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

                if cursor.description:
                    cols = [d[0] for d in cursor.description]
                    rows = cursor.fetchall()

                    self._result_tree["columns"] = cols
                    for col in cols:
                        self._result_tree.heading(col, text=col, anchor="w")
                        self._result_tree.column(col, width=120, minwidth=50,
                                                 anchor="w", stretch=True)
                    for i, row in enumerate(rows):
                        tag = "even" if i % 2 == 0 else "odd"
                        self._result_tree.insert("", "end", values=row, tags=(tag,))

                    self._result_tree.tag_configure("even", background="white")
                    self._result_tree.tag_configure("odd",  background="#f2f2f2")
                    self._info_label.config(
                        text=f"✔  {len(rows)} row(s) returned.", fg="green")
                else:
                    conn.commit()
                    self._info_label.config(
                        text=f"✔  OK — {cursor.rowcount} row(s) affected.", fg="green")
                    app.refresh_view()

        except Exception as e:
            self._info_label.config(text=f"✘  {e}", fg="red")

    # ------------------------------------------------------------------ #
    #  Save / Load                                                         #
    # ------------------------------------------------------------------ #

    def _save_current_query(self):
        sql = self._sql_input.get("1.0", "end").strip()
        if not sql:
            messagebox.showwarning("Empty Query", "Nothing to save.")
            return

        # Check if a query is selected - offer to overwrite it
        selected = self._saved_queries_listbox.curselection()
        initial_name = ""
        if selected:
            initial_name = self._saved_queries_listbox.get(selected[0])

        name = simpledialog.askstring(
            "Save Query",
            "Enter a name for this query:",
            initialvalue=initial_name
        )
        if not name:
            return

        name = name.strip()
        if not name:
            return

        if name in self._saved_queries:
            if not messagebox.askyesno("Overwrite?",
                                       f"'{name}' already exists. Overwrite?"):
                return

        self._saved_queries[name] = sql
        self._persist_queries()
        self._refresh_query_list()

        # Select the just-saved entry
        items = list(self._saved_queries.keys())
        if name in items:
            idx = items.index(name)
            self._saved_queries_listbox.selection_clear(0, "end")
            self._saved_queries_listbox.selection_set(idx)
            self._saved_queries_listbox.see(idx)

        self._info_label.config(text=f"✔  Query saved as '{name}'.", fg="green")

    def _load_selected_query(self):
        selected = self._saved_queries_listbox.curselection()
        if not selected:
            return
        name = self._saved_queries_listbox.get(selected[0])
        sql = self._saved_queries.get(name, "")
        self._set_query(sql)
        self._info_label.config(text=f"✔  Loaded '{name}'.", fg="gray")

    def _rename_selected_query(self):
        selected = self._saved_queries_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a query to rename.")
            return

        old_name = self._saved_queries_listbox.get(selected[0])
        new_name = simpledialog.askstring(
            "Rename Query", "New name:", initialvalue=old_name
        )
        if not new_name or new_name.strip() == old_name:
            return

        new_name = new_name.strip()
        if new_name in self._saved_queries:
            messagebox.showwarning("Name taken",
                                   f"A query named '{new_name}' already exists.")
            return

        # Preserve insertion order
        self._saved_queries = {
            (new_name if k == old_name else k): v
            for k, v in self._saved_queries.items()
        }
        self._persist_queries()
        self._refresh_query_list()

    def _delete_selected_query(self):
        selected = self._saved_queries_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a query to delete.")
            return

        name = self._saved_queries_listbox.get(selected[0])
        if not messagebox.askyesno("Delete Query",
                                   f"Delete saved query '{name}'?"):
            return

        del self._saved_queries[name]
        self._persist_queries()
        self._refresh_query_list()

    # ------------------------------------------------------------------ #
    #  Persistence                                                         #
    # ------------------------------------------------------------------ #

    def _load_queries_from_file(self) -> dict:
        if os.path.exists(SAVED_QUERIES_FILE):
            try:
                with open(SAVED_QUERIES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _persist_queries(self):
        try:
            with open(SAVED_QUERIES_FILE, "w", encoding="utf-8") as f:
                json.dump(self._saved_queries, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Save Error",
                                 f"Could not save queries to file:\n{e}")

    def _refresh_query_list(self):
        if not self._saved_queries_listbox:
            return
        self._saved_queries_listbox.delete(0, "end")
        for name in self._saved_queries:
            self._saved_queries_listbox.insert("end", name)

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
        return app.tree.master

    def _set_treeview_visible(self, app, visible: bool):
        treeview_frame = self._get_treeview_frame(app)
        if visible:
            treeview_frame.pack(fill="both", expand=True)
        else:
            treeview_frame.pack_forget()