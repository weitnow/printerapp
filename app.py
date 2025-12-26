import tkinter as tk
from tkinter import ttk
import db
from views.printers import PrintersView
from views.bureaus import BureausView
from views.slot_cari_docs import SlotCariDoc
from views.slot_printer import SlotPrinter


class PrinterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Printer Database")
        self.root.geometry("1500x700")
        
        self.current_rows = []
        self.sort_reverse = False
        
        self._setup_ui()
        self._setup_views()
        self.set_view("printers")

    def _setup_ui(self):
        """UI-Komponenten erstellen"""
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Container for dynamic content (like back button)
        self.dynamic_frame = tk.Frame(main_frame)
        self.dynamic_frame.pack(fill="x")
        
        self._create_filter_bar(main_frame)
        self._create_treeview(main_frame)
        self._create_context_menu()
        self._create_menubar()

    def _create_filter_bar(self, parent):
        """Filter-Leiste erstellen"""
        frame = tk.Frame(parent)
        frame.pack(fill="x")
        
        tk.Label(frame, text="Filter:").pack(side="left")
        
        self.filter_entry = tk.Entry(frame)
        self.filter_entry.pack(side="left", padx=(5, 10), fill="x", expand=True)
        self.filter_entry.bind("<KeyRelease>", self._apply_filter)
        
        self.filter_column = tk.StringVar()
        self.filter_dropdown = ttk.Combobox(frame, textvariable=self.filter_column, state="readonly")
        self.filter_dropdown.pack(side="left")
        self.filter_dropdown.bind("<<ComboboxSelected>>", self._apply_filter)
        
        # Zähler für angezeigte Zeilen
        self.count_label = tk.Label(frame, text="Total: 0")
        self.count_label.pack(side="left", padx=(10, 0))

    def _create_treeview(self, parent):
        """Treeview mit Scrollbars erstellen"""
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True)
        
        # Scrollbars zuerst erstellen
        v_scroll = ttk.Scrollbar(frame, orient="vertical")
        v_scroll.pack(side="right", fill="y")
        
        h_scroll = ttk.Scrollbar(frame, orient="horizontal")
        h_scroll.pack(side="bottom", fill="x")
        
        # Treeview mit Scrollbars verknüpfen
        self.tree = ttk.Treeview(frame, show="headings", 
                                 yscrollcommand=v_scroll.set,
                                 xscrollcommand=h_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        
        v_scroll.config(command=self.tree.yview)
        h_scroll.config(command=self.tree.xview)
        
        # Event bindings for double-click
        self.tree.bind("<Double-Button-1>", self._on_double_click)

    def _create_context_menu(self):
        """Rechtsklick-Menü erstellen"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Configure", command=self._configure_row)
        self.context_menu.add_command(label="Delete", command=self._delete_row)
        self.tree.bind("<Button-3>", self._show_context_menu)

    def _create_menubar(self):
        """Menüleiste erstellen"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Printer Slots", command=lambda: self.switch_view("printer slots"))
        view_menu.add_command(label="Cari Doc Slots", command=lambda: self.switch_view("slot_cari_docs"))
        view_menu.add_command(label="Printers", command=lambda: self.switch_view("printers"))
        view_menu.add_command(label="Bureaus", command=lambda: self.switch_view("bureaus"))

    def _setup_views(self):
        """Verfügbare Views initialisieren"""
        self.views = {
            "printers": PrintersView(),
            "bureaus": BureausView(),
            "printer slots": SlotPrinter(),
            "slot_cari_docs": SlotCariDoc(),
        }
        self.current_view = None

    def set_view(self, name):
        """View wechseln und Daten laden (legacy method)"""
        self.switch_view(name)

    def switch_view(self, view_name, **kwargs):
        """Switch to a different view with optional parameters"""
        # Check if view exists
        if view_name not in self.views:
            print(f"Warning: View '{view_name}' not found")
            return
        
        # Call on_view_hidden for current view
        if self.current_view and hasattr(self.current_view, 'on_view_hidden'):
            self.current_view.on_view_hidden(self)
        
        # Get the target view
        target_view = self.views[view_name]
        
        # Handle filter parameter for printer slots
        if 'filter_printer' in kwargs and hasattr(target_view, 'set_filter'):
            target_view.set_filter(kwargs['filter_printer'])
        elif hasattr(target_view, 'clear_filter'):
            # Clear filter if switching without filter parameter
            target_view.clear_filter()
        
        # Switch to the view
        self.current_view = target_view
        self.filter_entry.delete(0, tk.END)
        
        # Filter-Dropdown aktualisieren
        columns = self.current_view.columns
        self.filter_dropdown["values"] = columns
        if columns:
            self.filter_column.set(columns[0])
        
        self.refresh_view()
        
        # Call on_view_shown for new view
        if hasattr(self.current_view, 'on_view_shown'):
            self.current_view.on_view_shown(self, self.dynamic_frame)

    def refresh_view(self):
        """Daten neu laden und Treeview aktualisieren"""
        with db.get_connection() as conn:
            # Use get_query if available (for filtered views)
            if hasattr(self.current_view, 'get_query'):
                query = self.current_view.get_query()
                cursor = conn.cursor()
                cursor.execute(query)
                self.current_rows = cursor.fetchall()
            else:
                self.current_rows = self.current_view.fetch(conn)
        
        self._configure_columns()
        self._populate_tree(self.current_rows)

    def _configure_columns(self):
        """Treeview-Spalten konfigurieren"""
        columns = self.current_view.columns
        self.tree["columns"] = columns
        
        for col in columns:
            self.tree.heading(col, text=col, anchor="w", 
                            command=lambda c=col: self._sort_by_column(c))
            self.tree.column(col, anchor="w", width=120, minwidth=50, stretch=True)

    def _populate_tree(self, rows):
        """Treeview mit Daten füllen (Zebra-Styling)"""
        self.tree.delete(*self.tree.get_children())
        
        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", values=row, tags=(tag,))
        
        self.tree.tag_configure("even", background="white")
        self.tree.tag_configure("odd", background="#f2f2f2")
        
        # Zähler aktualisieren
        self.count_label.config(text=f"Total: {len(rows)}")

    def _sort_by_column(self, column):
        """Nach Spalte sortieren"""
        idx = self.current_view.columns.index(column)
        self.current_rows.sort(key=lambda row: row[idx], reverse=self.sort_reverse)
        self.sort_reverse = not self.sort_reverse
        self._apply_filter()

    def _apply_filter(self, event=None):
        """Filter anwenden"""
        filter_text = self.filter_entry.get().lower()
        column = self.filter_column.get()
        
        if not filter_text or column not in self.current_view.columns:
            self._populate_tree(self.current_rows)
            return
        
        idx = self.current_view.columns.index(column)
        filtered = [row for row in self.current_rows 
                   if filter_text in str(row[idx]).lower()]
        self._populate_tree(filtered)

    def _on_double_click(self, event):
        """Handle double-click on tree item"""
        selection = self.tree.selection()
        if selection and self.current_view:
            item = selection[0]
            row = self.tree.item(item, "values")
            # Call the view's on_double_click handler if it exists
            if hasattr(self.current_view, 'on_double_click'):
                self.current_view.on_double_click(self, row)

    def _show_context_menu(self, event):
        """Kontextmenü anzeigen"""
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            
            # Check if view has custom right-click handler
            if hasattr(self.current_view, 'on_right_click'):
                row = self.tree.item(row_id, "values")
                self.current_view.on_right_click(self, row, event)
            else:
                # Show default context menu
                self.context_menu.post(event.x_root, event.y_root)

    def _configure_row(self):
        """Zeile konfigurieren"""
        if self.tree.selection() and self.current_view:
            row = self.tree.item(self.tree.selection()[0], "values")
            self.current_view.configure(self, row)

    def _delete_row(self):
        """Zeile löschen"""
        if self.tree.selection() and self.current_view:
            row = self.tree.item(self.tree.selection()[0], "values")
            self.current_view.delete(self, row)