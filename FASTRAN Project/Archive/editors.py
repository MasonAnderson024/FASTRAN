# editors.py
"""
editors.py
----------
Houses the complex, application-specific Toplevel windows (editors) for the FASTRAN GUI.
Each class in this module represents a major editing dialog, such as the
spectrum creator, block loading editor, post-processor, and dkeff utility.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import xml.etree.ElementTree as ET
import queue
import csv
import copy

# Import modules from our application
import runners
import plots
import utils
import config # Needed for the post-processor to look up failure modes
from project import ProjectManager

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class SpectrumCreatorWindow(tk.Toplevel):
    """A Toplevel window for creating and editing spectrum loading files within a project."""
    def __init__(self, parent, callback, pm: ProjectManager, spectrum_filename: str):
        super().__init__(parent)
        self.title("Spectrum Editor")
        self.geometry("750x650")
        
        # --- NEW: Project-Aware Properties ---
        self.callback = callback
        self.project = pm
        self.spectrum_filename = spectrum_filename
        self.spectrum_filepath = os.path.join(self.project.get_path("input"), self.spectrum_filename)

        # --- State Variables (unchanged) ---
        self.levels_data = []
        self.level_widgets = []
        self.num_levels_var = tk.IntVar(value=0)
        self.speak_var = tk.StringVar(value="1.0")
        self.invert_var = tk.StringVar(value="0")
        self.undo_stack, self.redo_stack = [], []

        self._create_widgets()

        # Load the spectrum file from within the project, if it exists
        if os.path.exists(self.spectrum_filepath):
            self._load_spectrum_file(self.spectrum_filepath)
        else:
            if not self.levels_data: self.levels_data.append(['0.0', '0.0', '1'])
            self._redraw_levels_table()

        self._save_state_for_undo(clear_redo=False)
        self.transient(parent)
        self.grab_set()
        self.bind_all("<Control-z>", self._undo)
        self.bind_all("<Control-y>", self._redo)

    def _create_widgets(self):
        # --- Menubar (unchanged) ---
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        file_menu.add_command(label="Import External Spectrum...", command=self._import_spectrum)
        file_menu.add_command(label="Save", command=self._save_file)
        file_menu.add_command(label="Save & Close", command=self._generate_and_close)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.destroy)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self._undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self._redo)

        # --- Top Control Frame ---
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill='x', padx=10, pady=5)
        top_frame.columnconfigure(1, weight=1)
        ttk.Label(top_frame, text="Spectrum Title:").grid(row=0, column=0, sticky='w', pady=2)
        self.title_entry = ttk.Entry(top_frame)
        self.title_entry.insert(0, "Custom Spectrum")
        self.title_entry.grid(row=0, column=1, columnspan=3, sticky='ew', padx=5)
        ttk.Label(top_frame, text="INVERT:").grid(row=1, column=0, sticky='w', pady=(5,2))
        self.invert_entry = ttk.Entry(top_frame, width=10, textvariable=self.invert_var)
        self.invert_entry.grid(row=1, column=1, sticky='w', padx=5)
        ttk.Label(top_frame, text="SPEAK:").grid(row=2, column=0, sticky='w', pady=(5,2))
        speak_entry = ttk.Entry(top_frame, textvariable=self.speak_var, width=10)
        speak_entry.grid(row=2, column=1, sticky='w', padx=5)
        ttk.Button(top_frame, text="Save & Close", command=self._generate_and_close).grid(row=0, column=4, sticky='ne', padx=5)

        # --- CHANGED: Removed "Set Save Location" button and simplified the label ---
        self.output_label = ttk.Label(top_frame, text=f"File: {self.spectrum_filename} (in project input/ folder)", relief='sunken', anchor='w')
        self.output_label.grid(row=3, column=0, columnspan=5, sticky='ew', padx=0, pady=(10,0))
        
        # --- Paned Window and other widgets are unchanged ---
        paned_window = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned_window.pack(fill='both', expand=True, padx=10, pady=5)
        table_container = ttk.LabelFrame(paned_window, text="Stress Levels", padding="10")
        paned_window.add(table_container, weight=1)
        level_ctrl_frame = ttk.Frame(table_container)
        level_ctrl_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(level_ctrl_frame, text="Number of Levels:").pack(side='left')
        ttk.Spinbox(level_ctrl_frame, from_=0, to=500, textvariable=self.num_levels_var, width=6, command=self._update_levels_from_spinbox).pack(side='left', padx=5)
        ttk.Button(level_ctrl_frame, text="Import...", command=self._import_spectrum).pack(side='left', padx=(10, 0))
        ttk.Button(level_ctrl_frame, text="Normalize", command=self._normalize_spectrum).pack(side='left', padx=5)
        ttk.Button(level_ctrl_frame, text="Update Plot", command=self._update_plot).pack(side='left', padx=5)
        self.undo_button = ttk.Button(level_ctrl_frame, text="Undo", command=self._undo, state="disabled"); self.undo_button.pack(side='left', padx=(10, 0))
        self.redo_button = ttk.Button(level_ctrl_frame, text="Redo", command=self._redo, state="disabled"); self.redo_button.pack(side='left', padx=5)
        canvas = tk.Canvas(table_container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=canvas.yview)
        self.table_frame = ttk.Frame(canvas, padding="5")
        self.table_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        plot_container = ttk.LabelFrame(paned_window, text="Spectrum Plot", padding="10")
        paned_window.add(plot_container, weight=1)
        fig = Figure(dpi=100); fig.set_tight_layout(True)
        self.ax = fig.add_subplot(111)
        self.plot_canvas = FigureCanvasTkAgg(fig, master=plot_container)
        self.plot_canvas.get_tk_widget().pack(fill='both', expand=True)
        plot_container.bind("<Configure>", lambda event: self.plot_canvas.draw_idle())
        self._update_plot()

    def _save_file(self):
        """Saves the spectrum data to the correct file inside the project."""
        if not self.project.project_path:
            messagebox.showerror("Error", "No project is loaded.", parent=self)
            return False
        
        # The save path is now determined by the project context, set during __init__
        save_path = self.spectrum_filepath
        
        try:
            scale_factor = 1000.0
            title = self.title_entry.get()
            invert = int(self.invert_var.get())
            levels = []
            total_cycles, overall_smax_int, overall_smin_int = 0, -float('inf'), float('inf')
            self._sync_data_from_widgets()
            
            for level_data in self.levels_data:
                smax_float = utils.safe_float(level_data[0])
                smin_float = utils.safe_float(level_data[1])
                cycles = utils.safe_int(level_data[2])
                if cycles < 1: continue
                
                smax_int = int(round(smax_float * scale_factor))
                smin_int = int(round(smin_float * scale_factor))
                
                levels.append({'smax': smax_int, 'smin': smin_int, 'cycles': cycles})
                total_cycles += cycles
                overall_smax_int = max(overall_smax_int, smax_int)
                overall_smin_int = min(overall_smin_int, smin_int)
            
            with open(save_path, 'w') as f:
                f.write(f"{title}\n")
                f.write(f" {total_cycles * 2}    {overall_smax_int}    {overall_smin_int}    {invert}    3\n")
                
                line_str, current_col = "", 0
                for level in levels:
                    for _ in range(level['cycles']):
                        line_str += f"{level['smax']:8d}"
                        current_col += 1
                        if current_col >= 10:
                            f.write(line_str + "\n")
                            line_str, current_col = "", 0
                        
                        line_str += f"{level['smin']:8d}"
                        current_col += 1
                        if current_col >= 10:
                            f.write(line_str + "\n")
                            line_str, current_col = "", 0
                
                if line_str:
                    f.write(line_str + "\n")
            
            messagebox.showinfo("Success", f"Spectrum file '{self.spectrum_filename}' saved in project.", parent=self)
            if self.callback:
                self.callback(self.spectrum_filename)
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate spectrum file:\n{e}", parent=self)
            return False

    def _generate_and_close(self):
        if self._save_file():
            self.destroy()

    def _normalize_spectrum(self):
        self._save_state_for_undo()
        self._sync_data_from_widgets()
        max_abs_stress = 0.0
        for level_data in self.levels_data:
            try:
                max_abs_stress = max(max_abs_stress, abs(float(level_data[0])), abs(float(level_data[1])))
            except ValueError: continue
        if max_abs_stress == 0:
            messagebox.showinfo("Normalize", "Cannot normalize, max stress is zero.", parent=self)
            return
        for i, level_data in enumerate(self.levels_data):
            try:
                self.levels_data[i][0] = f"{float(level_data[0]) / max_abs_stress:.4g}"
                self.levels_data[i][1] = f"{float(level_data[1]) / max_abs_stress:.4g}"
            except ValueError: continue
        self.speak_var.set(f"{max_abs_stress:.4g}")
        self._redraw_levels_table()
        self._update_plot()

    def _update_levels_from_spinbox(self):
        self._save_state_for_undo()
        try:
            new_size = self.num_levels_var.get()
            if new_size < 0: return
            self._sync_data_from_widgets()
            while len(self.levels_data) < new_size: self.levels_data.append(['0.0', '0.0', '1'])
            if len(self.levels_data) > new_size: self.levels_data = self.levels_data[:new_size]
            self._redraw_levels_table()
        except tk.TclError: pass

    def _update_plot(self):
        self._sync_data_from_widgets()
        speak_val = utils.safe_float(self.speak_var.get(), 1.0)
        plots.plot_spectrum(self.ax, self.levels_data, speak_val)
        self.plot_canvas.draw()
        
    def _redraw_levels_table(self):
        for widget in self.table_frame.winfo_children(): widget.destroy()
        self.level_widgets.clear()
        headers = ["Max Stress", "Min Stress", "Cycles", "Actions"]
        for i, header in enumerate(headers):
            ttk.Label(self.table_frame, text=header, font="-weight bold").grid(row=0, column=i, padx=5, pady=5, columnspan=(3 if header=="Actions" else 1))
        for i, data_row in enumerate(self.levels_data):
            smax, smin, cycles = data_row
            smax_entry = ttk.Entry(self.table_frame, width=15); smax_entry.insert(0, smax); smax_entry.grid(row=i + 1, column=0, padx=5, pady=2)
            smin_entry = ttk.Entry(self.table_frame, width=15); smin_entry.insert(0, smin); smin_entry.grid(row=i + 1, column=1, padx=5, pady=2)
            cycles_entry = ttk.Entry(self.table_frame, width=10); cycles_entry.insert(0, cycles); cycles_entry.grid(row=i + 1, column=2, padx=5, pady=2)
            up_button = ttk.Button(self.table_frame, text="↑", width=3, command=lambda i=i: self._move_level_up(i))
            up_button.grid(row=i + 1, column=3, padx=(10, 2))
            down_button = ttk.Button(self.table_frame, text="↓", width=3, command=lambda i=i: self._move_level_down(i))
            down_button.grid(row=i + 1, column=4, padx=2)
            delete_button = ttk.Button(self.table_frame, text="Delete", width=8, command=lambda i=i: self._delete_level(i))
            delete_button.grid(row=i + 1, column=5, padx=2)
            if i == 0: up_button.config(state="disabled")
            if i == len(self.levels_data) - 1: down_button.config(state="disabled")
            self.level_widgets.append([smax_entry, smin_entry, cycles_entry])
        self.num_levels_var.set(len(self.levels_data))

    def _sync_data_from_widgets(self):
        for i, row_widgets in enumerate(self.level_widgets):
            if i < len(self.levels_data):
                self.levels_data[i] = [row_widgets[0].get(), row_widgets[1].get(), row_widgets[2].get()]

    def _save_state_for_undo(self, clear_redo=True):
        self._sync_data_from_widgets()
        self.undo_stack.append(copy.deepcopy(self.levels_data))
        if clear_redo: self.redo_stack.clear()
        self._update_undo_redo_buttons()

    def _undo(self, event=None):
        if len(self.undo_stack) <= 1: return
        self.redo_stack.append(self.undo_stack.pop())
        self.levels_data = copy.deepcopy(self.undo_stack[-1])
        self._redraw_levels_table(); self._update_plot(); self._update_undo_redo_buttons()

    def _redo(self, event=None):
        if not self.redo_stack: return
        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        self.levels_data = copy.deepcopy(state)
        self._redraw_levels_table(); self._update_plot(); self._update_undo_redo_buttons()

    def _update_undo_redo_buttons(self):
        self.undo_button.config(state="normal" if len(self.undo_stack) > 1 else "disabled")
        self.redo_button.config(state="normal" if self.redo_stack else "disabled")

    def _delete_level(self, index):
        self._save_state_for_undo()
        if 0 <= index < len(self.levels_data):
            self.levels_data.pop(index)
            self._redraw_levels_table()

    def _move_level_up(self, index):
        if index > 0:
            self._save_state_for_undo()
            self.levels_data[index], self.levels_data[index - 1] = self.levels_data[index - 1], self.levels_data[index]
            self._redraw_levels_table()

    def _move_level_down(self, index):
        if index < len(self.levels_data) - 1:
            self._save_state_for_undo()
            self.levels_data[index], self.levels_data[index + 1] = self.levels_data[index + 1], self.levels_data[index]
            self._redraw_levels_table()

    def _import_spectrum(self):
        filepath = filedialog.askopenfilename(title="Import Spectrum File", parent=self, filetypes=(("Spectrum Files", "*.spx *.sub *.txt"), ("All Files", "*.*")))
        if filepath: self._load_spectrum_file(filepath, from_import=True)

    def _load_spectrum_file(self, filepath, from_import=False):
        _, extension = os.path.splitext(filepath)
        new_levels_data, parser_used = None, ""
        try:
            if extension.lower() == '.spx':
                new_levels_data, parser_used = self._parse_spx(filepath), ".spx"
            elif extension.lower() in ['.sub', '.txt']:
                with open(filepath, 'r') as f: lines = [line.strip() for line in f.readlines() if line.strip()]
                if not lines: raise ValueError("File is empty")
                is_standard_fastran_txt = len(lines) > 1 and len(lines[1].split()) == 5 and all(p.replace('.','',1).replace('-','',1).isdigit() for p in lines[1].split())
                if is_standard_fastran_txt:
                    new_levels_data, parser_used = self._parse_spectrum_txt(filepath), "Standard FASTRAN .txt"
                else:
                    if len(lines) <= 1: raise ValueError("File contains only a title line or is empty.")
                    num_cols = len(lines[1].split())
                    if num_cols >= 3: new_levels_data, parser_used = self._parse_sub(filepath), ".sub (3-Column Text)"
                    elif num_cols == 1: new_levels_data, parser_used = self._parse_reversal_txt(filepath), "Reversal .txt (1-Column)"
                    else: messagebox.showwarning("Parsing Warning", "Unrecognized text format.", parent=self); new_levels_data, parser_used = self._parse_spectrum_txt(filepath), "Paired .txt"
            if new_levels_data is not None:
                if from_import: self._save_state_for_undo()
                self.levels_data = new_levels_data
                self._redraw_levels_table(); self._update_plot()
                if from_import: messagebox.showinfo("Import Success", f"Imported {len(new_levels_data)} levels using {parser_used} parser.", parent=self)
            else: raise ValueError("Could not parse file.")
        except Exception as e:
             messagebox.showerror("File Load Error", f"Could not load spectrum file.\nError: {e}", parent=self)
            
    def _parse_reversal_txt(self, filepath):
        with open(filepath, 'r') as f: lines = f.readlines()
        self.title_entry.delete(0, tk.END); self.title_entry.insert(0, lines[0].strip())
        self.speak_var.set("1.0"); self.invert_var.set("0")
        points = [float(p) for line in lines[1:] for p in line.split()]
        if len(points) < 2: return []
        stress_pairs = [[max(points[i], points[i+1]), min(points[i], points[i+1])] for i in range(len(points) - 1)]
        if not stress_pairs: return []
        pair_counts = {}
        for pair in stress_pairs: pair_counts[tuple(pair)] = pair_counts.get(tuple(pair), 0) + 1
        return [[f"{p[0]:.4g}", f"{p[1]:.4g}", str(c)] for p, c in pair_counts.items()]

    def _parse_spectrum_txt(self, filepath):
        with open(filepath, 'r') as f: lines = f.readlines()
        if len(lines) < 2: return None
        self.title_entry.delete(0, tk.END); self.title_entry.insert(0, lines[0].strip())
        header_parts = lines[1].strip().split()
        if len(header_parts) >= 5: self.invert_var.set(header_parts[3]); self.speak_var.set("1.0")
        body_text = "".join(line.strip('\n\r') for line in lines[2:])
        try: all_points_float = [float(body_text[i:i+8]) for i in range(0, len(body_text), 8) if body_text[i:i+8].strip()]
        except (ValueError, IndexError): all_points_float = [float(p) for p in body_text.split()]
        if not all_points_float: return []
        if len(all_points_float) % 2 != 0: all_points_float.pop()
        stress_pairs = [[all_points_float[i], all_points_float[i+1]] for i in range(0, len(all_points_float), 2)]
        levels = []
        if not stress_pairs: return []
        current_smax, current_smin, current_count = stress_pairs[0][0], stress_pairs[0][1], 1
        for i in range(1, len(stress_pairs)):
            next_smax, next_smin = stress_pairs[i]
            if abs(next_smax - current_smax) < 1e-9 and abs(next_smin - current_smin) < 1e-9:
                current_count += 1
            else:
                levels.append([f"{current_smax:.4g}", f"{current_smin:.4g}", str(current_count)])
                current_smax, current_smin, current_count = next_smax, next_smin, 1
        levels.append([f"{current_smax:.4g}", f"{current_smin:.4g}", str(current_count)])
        return levels
    
    def _parse_spx(self, filepath):
        tree = ET.parse(filepath); root = tree.getroot()
        self.title_entry.delete(0, tk.END); self.title_entry.insert(0, root.findtext('Title', ''))
        self.speak_var.set("1.0"); self.invert_var.set("0")
        levels = []
        subspectrum = root.find('.//SubSpectrum')
        if subspectrum is not None:
            for level in subspectrum.findall('B'):
                levels.append([level.get('Mx', '0.0'), level.get('Mn', '0.0'), level.get('C', '1')])
        return levels

    def _parse_sub(self, filepath):
        with open(filepath, 'r') as f: lines = [line.strip() for line in f.readlines() if line.strip()]
        self.title_entry.delete(0, tk.END); self.title_entry.insert(0, lines[0].strip())
        self.speak_var.set("1.0"); self.invert_var.set("0")
        return [line.split()[:3] for line in lines[1:] if len(line.split()) >= 3]



class PostProcessingWindow(tk.Toplevel):
    """
    A Toplevel window that acts as a results dashboard, showing a summary
    of inputs, the interactive plot, and the final analysis results.
    """
    def __init__(self, parent, header, data, input_params, summary_dict):
        super().__init__(parent)
        self.title("FASTRAN Post-Processor")
        self.geometry("1000x700")

        self.header = header
        self.data = data
        self.input_params = input_params
        self.summary_dict = summary_dict
        
        self.x_axis_var = tk.StringVar()
        self.y_axis_var = tk.StringVar()
        self.log_x_var = tk.BooleanVar(value=False)
        self.log_y_var = tk.BooleanVar(value=False)

        self._create_widgets()
        self._populate_summary_tree()
        self._populate_controls()

        self.transient(parent)
        self.grab_set()

    def _create_widgets(self):
        # --- Menu ---
        menubar = tk.Menu(self); self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Results As CSV...", command=self._save_parsed_results)
        file_menu.add_command(label="Export Plot...", command=self._export_plot)
        file_menu.add_separator(); file_menu.add_command(label="Close", command=self.destroy)

        # --- Main Layout ---
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill='both', expand=True, padx=10, pady=5)

        # --- Left Pane: Summary ---
        summary_frame = ttk.LabelFrame(main_pane, text="Input Summary", padding=10)
        main_pane.add(summary_frame, weight=1)
        
        self.summary_tree = ttk.Treeview(summary_frame, columns=('Parameter', 'Value'), show='headings', height=8)
        self.summary_tree.heading('Parameter', text='Parameter')
        self.summary_tree.heading('Value', text='Value')
        self.summary_tree.column('Parameter', width=150, anchor='w')
        self.summary_tree.column('Value', width=100, anchor='w')
        self.summary_tree.pack(fill='both', expand=True)

        # --- Right Pane: Plotting Area ---
        plot_area_frame = ttk.Frame(main_pane)
        main_pane.add(plot_area_frame, weight=3)

        plot_ctrl_frame = ttk.Frame(plot_area_frame, padding=5)
        plot_ctrl_frame.pack(fill='x', pady=5)
        
        ttk.Label(plot_ctrl_frame, text="Y-Axis:").pack(side='left', padx=(0,5))
        self.y_axis_combo = ttk.Combobox(plot_ctrl_frame, textvariable=self.y_axis_var, state='readonly', width=15)
        self.y_axis_combo.pack(side='left'); self.y_axis_combo.bind("<<ComboboxSelected>>", self._draw_custom_plot)
        ttk.Checkbutton(plot_ctrl_frame, text="log", variable=self.log_y_var, command=self._draw_custom_plot).pack(side='left', padx=5)
        
        ttk.Label(plot_ctrl_frame, text="X-Axis:").pack(side='left', padx=(20,5))
        self.x_axis_combo = ttk.Combobox(plot_ctrl_frame, textvariable=self.x_axis_var, state='readonly', width=15)
        self.x_axis_combo.pack(side='left'); self.x_axis_combo.bind("<<ComboboxSelected>>", self._draw_custom_plot)
        ttk.Checkbutton(plot_ctrl_frame, text="log", variable=self.log_x_var, command=self._draw_custom_plot).pack(side='left', padx=5)

        plot_canvas_frame = ttk.Frame(plot_area_frame)
        plot_canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)
        fig = Figure(dpi=100); fig.set_tight_layout(True)
        self.ax = fig.add_subplot(111)
        self.plot_canvas = FigureCanvasTkAgg(fig, master=plot_canvas_frame)
        self.plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # --- Bottom Frame: Final Results ---
        results_frame = ttk.LabelFrame(self, text="Final Results", padding=10)
        results_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # *** NEW LOGIC TO DISPLAY FULL FAILURE DESCRIPTION ***
        failure_code = self.summary_dict.get('failure_code')
        # Look up the code in the config dictionary, fall back to the raw reason if not found
        failure_description = config.FAILURE_MODES.get(failure_code, self.summary_dict.get('failure_reason', 'N/A'))
        
        results_text = (f"Total Cycles: {self.summary_dict.get('total_cycles', 'N/A')}\n"
                        f"Failure Mode: {failure_description}")
        ttk.Label(results_frame, text=results_text, justify=tk.LEFT).pack(anchor='w')

    def _populate_summary_tree(self):
        """Populates the Treeview with key input parameters."""
        for param, value in self.input_params.items():
            self.summary_tree.insert('', tk.END, values=(param, value))

    def _populate_controls(self):
        """Populates the plot comboboxes and draws the initial plot."""
        self.x_axis_combo.config(values=self.header)
        self.y_axis_combo.config(values=self.header)
        
        if 'CYCLES' in self.header: self.x_axis_var.set('CYCLES')
        if 'C_crack' in self.header: self.y_axis_var.set('C_crack')
        
        self._draw_custom_plot()

    def _draw_custom_plot(self, event=None):
        """Delegates plotting to the plots.py module."""
        try:
            plots.plot_post_processing(
                self.ax, self.header, self.data,
                self.x_axis_var.get(), self.y_axis_var.get(),
                self.log_x_var.get(), self.log_y_var.get()
            )
            self.plot_canvas.draw()
        except Exception as e:
            messagebox.showerror("Plotting Error", f"Could not create plot.\nDetails: {e}", parent=self)
        
    def _export_plot(self):
        filepath = filedialog.asksaveasfilename(
            title="Export Plot As", parent=self,
            filetypes=(("PNG Image", "*.png"),("SVG Vector Image", "*.svg"),("PDF Document", "*.pdf")),
            defaultextension=".png"
        )
        if not filepath: return
        try:
            self.ax.get_figure().savefig(filepath, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Success", f"Plot successfully exported to:\n{os.path.basename(filepath)}", parent=self)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export plot.\n{e}", parent=self)
    
    def _save_parsed_results(self):
        save_path = filedialog.asksaveasfilename(
            title="Save Results As", parent=self,
            defaultextension=".csv", 
            filetypes=(("CSV File", "*.csv"),("All Files", "*.*"))
        )
        if not save_path: return
        try:
            with open(save_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.header)
                writer.writerows(self.data)
            messagebox.showinfo("Success", f"Successfully saved results to:\n{os.path.basename(save_path)}", parent=self)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save the file.\n{e}", parent=self)

class BlockEditorWindow(tk.Toplevel):
    """A Toplevel window for editing variable-amplitude block loading (NFOPT=1)."""
    def __init__(self, parent, callback, initial_data, initial_params):
        super().__init__(parent)
        self.title("Block Loading Editor (NFOPT=1)")
        self.geometry("850x650")
        self.callback = callback
        self.blocks = copy.deepcopy(initial_data) if initial_data else [{'nsq': '1', 'levels': [['0.0', '0.0', '1']]}]
        self.current_block_index = 0
        self.param_vars = {k: tk.StringVar(value=initial_params.get(k, '0')) for k in ['MAXSEQ', 'MAXBLK', 'LPRINT', 'MAXLPR']}
        self.param_vars['SCALE'] = tk.StringVar(value=initial_params.get('SCALE', '1.0'))
        self.param_vars['MAXSEQ'].set(str(len(self.blocks)))
        self._create_widgets()
        self._populate_block_listbox()
        self.transient(parent); self.grab_set()

    def _create_widgets(self):
        bottom_frame = ttk.Frame(self, padding=10); bottom_frame.pack(side="bottom", fill="x")
        ttk.Button(bottom_frame, text="Save & Close", command=self._save_and_close).pack(side="right")
        params_lf = ttk.LabelFrame(self, text="Global Loading Parameters", padding=10); params_lf.pack(side="top", fill="x", padx=10, pady=5)
        param_labels = ["MAXSEQ:", "MAXBLK:", "SCALE:", "LPRINT:", "MAXLPR:"]
        for i, label in enumerate(param_labels):
            ttk.Label(params_lf, text=label).grid(row=i//3, column=(i%3)*2, sticky='w', padx=5, pady=2)
            entry = ttk.Entry(params_lf, textvariable=self.param_vars[label.replace(":", "")], width=10)
            if label == "MAXSEQ:": entry.config(state='disabled')
            entry.grid(row=i//3, column=(i%3)*2+1, sticky='w', padx=5)
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL); paned_window.pack(fill='both', expand=True, padx=10, pady=(10,0))
        left_pane = ttk.Frame(paned_window, padding=5); paned_window.add(left_pane, weight=1)
        list_frame = ttk.LabelFrame(left_pane, text="Block Sequence"); list_frame.pack(fill='both', expand=True)
        self.block_listbox = tk.Listbox(list_frame, exportselection=False); self.block_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        self.block_listbox.bind('<<ListboxSelect>>', self._on_block_select)
        list_ctrl_frame = ttk.Frame(left_pane); list_ctrl_frame.pack(fill='x', pady=5)
        btn_texts = ["Add Block", "Delete Block", "Move Up ↑", "Move Down ↓"]
        btn_cmds = [self._add_block, self._delete_block, self._move_block_up, self._move_block_down]
        for text, cmd in zip(btn_texts, btn_cmds): ttk.Button(list_ctrl_frame, text=text, command=cmd).pack(side='left', expand=True, fill='x', padx=2)
        self.right_pane = ttk.Frame(paned_window, padding=10); paned_window.add(self.right_pane, weight=3)

    def _populate_block_listbox(self):
        sel_idx = self.block_listbox.curselection()[0] if self.block_listbox.curselection() else self.current_block_index
        self.block_listbox.delete(0, tk.END)
        for i, block in enumerate(self.blocks): self.block_listbox.insert(tk.END, f"Block {i+1} (NSL={len(block.get('levels',[]))}, Reps={block.get('nsq',1)})")
        new_idx = min(sel_idx, len(self.blocks)-1)
        if new_idx >=0: self.block_listbox.selection_set(new_idx); self.block_listbox.activate(new_idx); self.block_listbox.see(new_idx)
        self.param_vars['MAXSEQ'].set(str(len(self.blocks))); self._on_block_select()

    def _on_block_select(self, event=None):
        if not self.block_listbox.curselection():
            if not self.blocks:
                for widget in self.right_pane.winfo_children(): widget.destroy()
                ttk.Label(self.right_pane, text="No Block Selected").pack()
                return
            else: self.block_listbox.selection_set(0)
        new_index = self.block_listbox.curselection()[0]
        self._sync_data_from_widgets(); self.current_block_index = new_index
        for widget in self.right_pane.winfo_children(): widget.destroy()
        props_frame = ttk.LabelFrame(self.right_pane, text=f"Block {self.current_block_index + 1} Properties", padding=5); props_frame.pack(fill='x')
        self.nsq_var = tk.StringVar(value=self.blocks[self.current_block_index].get('nsq', '1'))
        ttk.Label(props_frame, text="Block Repetitions (NSQ):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(props_frame, textvariable=self.nsq_var, width=10).grid(row=0, column=1, sticky='w', padx=5)
        self.nsl_label = ttk.Label(props_frame, text=""); self.nsl_label.grid(row=0, column=2, sticky='w', padx=20)
        levels_frame = ttk.LabelFrame(self.right_pane, text="Stress Levels in Block", padding=5); levels_frame.pack(fill='both', expand=True, pady=5)
        ttk.Button(levels_frame, text="Add Level", command=self._add_block_level).pack(anchor='w', pady=(0,5))
        canvas = tk.Canvas(levels_frame, borderwidth=0, highlightthickness=0); scrollbar = ttk.Scrollbar(levels_frame, orient="vertical", command=canvas.yview)
        self.table_frame = ttk.Frame(canvas, padding="5"); self.table_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.table_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        self._redraw_block_levels_table()

    def _update_nsl_display(self):
        if hasattr(self, 'nsl_label') and self.blocks: self.nsl_label.config(text=f"Number of Levels (NSL): {len(self.blocks[self.current_block_index]['levels'])}")

    def _redraw_block_levels_table(self):
        # This implementation is nearly identical to the _redraw_levels_table in SpectrumCreatorWindow
        for widget in self.table_frame.winfo_children(): widget.destroy()
        self.level_widgets = []
        if not self.blocks: return
        block_levels = self.blocks[self.current_block_index]['levels']
        headers = ["Max Stress", "Min Stress", "Cycles", "Actions"]
        for i, h in enumerate(headers): ttk.Label(self.table_frame, text=h, font="-weight bold").grid(row=0, column=i, padx=5, pady=2, columnspan=(3 if h=="Actions" else 1))
        for i, data_row in enumerate(block_levels):
            smax, smin, cycles = data_row
            smax_entry = ttk.Entry(self.table_frame, width=15); smax_entry.insert(0, smax); smax_entry.grid(row=i + 1, column=0, padx=5, pady=2)
            smin_entry = ttk.Entry(self.table_frame, width=15); smin_entry.insert(0, smin); smin_entry.grid(row=i + 1, column=1, padx=5, pady=2)
            cycles_entry = ttk.Entry(self.table_frame, width=10); cycles_entry.insert(0, cycles); cycles_entry.grid(row=i + 1, column=2, padx=5, pady=2)
            up_btn = ttk.Button(self.table_frame, text="↑", width=3, command=lambda i=i: self._move_block_level(i, -1)); up_btn.grid(row=i + 1, column=3, padx=(10, 2))
            down_btn = ttk.Button(self.table_frame, text="↓", width=3, command=lambda i=i: self._move_block_level(i, 1)); down_btn.grid(row=i + 1, column=4, padx=2)
            del_btn = ttk.Button(self.table_frame, text="Delete", width=8, command=lambda i=i: self._delete_block_level(i)); del_btn.grid(row=i + 1, column=5, padx=2)
            if i == 0: up_btn.config(state="disabled")
            if i == len(block_levels) - 1: down_btn.config(state="disabled")
            self.level_widgets.append([smax_entry, smin_entry, cycles_entry])
        self._update_nsl_display()

    def _sync_data_from_widgets(self):
        if not hasattr(self, 'nsq_var') or not self.blocks: return
        block_data = self.blocks[self.current_block_index]
        block_data['nsq'] = self.nsq_var.get()
        block_data['levels'] = [[w.get() for w in row_widgets] for row_widgets in self.level_widgets]
        
    def _add_block_level(self):
        self._sync_data_from_widgets(); self.blocks[self.current_block_index]['levels'].append(['0.0', '0.0', '1']); self._redraw_block_levels_table(); self._populate_block_listbox()

    def _delete_block_level(self, index):
        self._sync_data_from_widgets()
        if len(self.blocks[self.current_block_index]['levels']) > 1: self.blocks[self.current_block_index]['levels'].pop(index)
        else: messagebox.showwarning("Warning", "A block must have at least one level.", parent=self)
        self._redraw_block_levels_table(); self._populate_block_listbox()

    def _move_block_level(self, index, direction):
        self._sync_data_from_widgets()
        levels = self.blocks[self.current_block_index]['levels']; new_index = index + direction
        if 0 <= new_index < len(levels): levels[index], levels[new_index] = levels[new_index], levels[index]
        self._redraw_block_levels_table()

    def _add_block(self):
        self._sync_data_from_widgets(); self.blocks.append({'nsq': '1', 'levels': [['0.0', '0.0', '1']]})
        self._populate_block_listbox(); self.block_listbox.selection_set(tk.END)

    def _delete_block(self):
        if not self.block_listbox.curselection() or len(self.blocks) <= 1: return
        self.blocks.pop(self.block_listbox.curselection()[0]); self.current_block_index = 0; self._populate_block_listbox()

    def _move_block(self, direction):
        if not self.block_listbox.curselection(): return
        index = self.block_listbox.curselection()[0]; new_index = index + direction
        if 0 <= new_index < len(self.blocks):
            self._sync_data_from_widgets()
            self.blocks[index], self.blocks[new_index] = self.blocks[new_index], self.blocks[index]
            self._populate_block_listbox(); self.block_listbox.selection_set(new_index)
            
    def _move_block_up(self): self._move_block(-1)
    def _move_block_down(self): self._move_block(1)

    def _save_and_close(self):
        self._sync_data_from_widgets()
        if self.callback:
            self.callback({'params': {k: v.get() for k,v in self.param_vars.items()}, 'blocks': self.blocks})
        self.destroy()

class DkeffWindow(tk.Toplevel):
    """
    A Toplevel window for generating dKeff data by running dkeff.exe.
    This serves as a GUI front-end for the DKEFF13 utility described in the
    FASTRAN user guide.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Material Data Generator (dkeff)")
        self.geometry("850x700")

        self.parent = parent
        self.dkeff_input_path = None
        self.processed_data = []
        self.dkeff_queue = queue.Queue()
        self.parsed_tlookup_table = None
        self.r_ratio_options = {}

        # Mappings specific to the dkeff tool
        self.lunit_map = {
            "Keep Same Units": '0',
            "Input: English -> Output: SI": '1',
            "Input: SI -> Output: English": '2'
        }
        self.ntyp_map = {
            "Middle-crack tension": '1',
            "Compact C(T)": '2',
            "ESE(T)": '3'
        }
        self.ntyp_rev_map = {v: k for k, v in self.ntyp_map.items()}
        self.nsop_map = {
            "Calculate c (NSOP=0)": '0',
            "Input c (NSOP=1)": '1',
            "Input So/Smax (NSOP=2)": '2'
        }
        self.nsop_rev_map = {v: k for k, v in self.nsop_map.items()}
        self.test_type_map = {"Constant R test": '0', "Kmax test": '1'}
        self.test_type_rev_map = {v: k for k, v in self.test_type_map.items()}

        # Tkinter variables for widget state
        self.ntyp_var = tk.StringVar(value="Compact C(T)")
        self.nsop_var = tk.StringVar(value="Input c (NSOP=1)")
        self.nsop_var.trace_add('write', self._update_nsop_widgets)
        self.test_type_var = tk.StringVar(value="Kmax test")
        self.test_type_var.trace_add('write', self._update_test_type_widgets)
        self.output_filename_var = tk.StringVar(value="output.dkout")
        self.r_var = tk.StringVar(value="0.1")
        self.smax_var = tk.StringVar(value="7.5")
        self.dkeff_version_var = tk.StringVar(value="dkeff21f (New)")
        
        self._create_widgets()
        self._update_test_type_widgets()
        
        self.transient(parent)
        self.grab_set()

    def _create_widgets(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Batch Convert .lkpx File...", command=self.parent._batch_convert_lkpx)
        file_menu.add_separator()
        file_menu.add_command(label="Load dkeff Input File...", command=self._load_dkeff_input_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save Input File As...", command=self._save_dkeff_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.destroy)
        
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(fill='both', expand=True, padx=10, pady=5)

        params_frame = ttk.Frame(paned_window, padding="10")
        paned_window.add(params_frame, weight=2)

        self.input_file_label = ttk.Label(params_frame, text="Input File: None", relief="sunken", anchor="w", padding=2)
        self.input_file_label.pack(fill='x', pady=(0,10))

        mat_prop_lf = ttk.LabelFrame(params_frame, text="Material Properties", padding="10")
        mat_prop_lf.pack(fill='x', pady=5)
        
        ttk.Label(mat_prop_lf, text="Yield Stress (SYIELD):").grid(row=0, column=0, sticky='w', pady=2)
        self.syield_entry = ttk.Entry(mat_prop_lf)
        self.syield_entry.grid(row=0, column=1, sticky='ew', padx=5)

        ttk.Label(mat_prop_lf, text="Ultimate Strength (SULT):").grid(row=1, column=0, sticky='w', pady=2)
        self.sult_entry = ttk.Entry(mat_prop_lf)
        self.sult_entry.grid(row=1, column=1, sticky='ew', padx=5)

        ttk.Label(mat_prop_lf, text="Elastic Modulus (E):").grid(row=2, column=0, sticky='w', pady=2)
        self.e_entry = ttk.Entry(mat_prop_lf)
        self.e_entry.grid(row=2, column=1, sticky='ew', padx=5)

        analysis_lf = ttk.LabelFrame(params_frame, text="Test & Analysis Parameters", padding="10")
        analysis_lf.pack(fill='x', pady=5)
        
        ttk.Label(analysis_lf, text="Specimen Type (NTYP):").grid(row=0, column=0, sticky='w', pady=2)
        self.ntyp_combo = ttk.Combobox(analysis_lf, textvariable=self.ntyp_var, state='readonly', values=list(self.ntyp_map.keys()))
        self.ntyp_combo.current(1)
        self.ntyp_combo.grid(row=0, column=1, sticky='ew', padx=5)
        
        ttk.Label(analysis_lf, text="dkeff Version:").grid(row=1, column=0, sticky='w', pady=2)
        self.dkeff_version_combo = ttk.Combobox(analysis_lf, textvariable=self.dkeff_version_var, state='readonly', values=["dkeff21f (New)", "dkeff13 (Legacy)"])
        self.dkeff_version_combo.grid(row=1, column=1, sticky='ew', padx=5)

        ttk.Label(analysis_lf, text="Test Type:").grid(row=2, column=0, sticky='w', pady=2)
        self.test_type_combo = ttk.Combobox(analysis_lf, textvariable=self.test_type_var, state='readonly', values=list(self.test_type_map.keys()))
        self.test_type_combo.grid(row=2, column=1, sticky='ew', padx=5)

        ttk.Label(analysis_lf, text="Analysis Mode (NSOP):").grid(row=3, column=0, sticky='w', pady=2)
        self.nsop_combo = ttk.Combobox(analysis_lf, textvariable=self.nsop_var, state='readonly', values=list(self.nsop_map.keys()))
        self.nsop_combo.grid(row=3, column=1, sticky='ew', padx=5)
        
        self.kmax_lbl = ttk.Label(analysis_lf, text="Kmax:")
        self.kmax_lbl.grid(row=4, column=0, sticky='w', pady=2)
        self.kmax_entry = ttk.Entry(analysis_lf)
        self.kmax_entry.grid(row=4, column=1, sticky='ew', padx=5)

        self.r_lbl = ttk.Label(analysis_lf, text="Stress Ratio (R):")
        self.r_lbl.grid(row=5, column=0, sticky='w', pady=2)
        self.r_entry = ttk.Entry(analysis_lf, textvariable=self.r_var)
        self.r_entry.grid(row=5, column=1, sticky='ew', padx=5)

        self.smax_lbl = ttk.Label(analysis_lf, text="Smax:")
        self.smax_lbl.grid(row=6, column=0, sticky='w', pady=2)
        self.smax_entry = ttk.Entry(analysis_lf, textvariable=self.smax_var)
        self.smax_entry.grid(row=6, column=1, sticky='ew', padx=5)

        ttk.Label(analysis_lf, text="Specimen Width (W):").grid(row=7, column=0, sticky='w', pady=2)
        self.w_entry = ttk.Entry(analysis_lf)
        self.w_entry.grid(row=7, column=1, sticky='ew', padx=5)

        ttk.Label(analysis_lf, text="Specimen Thickness (T):").grid(row=8, column=0, sticky='w', pady=2)
        self.t_entry = ttk.Entry(analysis_lf)
        self.t_entry.grid(row=8, column=1, sticky='ew', padx=5)

        ttk.Label(analysis_lf, text="Constraint Factor (ALP):").grid(row=9, column=0, sticky='w', pady=2)
        self.alp_entry = ttk.Entry(analysis_lf)
        self.alp_entry.grid(row=9, column=1, sticky='ew', padx=5)
        
        ttk.Label(analysis_lf, text="Unit Conversion (LUNIT):").grid(row=10, column=0, sticky='w', pady=2)
        self.lunit_combo = ttk.Combobox(analysis_lf, state='readonly', values=list(self.lunit_map.keys()))
        self.lunit_combo.current(0)
        self.lunit_combo.grid(row=10, column=1, sticky='ew', padx=5)

        table_container = ttk.Frame(paned_window, padding="5")
        paned_window.add(table_container, weight=3)
        
        table_lf = ttk.LabelFrame(table_container, text="Lab Data (Editable)", padding="10")
        table_lf.pack(fill='both', expand=True)
        
        grid_canvas = tk.Canvas(table_lf, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(table_lf, orient="vertical", command=grid_canvas.yview)
        self.grid_frame = ttk.Frame(grid_canvas)
        self.grid_frame.bind("<Configure>", lambda e: grid_canvas.configure(scrollregion=grid_canvas.bbox("all")))
        grid_canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        grid_canvas.configure(yscrollcommand=scrollbar.set)
        grid_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.grid_widgets = []

        bottom_frame = ttk.Frame(self, padding="10")
        bottom_frame.pack(fill='x', side='bottom')

        self.status_label = ttk.Label(bottom_frame, text="Status: Ready. Load a file or enter data manually.")
        self.status_label.pack(side='top', fill='x', pady=(0, 5))

        control_frame = ttk.Frame(bottom_frame)
        control_frame.pack(side='top', fill='x')

        ttk.Label(control_frame, text="Output Filename:").pack(side='left', padx=(0,5))
        ttk.Entry(control_frame, textvariable=self.output_filename_var).pack(side='left', fill='x', expand=True)
        
        ttk.Button(control_frame, text="Validate Data", command=self._validate_grid_data).pack(side='left', padx=5)

        self.generate_button = ttk.Button(control_frame, text="Generate dKeff Data", command=self._run_dkeff, state='normal')
        self.generate_button.pack(side='left', padx=5)
        self.apply_button = ttk.Button(control_frame, text="Apply to Main Window", command=self._apply_to_main, state='disabled')
        self.apply_button.pack(side='left', padx=5)
        ttk.Button(control_frame, text="Close", command=self.destroy).pack(side='right')

    def _update_test_type_widgets(self, *args):
        is_kmax_test = (self.test_type_var.get() == "Kmax test")
        for widget in [self.kmax_lbl, self.kmax_entry]:
            widget.grid() if is_kmax_test else widget.grid_remove()
        for widget in [self.r_lbl, self.r_entry, self.smax_lbl, self.smax_entry]:
            widget.grid_remove() if is_kmax_test else widget.grid()

    def _redraw_grid(self, data):
        for widget in self.grid_frame.winfo_children(): widget.destroy()
        self.grid_widgets = []
        nsop_mode = self.nsop_map.get(self.nsop_var.get())
        header3_text = "So/Smax" if nsop_mode == '2' else "Crack Length (c)"
        headers = ['ΔK', 'da/dN', header3_text]
        for col, header_text in enumerate(headers):
            if nsop_mode == '0' and col == 2: continue
            ttk.Label(self.grid_frame, text=header_text, font="-weight bold").grid(row=0, column=col, padx=5, pady=2)
        for row_idx, row_data in enumerate(data):
            row_of_widgets = []
            for col_idx, cell_data in enumerate(row_data):
                if nsop_mode == '0' and col_idx == 2: continue
                entry = ttk.Entry(self.grid_frame, width=15); entry.insert(0, str(cell_data))
                entry.grid(row=row_idx + 1, column=col_idx, padx=5, pady=1)
                row_of_widgets.append(entry)
            self.grid_widgets.append(row_of_widgets)

    def _validate_grid_data(self):
        is_valid = True; last_dk, last_rate = -float('inf'), -float('inf')
        style = ttk.Style(); style.configure('Invalid.TEntry', foreground='red')
        for row_widgets in self.grid_widgets:
            dk_entry, rate_entry = row_widgets[0], row_widgets[1]; row_is_ok = True
            try:
                current_dk, current_rate = float(dk_entry.get()), float(rate_entry.get())
                if current_dk <= last_dk or current_rate <= last_rate: row_is_ok, is_valid = False, False
                last_dk, last_rate = current_dk, current_rate
            except (ValueError, IndexError): row_is_ok, is_valid = False, False
            for widget in row_widgets: widget.config(style='Invalid.TEntry' if not row_is_ok else 'TEntry')
        self.status_label.config(text="Data validation passed." if is_valid else "Validation Failed: Data must be numeric and ascending.")
        return is_valid

    def _update_nsop_widgets(self, *args):
        self._redraw_grid([[w.get() for w in row_widgets] for row_widgets in self.grid_widgets])
    
    def _load_dkeff_input_file(self):
        filepath = filedialog.askopenfilename(title="Select dkeff Input File", filetypes=(("dkeff Input", "*.dkin"), ("All Files", "*.*")), parent=self)
        if not filepath: return
        try:
            with open(filepath, 'r') as f: lines = [line.strip() for line in f.readlines() if line.strip()]
            datasets = []
            for i, line in enumerate(lines):
                parts = line.split()
                try:
                    is_header = (len(parts) in [4, 5] and all(p.replace('.', '', 1).replace('-', '', 1).isdigit() for p in parts))
                    if is_header:
                        desc = f"Dataset {len(datasets)+1}: " + (f"R={parts[1]}, Smax={parts[2]}" if len(parts) == 5 else f"Kmax={parts[1]}")
                        datasets.append({'start_line': i, 'description': desc})
                except Exception: continue
            if not datasets: raise ValueError("No valid datasets found.")
            selected_idx = 0
            if len(datasets) > 1:
                dialog = DatasetSelectionDialog(self, [d['description'] for d in datasets])
                if dialog.result_index is None: return
                selected_idx = dialog.result_index
            dataset_to_load = datasets[selected_idx]; start_index = dataset_to_load['start_line']
            def set_entry(widget, value): widget.delete(0, tk.END); widget.insert(0, value)
            self.parent.vars['MAT'].set(os.path.splitext(os.path.basename(filepath))[0])
            ntyp_code, lunit_code = lines[2].split(); self.ntyp_var.set(self.ntyp_rev_map.get(ntyp_code, "Compact C(T)")); self.lunit_combo.set(next((k for k, v in self.lunit_map.items() if v == lunit_code), "Keep Same Units"))
            parts_l4 = lines[3].split(); set_entry(self.syield_entry, parts_l4[0]); set_entry(self.sult_entry, parts_l4[1]); set_entry(self.e_entry, parts_l4[2]); set_entry(self.alp_entry, parts_l4[5]); self.nsop_var.set(self.nsop_rev_map.get(parts_l4[6], "Input c (NSOP=1)"))
            parts_header = lines[start_index].split()
            if len(parts_header) == 5: self.test_type_var.set("Constant R test"); mtab, r_val, smax_val, w_val, t_val = parts_header; self.r_var.set(r_val); self.smax_var.set(smax_val)
            else: self.test_type_var.set("Kmax test"); mtab, kmax_val, w_val, t_val = parts_header; set_entry(self.kmax_entry, kmax_val)
            set_entry(self.w_entry, w_val); set_entry(self.t_entry, t_val)
            loaded_data = []
            data_lines = lines[start_index + 1 : start_index + 1 + int(mtab)]
            for line in data_lines: parts = line.split(); loaded_data.append([parts[1], parts[2], parts[3] if len(parts) > 3 else ""])
            self._redraw_grid(loaded_data); self.output_filename_var.set(f"{os.path.splitext(os.path.basename(filepath))[0]}.dkout")
            self.status_label.config(text=f"Loaded {dataset_to_load['description']}."); self.apply_button.config(state='disabled'); self._validate_grid_data()
        except Exception as e:
            messagebox.showerror("File Load Error", f"Could not load dkeff input file:\n{e}", parent=self)
    
    def _save_dkeff_input_file(self, filepath):
        try:
            mat_name, ntyp_code, lunit_code, nsop_code = self.parent.vars['MAT'].get(), self.ntyp_map[self.ntyp_var.get()], self.lunit_map[self.lunit_combo.get()], self.nsop_map[self.nsop_var.get()]
            dkeff_version, test_type = self.dkeff_version_var.get(), self.test_type_var.get()
            syield, sult, e_mod, alp, w_val, t_val = self.syield_entry.get(), self.sult_entry.get(), self.e_entry.get(), self.alp_entry.get(), self.w_entry.get(), self.t_entry.get()
            grid_data = [[widget.get() for widget in row] for row in self.grid_widgets]; mtab = len(grid_data)
            lines = [f"dkeff input from {os.path.basename(filepath)}", f" {mat_name}", f"{ntyp_code}  {lunit_code}"]
            if "dkeff13" in dkeff_version and test_type == "Kmax test": lines.append(f" {syield}  {sult}  {e_mod}  {alp}")
            else: lines.append(f" {syield}  {sult}  {e_mod}  0  0  {alp}  {nsop_code}")
            if test_type == "Kmax test": lines.append(f" {mtab}  {self.kmax_entry.get()}  {w_val}  {t_val}")
            else: lines.append(f" {mtab}  {self.r_var.get()}  {self.smax_var.get()}  {w_val}  {t_val}")
            for i, row in enumerate(grid_data):
                if nsop_code == '0': lines.append(f"  {i+1} {row[0]} {row[1]}")
                else: lines.append(f"  {i+1} {row[0]} {row[1]} {row[2]}")
            with open(filepath, 'w') as f: f.write('\n'.join(lines))
            self.dkeff_input_path = filepath; self.input_file_label.config(text=f"Input File: {os.path.basename(filepath)}")
            self.output_filename_var.set(f"{os.path.splitext(os.path.basename(filepath))[0]}.dkout"); self.status_label.config(text="Saved input file. Ready to generate data.")
            return True
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save dkeff input file:\n{e}", parent=self)
            return False

    def _save_dkeff_file_as(self):
        # --- Suggests saving inside the project ---
        initial_dir = self.parent.project.project_path
        if initial_dir:
            dkeff_dir = os.path.join(initial_dir, "dkeff")
            os.makedirs(dkeff_dir, exist_ok=True)
            initial_dir = dkeff_dir
        
        filepath = filedialog.asksaveasfilename(
            title="Save dkeff Input File",
            initialdir=initial_dir, # <-- This is the change
            defaultextension=".dkin",
            filetypes=(("dkeff Input", "*.dkin"),),
            parent=self
        )
        if filepath:
            return self._save_dkeff_input_file(filepath)
        return False

    def _run_dkeff(self):
        if not self.dkeff_input_path and not self._save_dkeff_file_as():
            self.status_label.config(text="Status: Save cancelled. Run aborted."); return
        if not self.parent.dkeff_exe_path:
            messagebox.showerror("dkeff Path Not Set", "Set path to dkeff.exe in main window's File menu.", parent=self); return
        self.generate_button.config(state="disabled"); self.status_label.config(text="Status: Running dkeff...")
        output_path = os.path.join(os.path.dirname(self.dkeff_input_path), self.output_filename_var.get()); self.dkeff_output_path = output_path
        runners.run_dkeff(
            self.parent.dkeff_exe_path,
            self.dkeff_input_path,
            self.dkeff_output_path,
            self.test_type_map[self.test_type_var.get()],
            self.dkeff_queue
        )
        self.after(100, self._process_dkeff_queue)

    def _process_dkeff_queue(self):
        try:
            message = self.dkeff_queue.get_nowait()
            if "ERROR" in message:
                messagebox.showerror("dkeff Error", message, parent=self); self.status_label.config(text="Status: Error!")
                self.generate_button.config(state="normal")
            elif message == "DONE":
                self.processed_data = []
                with open(self.dkeff_output_path, 'r') as f:
                    in_data_section = False
                    for line in f:
                        if "DKEFF ELASTIC:" in line: in_data_section = True; continue
                        if in_data_section and line.strip():
                            parts = line.split()
                            if len(parts) >= 2:
                                try: self.processed_data.append([f"{float(parts[0]):.4f}", f"{float(parts[1]):.4E}"])
                                except (ValueError, IndexError): continue
                self.status_label.config(text=f"Run complete. {len(self.processed_data)} data points processed.")
                self.generate_button.config(state="normal"); self.apply_button.config(state="normal")
        except queue.Empty:
            self.after(100, self._process_dkeff_queue)

    def _apply_to_main(self):
        if not self.processed_data:
            messagebox.showerror("Error", "No processed data available to apply.", parent=self); return
        try:
            syield, sult, e_mod = float(self.syield_entry.get()), float(self.sult_entry.get()), float(self.e_entry.get())
            lunit_code, factor = self.lunit_map[self.lunit_combo.get()], 6.895 # ksi to MPa
            if lunit_code == '1': syield *= factor; sult *= factor; e_mod *= factor
            elif lunit_code == '2': syield /= factor; sult /= factor; e_mod /= factor
            self.parent.vars['SYIELD'].set(f"{syield:.1f}"); self.parent.vars['SULT'].set(f"{sult:.1f}"); self.parent.vars['E'].set(f"{e_mod:.1f}")
            self.parent.table_data = self.processed_data; self.parent.vars['NTAB'].set(str(len(self.processed_data))); self.parent._redraw_table()
            messagebox.showinfo("Success", f"Applied {len(self.processed_data)} data points to main window.", parent=self)
            self.destroy()
        except ValueError:
            messagebox.showerror("Value Error", "Could not apply data. Ensure material properties are valid numbers.", parent=self)

class BatchInputDialog(tk.Toplevel):
    """A helper dialog for the DkeffWindow to get batch parameters for multiple R-ratios."""
    def __init__(self, parent, r_ratios):
        super().__init__(parent)
        self.title("Enter Batch Parameters")
        self.transient(parent); self.grab_set()
        self.result, self.entries = None, {}
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0); scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding="10")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        headers = ["R-Ratio", "Smax", "Width (W)", "Thickness (T)"]
        for col, header in enumerate(headers): ttk.Label(scrollable_frame, text=header, font="-weight bold").grid(row=0, column=col, padx=5, pady=5)
        for i, r_ratio in enumerate(r_ratios, start=1):
            ttk.Label(scrollable_frame, text=f"{r_ratio}").grid(row=i, column=0, sticky='w')
            smax_var, w_var, t_var = tk.StringVar(value="10.0"), tk.StringVar(value="3.0"), tk.StringVar(value="0.25")
            ttk.Entry(scrollable_frame, textvariable=smax_var, width=10).grid(row=i, column=1, padx=5, pady=2)
            ttk.Entry(scrollable_frame, textvariable=w_var, width=10).grid(row=i, column=2, padx=5, pady=2)
            ttk.Entry(scrollable_frame, textvariable=t_var, width=10).grid(row=i, column=3, padx=5, pady=2)
            self.entries[r_ratio] = (smax_var, w_var, t_var)
        button_frame = ttk.Frame(self, padding="10")
        ttk.Button(button_frame, text="Generate", command=self.on_ok).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side='right')
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y"); button_frame.pack(side='bottom', fill='x')
        self.wait_window()

    def on_ok(self):
        self.result = {r: (s.get(), w.get(), t.get()) for r, (s, w, t) in self.entries.items()}; self.destroy()
    def on_cancel(self):
        self.result = None; self.destroy()

class DatasetSelectionDialog(tk.Toplevel):
    """A helper dialog for the DkeffWindow to select one of multiple datasets found in a file."""
    def __init__(self, parent, dataset_info):
        super().__init__(parent)
        self.title("Select Dataset")
        self.transient(parent); self.grab_set()
        self.result_index = None
        ttk.Label(self, text="This file contains multiple datasets. Please select one to load:", padding=10).pack()
        listbox_frame = ttk.Frame(self, padding=(10, 0, 10, 10)); listbox_frame.pack(fill='both', expand=True)
        self.listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE, exportselection=False)
        for item in dataset_info: self.listbox.insert(tk.END, item)
        self.listbox.selection_set(0); self.listbox.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.listbox.yview); scrollbar.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=scrollbar.set)
        button_frame = ttk.Frame(self, padding="10"); button_frame.pack(fill='x')
        ttk.Button(button_frame, text="Load Selected", command=self.on_ok).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side='right')
        self.wait_window()

    def on_ok(self):
        if self.listbox.curselection(): self.result_index = self.listbox.curselection()[0]
        self.destroy()
    def on_cancel(self):
        self.result_index = None; self.destroy()
