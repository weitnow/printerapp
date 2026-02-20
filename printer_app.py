import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import db
from views.printers import PrintersView
from views.bureaus import BureausView
from views.slot_cari_docs import SlotCariDoc
from views.slot_printer import SlotPrinter
from views.departments import DepartmentView    
from views.printer_models import PrinterModels
from views.lieugestion import LieugestionView
from views.printinserts import PrintInsertView
from views.caridocs import CaridocView
import threading
from typing import List, Tuple, Dict, Any, Optional
from functools import partial
from textwrap import dedent

from views.sql_query_view import SQLQueryView


class PrinterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Printer Database")
        self.root.geometry("1500x700")
        
        self.current_rows: List[Tuple] = []
        self.sort_reverse: bool = False
        self.navigation_history: List[Dict[str, Any]] = []
        self.back_button: Optional[tk.Button] = None
        self.current_view = ""
        
        self.last_selected_printer = None
        self.last_selected_bureau = None

        self._setup_ui()
        self._setup_views()
        self.switch_view("printers")

    def _setup_ui(self) -> None:
        """Create UI components"""
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Store main_frame reference for repacking dynamic_frame later
        self.main_frame = main_frame
        
        self.dynamic_frame = tk.Frame(main_frame)
        # Don't pack it initially - will be packed when needed
        
        self._create_filter_bar(main_frame)
        self._create_treeview(main_frame)
        self._create_context_menu()
        self._create_menubar()

    def _create_filter_bar(self, parent: tk.Frame) -> None:
        """Create filter bar with search and dropdown"""
        frame = tk.Frame(parent)
        frame.pack(fill="x")
        
        tk.Label(frame, text="Filter:").pack(side="left")
        
        self.filter_entry = tk.Entry(frame)
        self.filter_entry.pack(side="left", padx=(5, 10), fill="x", expand=True)
        self.filter_entry.bind("<KeyRelease>", self._apply_filter)
        
        self.filter_column = tk.StringVar()
        self.filter_dropdown = ttk.Combobox(
            frame, 
            textvariable=self.filter_column, 
            state="readonly"
        )
        self.filter_dropdown.pack(side="left")
        self.filter_dropdown.bind("<<ComboboxSelected>>", self._apply_filter)
        
        self.count_label = tk.Label(frame, text="Total: 0")
        self.count_label.pack(side="left", padx=(10, 0))

    def _create_treeview(self, parent: tk.Frame) -> None:
        """Create treeview with scrollbars"""
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True)
        
        v_scroll = ttk.Scrollbar(frame, orient="vertical")
        v_scroll.pack(side="right", fill="y")
        
        h_scroll = ttk.Scrollbar(frame, orient="horizontal")
        h_scroll.pack(side="bottom", fill="x")
        
        self.tree = ttk.Treeview(
            frame, 
            show="headings",
            selectmode="extended",
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )
        self.tree.pack(side="left", fill="both", expand=True)
        
        v_scroll.config(command=self.tree.yview)
        h_scroll.config(command=self.tree.xview)
        
        self.tree.bind("<Double-1>", self._on_double_click)

    def _create_context_menu(self) -> None:
        """Create right-click context menu"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.tree.bind("<Button-3>", self._show_context_menu)

    def _create_menubar(self) -> None:
        """Create application menubar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(
            label="Printers", 
            command=partial(self.switch_view, "printers", clear_history=True)
        )
        view_menu.add_command(
            label="Bureaus", 
            command=partial(self.switch_view, "bureaus", clear_history=True)
        )
        view_menu.add_command(
            label="Cari Doc Slots", 
            command=partial(self.switch_view, "slot_cari_docs", clear_history=True)
        )
        view_menu.add_command(
            label="Departments",
            command=partial(self.switch_view, "departments", clear_history=True)
        )
        view_menu.add_command(
            label="Printermodels",
            command=partial(self.switch_view, "printer_models", clear_history=True)
        )
        view_menu.add_command(
            label="Lieugestion",
            command=partial(self.switch_view, "lieugestion", clear_history=True)
        )
        view_menu.add_command(
            label="Printinserts",
            command=partial(self.switch_view, "printinserts", clear_history=True)
        )
        view_menu.add_command(
            label="Caridocs",
            command=partial(self.switch_view, "caridocs", clear_history=True)
        )
        view_menu.add_command(
            label="SQL Query",
            command=partial(self.switch_view, "sql_query", clear_history=True)
        )
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import XLSX", command=self._import_xlsx)
        file_menu.add_command(label="Export XLSX", command=self._export_xlsx)

    def _setup_views(self) -> None:
        """Initialize available views"""
        self.views = {
            "printers": PrintersView(),
            "bureaus": BureausView(),
            "printer_slots": SlotPrinter(),
            "slot_cari_docs": SlotCariDoc(),
            "departments": DepartmentView(),
            "printer_models": PrinterModels(),
            "lieugestion": LieugestionView(),
            "printinserts": PrintInsertView(),
            "caridocs": CaridocView(),
            "sql_query": SQLQueryView()
        }

    def switch_view(
        self, 
        view_name: str, 
        add_to_history: bool = True, 
        clear_history: bool = False,
        last_selected_printer: Optional[str] = None,
        last_selected_bureau: Optional[str] = None,
        **kwargs
    ) -> None:

        if last_selected_printer is not None:
            self.last_selected_printer = last_selected_printer

        if last_selected_bureau is not None:
            self.last_selected_bureau = last_selected_bureau


        """Switch to a different view with optional parameters"""
        if view_name not in self.views:
            print(f"Warning: View '{view_name}' not found")
            return
        
        if clear_history:
            self.navigation_history.clear()
            self.last_selected_printer = None
            self.last_selected_bureau = None

        # If old view has "on view hidden" call the methode before switching to new view
        if hasattr(self.current_view, 'on_view_hidden'):
            self.current_view.on_view_hidden(self)
        
        target_view = self.views[view_name]

        # ---- APPLY FILTER TO TARGET VIEW FIRST ----
        if 'filter_printer' in kwargs and 'filter_slot' in kwargs and hasattr(target_view, 'set_filter'):
            target_view.set_filter(
                printer_name=kwargs.get('filter_printer'),
                slot_name=kwargs.get('filter_slot')
            )
        elif 'filter_printer' in kwargs and 'filter_bureau' in kwargs and hasattr(target_view, 'set_filter'):
            target_view.set_filter(
                printer_name=kwargs['filter_printer'],
                bureau_id=kwargs.get('filter_bureau')
            )
        elif 'filter_printer' in kwargs and hasattr(target_view, 'set_filter'):
            target_view.set_filter(printer_name=kwargs['filter_printer'])
        elif 'filter_bureau' in kwargs and hasattr(target_view, 'set_filter'):
            target_view.set_filter(bureau_id=kwargs['filter_bureau'])
        elif hasattr(target_view, 'clear_filter'):
            target_view.clear_filter()

        # ---- NOW SAVE HISTORY OF CURRENT VIEW ----
        if add_to_history and self.current_view and not clear_history:
            history_entry = {
            'view_name': getattr(self.current_view, 'name', None),
            'filter_printer': (
                getattr(self.current_view, 'filtered_printer', None)
                or kwargs.get('filter_printer')
                ),
            }
            self.navigation_history.append(history_entry)

        
        self.current_view = target_view

        #TODO remove debug print
        print("\n--- SWITCHING VIEW ---")
        print(f"{'view_name:':<30}{view_name}")
        print(f"{'filtered_printer:':<30}{self.current_view.filtered_printer if self.current_view else 'None'}")
        print(f"{'filtered_bureau:':<30}{self.current_view.filtered_bureau if self.current_view else 'None'} ")
        print(f"{'filtered_slot:':<30}{self.current_view.filtered_slot if self.current_view else 'None'}")
        print(f"{'last_selected_printer:':<30}{last_selected_printer}")
        print(f"{'last_selected_bureau:':<30}{last_selected_bureau}")
        print("-----------------------\n")

        self.filter_entry.delete(0, tk.END)
        
        columns = self.current_view.columns
        self.filter_dropdown["values"] = columns
        if columns:
            self.filter_column.set(columns[0])
        
        self.refresh_view()
        self._update_back_button()
        
        if hasattr(self.current_view, 'on_view_shown'):
            self.current_view.on_view_shown(self, self.dynamic_frame)


    def refresh_view(self) -> None:
        """Reload data and update treeview"""
        try:
            with db.get_connection() as conn:
                if hasattr(self.current_view, 'get_query'):
                    query = self.current_view.get_query()
                    cursor = conn.cursor()
                    cursor.execute(query)
                    self.current_rows = cursor.fetchall()
                else:
                    self.current_rows = self.current_view.fetch(conn)
            
            self._configure_columns()
            self._populate_tree(self.current_rows)

            # restore selection AFTER population
            self._restore_last_selection() 

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load data:\n{str(e)}")
            self.current_rows = []
        

    def _restore_last_selection(self) -> None: 
        """Restore selection but only for printers or bureaus"""
        if not self.last_selected_printer and not self.last_selected_bureau:
            return

        relevant_saved_value = None
        
        if self.current_view.name == "printers":
            relevant_saved_value = self.last_selected_printer
        if self.current_view.name == "bureaus":
            relevant_saved_value = self.last_selected_bureau

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values and values[0] == relevant_saved_value:
                self.tree.selection_set(item)
                self.tree.focus(item)
                self.tree.see(item)
                break

    def _update_back_button(self) -> None:
        """Update back button based on navigation history"""
        if self.back_button:
            self.back_button.destroy()
            self.back_button = None
        
        if self.navigation_history:
            # Ensure dynamic_frame is packed before the filter_bar
            self.dynamic_frame.pack(fill="x", before=self.main_frame.winfo_children()[1])
            
            last_entry = self.navigation_history[-1]
            view_name = last_entry.get('view_name', 'previous view')
            filter_info = ""
            if last_entry.get('filter_printer'):
                filter_info = f" ({last_entry['filter_printer']})"
            
            self.back_button = tk.Button(
                self.dynamic_frame,
                text=f"← Back to {view_name}{filter_info}",
                command=self._go_back
            )
            self.back_button.pack(side="top", fill="x", padx=5, pady=5)
        else:
            # No history, hide the dynamic frame to remove the gap
            self.dynamic_frame.pack_forget()

    def _go_back(self) -> None:
        """Navigate back to previous view"""
        if not self.navigation_history:
            return
        
        last_entry = self.navigation_history.pop()
        view_name = last_entry.get('view_name')
        
        if not view_name:
            return
        
        if view_name == "printers":
            #clear any filters when going back to printers view
            self.views["printers"].clear_filter()
        
        view_key = self._find_view_key_by_name(view_name)
        if not view_key:
            return
        
        filter_printer = last_entry.get('filter_printer')
        if filter_printer:
            self.switch_view(view_key, add_to_history=False, filter_printer=filter_printer)
        else:
            self.switch_view(view_key, add_to_history=False)

    def _find_view_key_by_name(self, view_name: str) -> Optional[str]:
        """Find view key by view name"""
        for key, view in self.views.items():
            if hasattr(view, 'name') and view.name == view_name:
                return key
        return None

    def _configure_columns(self) -> None:
        """Configure treeview columns"""
        columns = self.current_view.columns
        self.tree["columns"] = columns
        
        # Define specific widths for certain columns
        column_widths = {
            "CARIDocument": 300,  # Wider for this column
            "CARIdoc": 100,
            "SlotRemark": 200,
            "BureauRemark": 200,
            # Add more specific widths as needed
        }
        
        for col in columns:
            self.tree.heading(
                col, 
                text=col, 
                anchor="w",
                command=partial(self._sort_by_column, col)
            )
            
            # Use specific width if defined, otherwise use default
            width = column_widths.get(col, 120)
            self.tree.column(col, anchor="w", width=width, minwidth=50, stretch=True)

    def _populate_tree(self, rows: List[Tuple]) -> None:
        """Fill treeview with data (zebra styling)"""
        self.tree.delete(*self.tree.get_children())
        
        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", values=row, tags=(tag,))
        
        self.tree.tag_configure("even", background="white")
        self.tree.tag_configure("odd", background="#f2f2f2")
        
        self.count_label.config(text=f"Total: {len(rows)}")

    def _sort_by_column(self, column: str) -> None:
        """Sort by column"""
        idx = self.current_view.columns.index(column)
        self.current_rows.sort(key=lambda row: row[idx], reverse=self.sort_reverse)
        self.sort_reverse = not self.sort_reverse
        self._apply_filter()

    def _apply_filter(self, event=None) -> None:
        """Apply filter to displayed rows"""
        filter_text = self.filter_entry.get().lower()
        column = self.filter_column.get()
        
        if not filter_text or column not in self.current_view.columns:
            self._populate_tree(self.current_rows)
            return
        
        idx = self.current_view.columns.index(column)
        filtered = [
            row for row in self.current_rows 
            if filter_text in str(row[idx]).lower()
        ]
        self._populate_tree(filtered)

    def _on_double_click(self, event) -> None:
        """Handle double-click on treeview row"""
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        
        if not row_id or not self.current_view:
            return
        
        row_value = self.tree.item(row_id, "values")
        
        if hasattr(self.current_view, 'on_double_click'):
            self.current_view.on_double_click(self, row_value, col_id)

    def _dismiss_context_menu(self, event):
        try:
            self.context_menu.unpost()
        except:
            pass

    def _show_context_menu(self, event) -> None:
        """Show context menu on right-click"""
        row_id = self.tree.identify_row(event.y)
        
        if not self.current_view:
            return
        
        # If a row is clicked and not selected, select it
        if row_id and row_id not in self.tree.selection():
            self.tree.selection_set(row_id)

        selected_rows = [
            self.tree.item(row_id, "values")
            for row_id in self.tree.selection()
        ]

        self.context_menu.delete(0, "end")

        # Only show Modify and Delete if a row is selected
        if row_id:
            # Add base context actions which are common for all views
            self.context_menu.add_command(
                label="Modify",
                command=partial(self.current_view.modify, self, selected_rows)
            )
            self.context_menu.add_command(
                label=f"Delete ({len(selected_rows)})",
                command=partial(self.current_view.delete, self, selected_rows)
            )
            self.context_menu.add_command(
                label="Add",
                command=partial(self.current_view.add, self)
            )
        else:
            # No row selected, only show Add
            self.context_menu.add_command(
                label="Add",
                command=partial(self.current_view.add, self)
            )

        # Add view-specific context menu items, by calling build_context_menu of the view if it exists
        if hasattr(self.current_view, "build_context_menu"):
            self.context_menu.add_separator()
            self.current_view.build_context_menu(
                app=self,
                menu=self.context_menu,
                selected_rows=selected_rows
            )

        self.context_menu.post(event.x_root, event.y_root)

        # Bind left-click to dismiss menu
        self.root.bind("<Button-1>", self._dismiss_context_menu, add="+")


    def _add_base_context_actions(self, row: Tuple) -> None:
        """Add base context menu actions"""
        self.context_menu.add_command(
            label="Show details",
            command=partial(self.current_view.show_details, self, row)
        )
        self.context_menu.add_command(
            label="Delete",
            command=partial(self.current_view.delete, self, row)
        )

    def _run_in_thread(self, target_func, success_message: str, error_title: str) -> None:
        """Run a function in a separate thread with error handling"""
        def thread_wrapper():
            try:
                result = target_func()
                if isinstance(result, tuple):
                    success, message, *extra = result
                    if success:
                        messagebox.showinfo("Success", message)
                    else:
                        messagebox.showerror(error_title, message)
                else:
                    messagebox.showinfo("Success", success_message)
                
                self.refresh_view()
            except Exception as e:
                messagebox.showerror(error_title, f"Error: {str(e)}")
        
        thread = threading.Thread(target=thread_wrapper, daemon=True)
        thread.start()

    def _import_xlsx(self) -> None:
        """Prompt user to pick an XLSX file and run the import"""
        filename = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )

        if not filename:
            return

        from xlsx_import import run_import
        import pandas as pd

        # --- Confirm destructive import ---
        response = messagebox.askokcancel(
            "Confirm Import",
            "⚠️ WARNING: Importing will override ALL existing data in the database!\n\n"
            "All current printers, bureaus, slots and assignments will be deleted "
            "and replaced with the contents of the selected Excel file.\n\n"
            "Do you want to continue?",
            icon="warning"
        )

        if not response:
            return

        try:
            # --- Read Excel stats (before import) ---
            df_printers = pd.read_excel(filename, sheet_name=0)
            df_forms = pd.read_excel(filename, sheet_name=1)

            total_printer_rows = len(df_printers)
            total_form_rows = len(df_forms)

            # --- Run import ---
            self.root.config(cursor="watch")
            self.root.update()

            run_import(xlsx_file=filename)

            success_msg = (
                f"✅ Import finished successfully!\n\n"
                f"📊 Import Statistics:\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Printer sheet rows: {total_printer_rows}\n"
                f"Forms sheet rows: {total_form_rows}\n"
                f"Total rows processed: {total_printer_rows + total_form_rows}"
            )

            messagebox.showinfo("Success", success_msg)
            self.refresh_view()

        except Exception as e:
            messagebox.showerror("Import Error", f"Error: {str(e)}")

        finally:
            self.root.config(cursor="")


    def _export_xlsx(self) -> None:
        """Prompt user for export location and run the export"""
        from xlsx_export import export_printer_data
        
        filename = filedialog.asksaveasfilename(
            title="Save Excel Export As",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile="Druckerliste_CARI_export.xlsx"
        )
        
        if not filename:
            return
        
        try:
            # Disable the root window to prevent interaction
            self.root.config(cursor="watch")
            self.root.update()
            db_file = "printers.db"
            success, message, stats = export_printer_data(
                db_file=db_file,
                output_xlsx=filename
            )
            
            if success:
                stats_msg = (
                    f"{message}\n\n"
                    f"📊 Export Statistics:\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Total rows: {stats['total_rows']}\n"
                    f" • Bureau-printer connections: {stats['bureau_printer_connections']}\n"
                    f" • Printers without bureaus: {stats['printers_without_bureaus']}\n"
                    f" • Bureaus without printers: {stats['bureaus_without_printers']}\n\n"
                    f"Total CARIdocs: {stats['total_caridocs']}"
                )
                messagebox.showinfo("Success", stats_msg)
            else:
                messagebox.showerror("Export Error", message)
            
            self.refresh_view()
        except Exception as e:
            messagebox.showerror("Export Error", f"Error: {str(e)}")
        finally:
            # Re-enable the root window
            self.root.config(cursor="")

    