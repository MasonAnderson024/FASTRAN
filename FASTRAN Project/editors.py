# editors.py
"""
editors.py
----------
All Toplevel editor windows for the FASTRAN GUI:
  - SpectrumCreatorWindow  — create/edit spectrum loading files
  - PostProcessingWindow   — single-run results dashboard
  - BlockEditorWindow      — NFOPT=1 block loading editor
  - DkeffWindow            — dKeff material data generator (dkeff13 + dkeff21)
  - BatchInputDialog       — helper for .lkpx batch conversion
  - DatasetSelectionDialog — helper for multi-dataset .dkin files
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import xml.etree.ElementTree as ET
import queue
import csv
import copy

import runners
import parsers
import plots
import utils
import config
import widgets as widgets_mod   # ToolTip helper (avoids name collision with tkinter)
from project import ProjectManager

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ==============================================================
# SPECTRUM CREATOR
# ==============================================================
class SpectrumCreatorWindow(tk.Toplevel):
    """Create and edit spectrum loading files (.txt) within a project."""

    def __init__(self, parent, callback, pm: ProjectManager, spectrum_filename: str):
        super().__init__(parent)
        self.title("Spectrum Editor")
        self.geometry("750x650")

        self.callback = callback
        self.project = pm
        self.spectrum_filename = spectrum_filename
        self.spectrum_filepath = os.path.join(
            self.project.get_path("input"), self.spectrum_filename
        )

        self.levels_data = []
        self.level_widgets = []
        self.num_levels_var = tk.IntVar(value=0)
        self.speak_var = tk.StringVar(value="1.0")
        self.invert_var = tk.StringVar(value="0")
        self.undo_stack, self.redo_stack = [], []

        self._create_widgets()

        if os.path.exists(self.spectrum_filepath):
            self._load_spectrum_file(self.spectrum_filepath)
        else:
            if not self.levels_data:
                self.levels_data.append(['0.0', '0.0', '1'])
            self._redraw_levels_table()

        self._save_state_for_undo(clear_redo=False)
        self.transient(parent)
        self.grab_set()
        self.bind_all("<Control-z>", self._undo)
        self.bind_all("<Control-y>", self._redo)

    def _create_widgets(self):
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

        # ── Guide banner ─────────────────────────────────────────────────────
        guide = ttk.Frame(self, padding="10 8 10 4")
        guide.pack(fill='x')
        ttk.Label(guide,
                  text="Define the load spectrum as a table of (Smax, Smin, Cycles) "
                       "levels — each row is one distinct load level.  "
                       "SPEAK scales every stress value before the analysis (set to the peak "
                       "stress if you normalise to 1.0).  "
                       "INVERT=1 swaps the order of each max/min pair.  "
                       "Use  Normalize  to rescale so peak = 1, then put the real peak in SPEAK.  "
                       "Ctrl+Z / Ctrl+Y to undo/redo.",
                  foreground='#1a5fa8', font=('Segoe UI', 9, 'italic'),
                  wraplength=700, justify='left').pack(fill='x')
        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=10, pady=(4, 0))

        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill='x', padx=10, pady=5)
        top_frame.columnconfigure(1, weight=1)

        ttk.Label(top_frame, text="Spectrum Title:").grid(row=0, column=0, sticky='w', pady=2)
        self.title_entry = ttk.Entry(top_frame)
        self.title_entry.insert(0, "Custom Spectrum")
        self.title_entry.grid(row=0, column=1, columnspan=3, sticky='ew', padx=5)

        ttk.Label(top_frame, text="INVERT:").grid(row=1, column=0, sticky='w', pady=(5, 2))
        invert_e = ttk.Entry(top_frame, width=10, textvariable=self.invert_var)
        invert_e.grid(row=1, column=1, sticky='w', padx=5)
        widgets_mod.ToolTip(invert_e,
            "0 = normal (max applied first, then min).\n"
            "1 = inverted (min applied first, then max).\n"
            "Use 1 for compressive spectra or when the test machine applies loads bottom-up.")

        ttk.Label(top_frame, text="SPEAK:").grid(row=2, column=0, sticky='w', pady=(5, 2))
        speak_e = ttk.Entry(top_frame, textvariable=self.speak_var, width=10)
        speak_e.grid(row=2, column=1, sticky='w', padx=5)
        widgets_mod.ToolTip(speak_e,
            "Scale factor applied to every stress value in this spectrum.\n"
            "Example: enter normalised levels (peak = 1.0) then set SPEAK = actual peak stress.\n"
            "The plot preview reflects this scaling.")

        ttk.Button(top_frame, text="Save & Close",
                   command=self._generate_and_close).grid(row=0, column=4, sticky='ne', padx=5)

        self.output_label = ttk.Label(
            top_frame,
            text=f"File: {self.spectrum_filename} (in project input/ folder)",
            relief='sunken', anchor='w'
        )
        self.output_label.grid(row=3, column=0, columnspan=5, sticky='ew', pady=(10, 0))

        paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned.pack(fill='both', expand=True, padx=10, pady=5)

        table_container = ttk.LabelFrame(paned, text="Stress Levels", padding="10")
        paned.add(table_container, weight=1)

        ctrl = ttk.Frame(table_container)
        ctrl.pack(fill='x', pady=(0, 5))
        ttk.Label(ctrl, text="Number of Levels:").pack(side='left')
        ttk.Spinbox(ctrl, from_=0, to=500, textvariable=self.num_levels_var,
                    width=6, command=self._update_levels_from_spinbox).pack(side='left', padx=5)
        ttk.Button(ctrl, text="Import...", command=self._import_spectrum).pack(
            side='left', padx=(10, 0))
        ttk.Button(ctrl, text="Normalize", command=self._normalize_spectrum).pack(
            side='left', padx=5)
        ttk.Button(ctrl, text="Update Plot", command=self._update_plot).pack(side='left', padx=5)
        self.undo_button = ttk.Button(ctrl, text="Undo", command=self._undo, state="disabled")
        self.undo_button.pack(side='left', padx=(10, 0))
        self.redo_button = ttk.Button(ctrl, text="Redo", command=self._redo, state="disabled")
        self.redo_button.pack(side='left', padx=5)

        tbl_canvas = tk.Canvas(table_container, borderwidth=0, highlightthickness=0)
        tbl_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=tbl_canvas.yview)
        self.table_frame = ttk.Frame(tbl_canvas, padding="5")
        self.table_frame.bind(
            "<Configure>",
            lambda e: tbl_canvas.configure(scrollregion=tbl_canvas.bbox("all"))
        )
        tbl_canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        tbl_canvas.configure(yscrollcommand=tbl_scrollbar.set)
        tbl_canvas.pack(side="left", fill="both", expand=True)
        tbl_scrollbar.pack(side="right", fill="y")

        plot_container = ttk.LabelFrame(paned, text="Spectrum Plot", padding="10")
        paned.add(plot_container, weight=1)
        fig = Figure(dpi=100)
        fig.set_tight_layout(True)
        self.ax = fig.add_subplot(111)
        self.plot_canvas = FigureCanvasTkAgg(fig, master=plot_container)
        self.plot_canvas.get_tk_widget().pack(fill='both', expand=True)
        self._update_plot()

    # --- File I/O ---

    def _save_file(self):
        if not self.project.project_path:
            messagebox.showerror("Error", "No project is loaded.", parent=self)
            return False
        try:
            scale_factor = 1000.0
            title = self.title_entry.get()
            invert = int(self.invert_var.get())
            levels = []
            total_cycles, overall_smax_int, overall_smin_int = 0, -float('inf'), float('inf')
            self._sync_data_from_widgets()

            for row in self.levels_data:
                smax_f = utils.safe_float(row[0])
                smin_f = utils.safe_float(row[1])
                cycles = utils.safe_int(row[2])
                if cycles < 1:
                    continue
                smax_i = int(round(smax_f * scale_factor))
                smin_i = int(round(smin_f * scale_factor))
                levels.append({'smax': smax_i, 'smin': smin_i, 'cycles': cycles})
                total_cycles += cycles
                overall_smax_int = max(overall_smax_int, smax_i)
                overall_smin_int = min(overall_smin_int, smin_i)

            with open(self.spectrum_filepath, 'w') as f:
                f.write(f"{title}\n")
                f.write(f" {total_cycles * 2}    {overall_smax_int}    "
                        f"{overall_smin_int}    {invert}    3\n")
                line_str, col = "", 0
                for lv in levels:
                    for _ in range(lv['cycles']):
                        line_str += f"{lv['smax']:8d}"
                        col += 1
                        if col >= 10:
                            f.write(line_str + "\n")
                            line_str, col = "", 0
                        line_str += f"{lv['smin']:8d}"
                        col += 1
                        if col >= 10:
                            f.write(line_str + "\n")
                            line_str, col = "", 0
                if line_str:
                    f.write(line_str + "\n")

            messagebox.showinfo(
                "Success", f"Spectrum file '{self.spectrum_filename}' saved.", parent=self)
            if self.callback:
                self.callback(self.spectrum_filename)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not save spectrum:\n{e}", parent=self)
            return False

    def _generate_and_close(self):
        if self._save_file():
            self.destroy()

    # --- Spectrum operations ---

    def _normalize_spectrum(self):
        self._save_state_for_undo()
        self._sync_data_from_widgets()
        peak = 0.0
        for row in self.levels_data:
            try:
                peak = max(peak, abs(float(row[0])), abs(float(row[1])))
            except ValueError:
                continue
        if peak == 0:
            messagebox.showinfo("Normalize", "Cannot normalize, max stress is zero.", parent=self)
            return
        for i, row in enumerate(self.levels_data):
            try:
                self.levels_data[i][0] = f"{float(row[0]) / peak:.4g}"
                self.levels_data[i][1] = f"{float(row[1]) / peak:.4g}"
            except ValueError:
                continue
        self.speak_var.set(f"{peak:.4g}")
        self._redraw_levels_table()
        self._update_plot()

    def _update_levels_from_spinbox(self):
        self._save_state_for_undo()
        try:
            new_size = self.num_levels_var.get()
            if new_size < 0:
                return
            self._sync_data_from_widgets()
            while len(self.levels_data) < new_size:
                self.levels_data.append(['0.0', '0.0', '1'])
            if len(self.levels_data) > new_size:
                self.levels_data = self.levels_data[:new_size]
            self._redraw_levels_table()
        except tk.TclError:
            pass

    def _update_plot(self):
        self._sync_data_from_widgets()
        plots.plot_spectrum(self.ax, self.levels_data, utils.safe_float(self.speak_var.get(), 1.0))
        self.plot_canvas.draw()

    def _redraw_levels_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()
        self.level_widgets.clear()
        for i, hdr in enumerate(["Max Stress", "Min Stress", "Cycles", "Actions"]):
            ttk.Label(self.table_frame, text=hdr, font="-weight bold").grid(
                row=0, column=i, padx=5, pady=5,
                columnspan=(3 if hdr == "Actions" else 1))
        for i, row in enumerate(self.levels_data):
            smax_e = ttk.Entry(self.table_frame, width=15)
            smax_e.insert(0, row[0])
            smax_e.grid(row=i + 1, column=0, padx=5, pady=2)
            smin_e = ttk.Entry(self.table_frame, width=15)
            smin_e.insert(0, row[1])
            smin_e.grid(row=i + 1, column=1, padx=5, pady=2)
            cyc_e = ttk.Entry(self.table_frame, width=10)
            cyc_e.insert(0, row[2])
            cyc_e.grid(row=i + 1, column=2, padx=5, pady=2)
            up_btn = ttk.Button(self.table_frame, text="↑", width=3,
                                command=lambda i=i: self._move_level_up(i))
            up_btn.grid(row=i + 1, column=3, padx=(10, 2))
            dn_btn = ttk.Button(self.table_frame, text="↓", width=3,
                                command=lambda i=i: self._move_level_down(i))
            dn_btn.grid(row=i + 1, column=4, padx=2)
            del_btn = ttk.Button(self.table_frame, text="Delete", width=8,
                                 command=lambda i=i: self._delete_level(i))
            del_btn.grid(row=i + 1, column=5, padx=2)
            if i == 0:
                up_btn.config(state="disabled")
            if i == len(self.levels_data) - 1:
                dn_btn.config(state="disabled")
            self.level_widgets.append([smax_e, smin_e, cyc_e])
        self.num_levels_var.set(len(self.levels_data))

    def _sync_data_from_widgets(self):
        for i, row_w in enumerate(self.level_widgets):
            if i < len(self.levels_data):
                self.levels_data[i] = [row_w[0].get(), row_w[1].get(), row_w[2].get()]

    # --- Undo / Redo ---

    def _save_state_for_undo(self, clear_redo=True):
        self._sync_data_from_widgets()
        self.undo_stack.append(copy.deepcopy(self.levels_data))
        if clear_redo:
            self.redo_stack.clear()
        self._update_undo_redo_buttons()

    def _undo(self, event=None):
        if len(self.undo_stack) <= 1:
            return
        self.redo_stack.append(self.undo_stack.pop())
        self.levels_data = copy.deepcopy(self.undo_stack[-1])
        self._redraw_levels_table()
        self._update_plot()
        self._update_undo_redo_buttons()

    def _redo(self, event=None):
        if not self.redo_stack:
            return
        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        self.levels_data = copy.deepcopy(state)
        self._redraw_levels_table()
        self._update_plot()
        self._update_undo_redo_buttons()

    def _update_undo_redo_buttons(self):
        self.undo_button.config(state="normal" if len(self.undo_stack) > 1 else "disabled")
        self.redo_button.config(state="normal" if self.redo_stack else "disabled")

    # --- Row editing ---

    def _delete_level(self, index):
        self._save_state_for_undo()
        if 0 <= index < len(self.levels_data):
            self.levels_data.pop(index)
            self._redraw_levels_table()

    def _move_level_up(self, index):
        if index > 0:
            self._save_state_for_undo()
            self.levels_data[index], self.levels_data[index - 1] = (
                self.levels_data[index - 1], self.levels_data[index])
            self._redraw_levels_table()

    def _move_level_down(self, index):
        if index < len(self.levels_data) - 1:
            self._save_state_for_undo()
            self.levels_data[index], self.levels_data[index + 1] = (
                self.levels_data[index + 1], self.levels_data[index])
            self._redraw_levels_table()

    # --- Import ---

    def _import_spectrum(self):
        filepath = filedialog.askopenfilename(
            title="Import Spectrum File", parent=self,
            filetypes=(("Spectrum Files", "*.spx *.sub *.txt"), ("All Files", "*.*"))
        )
        if filepath:
            self._load_spectrum_file(filepath, from_import=True)

    def _load_spectrum_file(self, filepath, from_import=False):
        _, ext = os.path.splitext(filepath)
        new_data, parser_used = None, ""
        try:
            if ext.lower() == '.spx':
                new_data = self._parse_spx(filepath)
                parser_used = ".spx"
            elif ext.lower() in ['.sub', '.txt']:
                with open(filepath, 'r') as f:
                    lines = [ln.strip() for ln in f if ln.strip()]
                if not lines:
                    raise ValueError("File is empty.")
                is_std = (len(lines) > 1 and len(lines[1].split()) == 5 and
                          all(p.replace('.', '', 1).replace('-', '', 1).isdigit()
                              for p in lines[1].split()))
                if is_std:
                    new_data = self._parse_spectrum_txt(filepath)
                    parser_used = "Standard FASTRAN .txt"
                else:
                    if len(lines) <= 1:
                        raise ValueError("File contains only a title line.")
                    ncols = len(lines[1].split())
                    if ncols >= 3:
                        new_data = self._parse_sub(filepath)
                        parser_used = ".sub (3-column text)"
                    elif ncols == 1:
                        new_data = self._parse_reversal_txt(filepath)
                        parser_used = "Reversal .txt (1-column)"
                    else:
                        messagebox.showwarning("Warning", "Unrecognized text format.", parent=self)
                        new_data = self._parse_spectrum_txt(filepath)
                        parser_used = "Paired .txt"
            if new_data is not None:
                if from_import:
                    self._save_state_for_undo()
                self.levels_data = new_data
                self._redraw_levels_table()
                self._update_plot()
                if from_import:
                    messagebox.showinfo(
                        "Import Success",
                        f"Imported {len(new_data)} levels using {parser_used} parser.",
                        parent=self)
            else:
                raise ValueError("Could not parse file.")
        except Exception as e:
            messagebox.showerror("File Load Error",
                                 f"Could not load spectrum file.\nError: {e}", parent=self)

    def _parse_reversal_txt(self, filepath):
        with open(filepath, 'r') as f:
            lines = f.readlines()
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, lines[0].strip())
        self.speak_var.set("1.0")
        self.invert_var.set("0")
        pts = [float(p) for ln in lines[1:] for p in ln.split()]
        if len(pts) < 2:
            return []
        pairs = [[max(pts[i], pts[i+1]), min(pts[i], pts[i+1])]
                 for i in range(len(pts) - 1)]
        counts = {}
        for p in pairs:
            counts[tuple(p)] = counts.get(tuple(p), 0) + 1
        return [[f"{p[0]:.4g}", f"{p[1]:.4g}", str(c)] for p, c in counts.items()]

    def _parse_spectrum_txt(self, filepath):
        with open(filepath, 'r') as f:
            lines = f.readlines()
        if len(lines) < 2:
            return None
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, lines[0].strip())
        hp = lines[1].strip().split()
        if len(hp) >= 5:
            self.invert_var.set(hp[3])
            self.speak_var.set("1.0")
        body = "".join(ln.strip('\n\r') for ln in lines[2:])
        try:
            pts = [float(body[i:i+8]) for i in range(0, len(body), 8)
                   if body[i:i+8].strip()]
        except (ValueError, IndexError):
            pts = [float(p) for p in body.split()]
        if not pts:
            return []
        if len(pts) % 2 != 0:
            pts.pop()
        pairs = [[pts[i], pts[i+1]] for i in range(0, len(pts), 2)]
        levels = []
        if not pairs:
            return []
        cur_mx, cur_mn, cur_c = pairs[0][0], pairs[0][1], 1
        for nx, nn in pairs[1:]:
            if abs(nx - cur_mx) < 1e-9 and abs(nn - cur_mn) < 1e-9:
                cur_c += 1
            else:
                levels.append([f"{cur_mx:.4g}", f"{cur_mn:.4g}", str(cur_c)])
                cur_mx, cur_mn, cur_c = nx, nn, 1
        levels.append([f"{cur_mx:.4g}", f"{cur_mn:.4g}", str(cur_c)])
        return levels

    def _parse_spx(self, filepath):
        root = ET.parse(filepath).getroot()
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, root.findtext('Title', ''))
        self.speak_var.set("1.0")
        self.invert_var.set("0")
        levels = []
        sub = root.find('.//SubSpectrum')
        if sub is not None:
            for b in sub.findall('B'):
                levels.append([b.get('Mx', '0.0'), b.get('Mn', '0.0'), b.get('C', '1')])
        return levels

    def _parse_sub(self, filepath):
        with open(filepath, 'r') as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, lines[0].strip())
        self.speak_var.set("1.0")
        self.invert_var.set("0")
        return [ln.split()[:3] for ln in lines[1:] if len(ln.split()) >= 3]


# ==============================================================
# POST-PROCESSING WINDOW (single-run results dashboard)
# ==============================================================
class PostProcessingWindow(tk.Toplevel):
    """Displays input summary, crack-growth plot, and final results for one run."""

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
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        fm = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=fm)
        fm.add_command(label="Save Results As CSV...", command=self._save_parsed_results)
        fm.add_command(label="Export Plot...", command=self._export_plot)
        fm.add_separator()
        fm.add_command(label="Close", command=self.destroy)

        # ── Guide banner ─────────────────────────────────────────────────────
        guide = ttk.Frame(self, padding="10 6 10 4")
        guide.pack(fill='x')
        ttk.Label(guide,
                  text="Post-processor: review FASTRAN output data from the last run.  "
                       "Select any two columns for the X and Y axes using the dropdowns below "
                       "the plot — typical view is Cycles (X) vs crack size (Y).  "
                       "Enable log scale checkboxes for da/dN or crack-growth plots.  "
                       "Use  File → Save Results As CSV  to export the full output table.",
                  foreground='#1a5fa8', font=('Segoe UI', 9, 'italic'),
                  wraplength=960, justify='left').pack(fill='x')
        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=10, pady=(4, 0))

        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill='both', expand=True, padx=10, pady=5)

        summary_frame = ttk.LabelFrame(main_pane, text="Input Summary", padding=10)
        main_pane.add(summary_frame, weight=1)
        self.summary_tree = ttk.Treeview(
            summary_frame, columns=('Parameter', 'Value'), show='headings', height=8)
        self.summary_tree.heading('Parameter', text='Parameter')
        self.summary_tree.heading('Value', text='Value')
        self.summary_tree.column('Parameter', width=150, anchor='w')
        self.summary_tree.column('Value', width=100, anchor='w')
        self.summary_tree.pack(fill='both', expand=True)

        plot_area = ttk.Frame(main_pane)
        main_pane.add(plot_area, weight=3)

        ctrl = ttk.Frame(plot_area, padding=5)
        ctrl.pack(fill='x', pady=5)
        ttk.Label(ctrl, text="Y-Axis:").pack(side='left', padx=(0, 5))
        self.y_axis_combo = ttk.Combobox(ctrl, textvariable=self.y_axis_var,
                                          state='readonly', width=15)
        self.y_axis_combo.pack(side='left')
        self.y_axis_combo.bind("<<ComboboxSelected>>", self._draw_custom_plot)
        widgets_mod.ToolTip(self.y_axis_combo,
            "Choose the output column to plot on the Y-axis.\n"
            "Common choices: crack size C, stress intensity K, closure level So.")
        ttk.Checkbutton(ctrl, text="log", variable=self.log_y_var,
                        command=self._draw_custom_plot).pack(side='left', padx=5)
        ttk.Label(ctrl, text="X-Axis:").pack(side='left', padx=(20, 5))
        self.x_axis_combo = ttk.Combobox(ctrl, textvariable=self.x_axis_var,
                                          state='readonly', width=15)
        self.x_axis_combo.pack(side='left')
        self.x_axis_combo.bind("<<ComboboxSelected>>", self._draw_custom_plot)
        widgets_mod.ToolTip(self.x_axis_combo,
            "Choose the output column to plot on the X-axis.\n"
            "CYCLES is the most common choice for a crack-growth life plot.")
        ttk.Checkbutton(ctrl, text="log", variable=self.log_x_var,
                        command=self._draw_custom_plot).pack(side='left', padx=5)

        plot_canvas_frame = ttk.Frame(plot_area)
        plot_canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)
        fig = Figure(dpi=100)
        fig.set_tight_layout(True)
        self.ax = fig.add_subplot(111)
        self.plot_canvas = FigureCanvasTkAgg(fig, master=plot_canvas_frame)
        self.plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        results_frame = ttk.LabelFrame(self, text="Final Results", padding=10)
        results_frame.pack(fill='x', padx=10, pady=(0, 10))
        failure_code = self.summary_dict.get('failure_code')
        failure_desc = config.FAILURE_MODES.get(
            failure_code, self.summary_dict.get('failure_reason', 'N/A'))
        ttk.Label(
            results_frame,
            text=(f"Total Cycles: {self.summary_dict.get('total_cycles', 'N/A')}\n"
                  f"Failure Mode: {failure_desc}"),
            justify=tk.LEFT
        ).pack(anchor='w')

    def _populate_summary_tree(self):
        for param, value in self.input_params.items():
            self.summary_tree.insert('', tk.END, values=(param, value))

    def _populate_controls(self):
        self.x_axis_combo.config(values=self.header)
        self.y_axis_combo.config(values=self.header)
        if 'CYCLES' in self.header:
            self.x_axis_var.set('CYCLES')
        if self.header:
            self.y_axis_var.set(self.header[-1] if 'C_crack' not in self.header
                                else 'C_crack')
        self._draw_custom_plot()

    def _draw_custom_plot(self, event=None):
        try:
            plots.plot_post_processing(
                self.ax, self.header, self.data,
                self.x_axis_var.get(), self.y_axis_var.get(),
                self.log_x_var.get(), self.log_y_var.get()
            )
            self.plot_canvas.draw()
        except Exception as e:
            messagebox.showerror("Plotting Error", f"Could not create plot:\n{e}", parent=self)

    def _export_plot(self):
        fp = filedialog.asksaveasfilename(
            title="Export Plot As", parent=self,
            filetypes=(("PNG Image", "*.png"), ("SVG", "*.svg"), ("PDF", "*.pdf")),
            defaultextension=".png"
        )
        if not fp:
            return
        try:
            self.ax.get_figure().savefig(fp, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Success",
                                f"Plot exported to:\n{os.path.basename(fp)}", parent=self)
        except Exception as e:
            messagebox.showerror("Export Error", str(e), parent=self)

    def _save_parsed_results(self):
        sp = filedialog.asksaveasfilename(
            title="Save Results As", parent=self,
            defaultextension=".csv",
            filetypes=(("CSV File", "*.csv"), ("All Files", "*.*"))
        )
        if not sp:
            return
        try:
            with open(sp, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.header)
                writer.writerows(self.data)
            messagebox.showinfo("Success",
                                f"Saved to:\n{os.path.basename(sp)}", parent=self)
        except Exception as e:
            messagebox.showerror("Save Error", str(e), parent=self)


# ==============================================================
# BLOCK LOADING EDITOR (NFOPT=1)
# ==============================================================
class BlockEditorWindow(tk.Toplevel):
    """Variable-amplitude block loading editor for NFOPT=1."""

    def __init__(self, parent, callback, initial_data, initial_params):
        super().__init__(parent)
        self.title("Block Loading Editor (NFOPT=1)")
        self.geometry("850x650")
        self.callback = callback
        self.blocks = (copy.deepcopy(initial_data)
                       if initial_data
                       else [{'nsq': '1', 'levels': [['0.0', '0.0', '1']]}])
        self.current_block_index = 0
        self.param_vars = {
            k: tk.StringVar(value=initial_params.get(k, '0'))
            for k in ['MAXSEQ', 'MAXBLK', 'LPRINT', 'MAXLPR']
        }
        self.param_vars['SCALE'] = tk.StringVar(value=initial_params.get('SCALE', '1.0'))
        self.param_vars['MAXSEQ'].set(str(len(self.blocks)))
        self._create_widgets()
        self._populate_block_listbox()
        self.transient(parent)
        self.grab_set()

    _BLOCK_PARAM_TIPS = {
        'MAXSEQ': "Number of blocks in the sequence (set automatically).",
        'MAXBLK': "Number of times the entire block sequence is repeated.\n"
                  "Total load cycles = (cycles per sequence) × MAXBLK.",
        'SCALE':  "Multiplies every stress value in every block before the run.\n"
                  "Use this to apply a stress-level factor without editing individual blocks.",
        'LPRINT': "Output verbosity flag passed to FASTRAN.\n0 = normal; 1 = extra output.",
        'MAXLPR': "Maximum number of print lines per block (0 = no limit).",
    }

    def _create_widgets(self):
        bot = ttk.Frame(self, padding=10)
        bot.pack(side="bottom", fill="x")
        ttk.Button(bot, text="Save & Close", command=self._save_and_close).pack(side="right")

        # ── Guide banner ─────────────────────────────────────────────────────
        guide = ttk.Frame(self, padding="10 8 10 4")
        guide.pack(side="top", fill='x')
        ttk.Label(guide,
                  text="NFOPT=1 block loading: define a sequence of load blocks, "
                       "each containing one or more (Smax, Smin, Cycles) levels.  "
                       "The entire sequence is repeated MAXBLK times.  "
                       "Select a block on the left to edit its stress levels on the right.  "
                       "SCALE multiplies every stress value in every block.",
                  foreground='#1a5fa8', font=('Segoe UI', 9, 'italic'),
                  wraplength=800, justify='left').pack(fill='x')
        ttk.Separator(self, orient='horizontal').pack(side="top", fill='x', padx=10, pady=(4, 0))

        params_lf = ttk.LabelFrame(self, text="Global Loading Parameters", padding=10)
        params_lf.pack(side="top", fill="x", padx=10, pady=5)
        for i, label in enumerate(["MAXSEQ:", "MAXBLK:", "SCALE:", "LPRINT:", "MAXLPR:"]):
            key = label.rstrip(':')
            ttk.Label(params_lf, text=label).grid(
                row=i // 3, column=(i % 3) * 2, sticky='w', padx=5, pady=2)
            e = ttk.Entry(params_lf, textvariable=self.param_vars[key], width=10)
            if label == "MAXSEQ:":
                e.config(state='disabled')
            e.grid(row=i // 3, column=(i % 3) * 2 + 1, sticky='w', padx=5)
            tip = self._BLOCK_PARAM_TIPS.get(key)
            if tip:
                widgets_mod.ToolTip(e, tip)

        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill='both', expand=True, padx=10, pady=(10, 0))

        left = ttk.Frame(paned, padding=5)
        paned.add(left, weight=1)

        list_frame = ttk.LabelFrame(left, text="Block Sequence")
        list_frame.pack(fill='both', expand=True)
        self.block_listbox = tk.Listbox(list_frame, exportselection=False)
        self.block_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        self.block_listbox.bind('<<ListboxSelect>>', self._on_block_select)

        lctrl = ttk.Frame(left)
        lctrl.pack(fill='x', pady=5)
        for text, cmd in [("Add Block", self._add_block),
                          ("Delete Block", self._delete_block),
                          ("Move Up ↑", self._move_block_up),
                          ("Move Down ↓", self._move_block_down)]:
            ttk.Button(lctrl, text=text, command=cmd).pack(
                side='left', expand=True, fill='x', padx=2)

        self.right_pane = ttk.Frame(paned, padding=10)
        paned.add(self.right_pane, weight=3)

    def _populate_block_listbox(self):
        sel = self.block_listbox.curselection()
        sel_idx = sel[0] if sel else self.current_block_index
        self.block_listbox.delete(0, tk.END)
        for i, b in enumerate(self.blocks):
            self.block_listbox.insert(
                tk.END,
                f"Block {i+1} (NSL={len(b.get('levels',[]))}, Reps={b.get('nsq',1)})")
        new_idx = min(sel_idx, len(self.blocks) - 1)
        if new_idx >= 0:
            self.block_listbox.selection_set(new_idx)
            self.block_listbox.activate(new_idx)
            self.block_listbox.see(new_idx)
        self.param_vars['MAXSEQ'].set(str(len(self.blocks)))
        self._on_block_select()

    def _on_block_select(self, event=None):
        if not self.block_listbox.curselection():
            if not self.blocks:
                for w in self.right_pane.winfo_children():
                    w.destroy()
                ttk.Label(self.right_pane, text="No Block Selected").pack()
                return
            else:
                self.block_listbox.selection_set(0)
        new_idx = self.block_listbox.curselection()[0]
        self._sync_data_from_widgets()
        self.current_block_index = new_idx
        for w in self.right_pane.winfo_children():
            w.destroy()

        props = ttk.LabelFrame(
            self.right_pane, text=f"Block {self.current_block_index + 1} Properties", padding=5)
        props.pack(fill='x')
        self.nsq_var = tk.StringVar(value=self.blocks[self.current_block_index].get('nsq', '1'))
        ttk.Label(props, text="Block Repetitions (NSQ):").grid(row=0, column=0, sticky='w', padx=5)
        ttk.Entry(props, textvariable=self.nsq_var, width=10).grid(row=0, column=1, sticky='w')
        self.nsl_label = ttk.Label(props, text="")
        self.nsl_label.grid(row=0, column=2, sticky='w', padx=20)

        levels_frame = ttk.LabelFrame(self.right_pane, text="Stress Levels in Block", padding=5)
        levels_frame.pack(fill='both', expand=True, pady=5)
        ttk.Button(levels_frame, text="Add Level",
                   command=self._add_block_level).pack(anchor='w', pady=(0, 5))

        canvas = tk.Canvas(levels_frame, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(levels_frame, orient="vertical", command=canvas.yview)
        self.table_frame = ttk.Frame(canvas, padding="5")
        self.table_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._redraw_block_levels_table()

    def _update_nsl_display(self):
        if hasattr(self, 'nsl_label') and self.blocks:
            self.nsl_label.config(
                text=f"NSL: {len(self.blocks[self.current_block_index]['levels'])}")

    def _redraw_block_levels_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()
        self.level_widgets = []
        if not self.blocks:
            return
        block_levels = self.blocks[self.current_block_index]['levels']
        for i, hdr in enumerate(["Max Stress", "Min Stress", "Cycles", "Actions"]):
            ttk.Label(self.table_frame, text=hdr, font="-weight bold").grid(
                row=0, column=i, padx=5, pady=2,
                columnspan=(3 if hdr == "Actions" else 1))
        for i, row in enumerate(block_levels):
            smax_e = ttk.Entry(self.table_frame, width=15)
            smax_e.insert(0, row[0])
            smax_e.grid(row=i + 1, column=0, padx=5, pady=2)
            smin_e = ttk.Entry(self.table_frame, width=15)
            smin_e.insert(0, row[1])
            smin_e.grid(row=i + 1, column=1, padx=5, pady=2)
            cyc_e = ttk.Entry(self.table_frame, width=10)
            cyc_e.insert(0, row[2])
            cyc_e.grid(row=i + 1, column=2, padx=5, pady=2)
            up_btn = ttk.Button(self.table_frame, text="↑", width=3,
                                command=lambda i=i: self._move_block_level(i, -1))
            up_btn.grid(row=i + 1, column=3, padx=(10, 2))
            dn_btn = ttk.Button(self.table_frame, text="↓", width=3,
                                command=lambda i=i: self._move_block_level(i, 1))
            dn_btn.grid(row=i + 1, column=4, padx=2)
            del_btn = ttk.Button(self.table_frame, text="Delete", width=8,
                                 command=lambda i=i: self._delete_block_level(i))
            del_btn.grid(row=i + 1, column=5, padx=2)
            if i == 0:
                up_btn.config(state="disabled")
            if i == len(block_levels) - 1:
                dn_btn.config(state="disabled")
            self.level_widgets.append([smax_e, smin_e, cyc_e])
        self._update_nsl_display()

    def _sync_data_from_widgets(self):
        if not hasattr(self, 'nsq_var') or not self.blocks:
            return
        bd = self.blocks[self.current_block_index]
        bd['nsq'] = self.nsq_var.get()
        bd['levels'] = [[w.get() for w in row_w] for row_w in self.level_widgets]

    def _add_block_level(self):
        self._sync_data_from_widgets()
        self.blocks[self.current_block_index]['levels'].append(['0.0', '0.0', '1'])
        self._redraw_block_levels_table()
        self._populate_block_listbox()

    def _delete_block_level(self, index):
        self._sync_data_from_widgets()
        levels = self.blocks[self.current_block_index]['levels']
        if len(levels) > 1:
            levels.pop(index)
        else:
            messagebox.showwarning("Warning", "A block must have at least one level.", parent=self)
        self._redraw_block_levels_table()
        self._populate_block_listbox()

    def _move_block_level(self, index, direction):
        self._sync_data_from_widgets()
        levels = self.blocks[self.current_block_index]['levels']
        new_idx = index + direction
        if 0 <= new_idx < len(levels):
            levels[index], levels[new_idx] = levels[new_idx], levels[index]
        self._redraw_block_levels_table()

    def _add_block(self):
        self._sync_data_from_widgets()
        self.blocks.append({'nsq': '1', 'levels': [['0.0', '0.0', '1']]})
        self._populate_block_listbox()
        self.block_listbox.selection_set(tk.END)

    def _delete_block(self):
        if not self.block_listbox.curselection() or len(self.blocks) <= 1:
            return
        self.blocks.pop(self.block_listbox.curselection()[0])
        self.current_block_index = 0
        self._populate_block_listbox()

    def _move_block(self, direction):
        if not self.block_listbox.curselection():
            return
        idx = self.block_listbox.curselection()[0]
        new_idx = idx + direction
        if 0 <= new_idx < len(self.blocks):
            self._sync_data_from_widgets()
            self.blocks[idx], self.blocks[new_idx] = self.blocks[new_idx], self.blocks[idx]
            self._populate_block_listbox()
            self.block_listbox.selection_set(new_idx)

    def _move_block_up(self):
        self._move_block(-1)

    def _move_block_down(self):
        self._move_block(1)

    def _save_and_close(self):
        self._sync_data_from_widgets()
        if self.callback:
            self.callback({
                'params': {k: v.get() for k, v in self.param_vars.items()},
                'blocks': self.blocks
            })
        self.destroy()


# ==============================================================
# DKEFF MATERIAL DATA GENERATOR
# ==============================================================
class DkeffWindow(tk.Toplevel):
    """
    GUI front-end for the DKEFF utility.
    Supports dkeff13 (legacy) and dkeff21f (new) with version-specific
    stdin protocols for the external executable.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Material Data Generator (dkeff)")
        self.geometry("850x700")

        self.parent = parent
        self.dkeff_input_path = None
        self.dkeff_output_path = None
        self.processed_data = []
        self.dkeff_queue = queue.Queue()

        self.lunit_map = {
            "Keep Same Units": '0',
            "Input: English → Output: SI": '1',
            "Input: SI → Output: English": '2',
        }
        self.ntyp_map = {
            "Middle-crack tension": '1',
            "Compact C(T)": '2',
            "ESE(T)": '3',
        }
        self.ntyp_rev_map = {v: k for k, v in self.ntyp_map.items()}
        self.nsop_map = {
            "Calculate c (NSOP=0)": '0',
            "Input c (NSOP=1)": '1',
            "Input So/Smax (NSOP=2)": '2',
        }
        self.nsop_rev_map = {v: k for k, v in self.nsop_map.items()}
        self.test_type_map = {"Constant R test": '0', "Kmax test": '1'}

        self.ntyp_var = tk.StringVar(value="Compact C(T)")
        self.nsop_var = tk.StringVar(value="Input c (NSOP=1)")
        self.nsop_var.trace_add('write', self._update_nsop_widgets)
        self.test_type_var = tk.StringVar(value="Kmax test")
        self.test_type_var.trace_add('write', self._update_test_type_widgets)
        self.output_filename_var = tk.StringVar(value="output.dkout")
        self.r_var = tk.StringVar(value="0.1")
        self.smax_var = tk.StringVar(value="7.5")
        self.dkeff_version_var = tk.StringVar(value="dkeff13 (Legacy)")

        self._create_widgets()
        self._update_test_type_widgets()
        self.transient(parent)
        self.grab_set()

    def _create_widgets(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        fm = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=fm)
        fm.add_command(label="Batch Convert .lkpx File...",
                       command=self._batch_convert_lkpx)
        fm.add_command(label="Import .lkpx Direct to Main Window...",
                       command=self._import_lkpx_direct)
        fm.add_separator()
        fm.add_command(label="Load dkeff Input File...", command=self._load_dkeff_input_file)
        fm.add_separator()
        fm.add_command(label="Save Input File As...", command=self._save_dkeff_file_as)
        fm.add_separator()
        fm.add_command(label="Close", command=self.destroy)

        # ── Workflow guide banner ────────────────────────────────────────────
        guide_frame = ttk.Frame(self, padding="10 8 10 4")
        guide_frame.pack(fill='x')
        guide_text = (
            "Purpose: convert raw lab crack-growth data (ΔK, da/dN) into effective-ΔK "
            "values by applying Newman's crack-closure model.\n"
            "Workflow:  ① Enter material properties & specimen dimensions on the left.  "
            "② Paste measured ΔK / da/dN rows into the table on the right.  "
            "③ Click Generate dKeff Data.  ④ Click Apply to Main Window.\n"
            "Shortcut: if your data is already on a ΔKeff basis (e.g. from the AFMAT "
            "database), use  File → Import .lkpx Direct to Main Window  — no dkeff run needed."
        )
        ttk.Label(guide_frame, text=guide_text, foreground='#1a5fa8',
                  font=('Segoe UI', 9, 'italic'), wraplength=820,
                  justify='left').pack(fill='x')
        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=10, pady=(0, 4))

        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill='both', expand=True, padx=10, pady=5)

        params_frame = ttk.Frame(paned, padding="10")
        paned.add(params_frame, weight=2)

        self.input_file_label = ttk.Label(
            params_frame, text="Input File: None", relief="sunken", anchor="w", padding=2)
        self.input_file_label.pack(fill='x', pady=(0, 6))

        # ── Material properties ──────────────────────────────────────────────
        mat_lf = ttk.LabelFrame(params_frame, text="① Material Properties", padding="10")
        mat_lf.pack(fill='x', pady=4)
        mat_fields = [
            ("Yield Stress (MPa):",     "syield_entry",
             "Yield stress Sy (0.2 % offset).  Must be less than ultimate strength."),
            ("Ultimate Strength (MPa):", "sult_entry",
             "Ultimate tensile strength Su."),
            ("Elastic Modulus (MPa):",   "e_entry",
             "Young's modulus E.  Typical aluminium: 70 000 MPa.  Steel: 210 000 MPa."),
        ]
        for i, (lbl, attr, tip) in enumerate(mat_fields):
            ttk.Label(mat_lf, text=lbl).grid(row=i, column=0, sticky='w', pady=2)
            e = ttk.Entry(mat_lf)
            e.grid(row=i, column=1, sticky='ew', padx=5)
            setattr(self, attr, e)
            widgets_mod.ToolTip(e, tip)
        mat_lf.columnconfigure(1, weight=1)

        # ── Test & analysis parameters ───────────────────────────────────────
        analysis_lf = ttk.LabelFrame(
            params_frame, text="② Specimen & Test Parameters", padding="10")
        analysis_lf.pack(fill='x', pady=4)

        ttk.Label(analysis_lf, text="Specimen Type (NTYP):").grid(row=0, column=0, sticky='w')
        self.ntyp_combo = ttk.Combobox(
            analysis_lf, textvariable=self.ntyp_var,
            state='readonly', values=list(self.ntyp_map.keys()))
        self.ntyp_combo.current(1)
        self.ntyp_combo.grid(row=0, column=1, sticky='ew', padx=5)
        widgets_mod.ToolTip(self.ntyp_combo,
            "1 = Middle-crack tension M(T)\n"
            "2 = Compact tension C(T)\n"
            "3 = Eccentrically-loaded single-edge ESE(T)")

        ttk.Label(analysis_lf, text="dkeff Version:").grid(row=1, column=0, sticky='w')
        self.dkeff_version_combo = ttk.Combobox(
            analysis_lf, textvariable=self.dkeff_version_var,
            state='readonly', values=["dkeff13 (Legacy)", "dkeff21f (New)"])
        self.dkeff_version_combo.grid(row=1, column=1, sticky='ew', padx=5)
        widgets_mod.ToolTip(self.dkeff_version_combo,
            "dkeff13: older executable, widely tested.\n"
            "dkeff21f: updated version with additional output.\n"
            "Configure paths via  File → Configure Executable Paths  in the main window.")

        ttk.Label(analysis_lf, text="Test Type:").grid(row=2, column=0, sticky='w')
        self.test_type_combo = ttk.Combobox(
            analysis_lf, textvariable=self.test_type_var,
            state='readonly', values=list(self.test_type_map.keys()))
        self.test_type_combo.grid(row=2, column=1, sticky='ew', padx=5)
        widgets_mod.ToolTip(self.test_type_combo,
            "Constant R: specify stress ratio R and Smax for each dataset.\n"
            "Kmax: specify Kmax directly (use when R was varied to hold Kmax constant).")

        ttk.Label(analysis_lf, text="Analysis Mode (NSOP):").grid(row=3, column=0, sticky='w')
        self.nsop_combo = ttk.Combobox(
            analysis_lf, textvariable=self.nsop_var,
            state='readonly', values=list(self.nsop_map.keys()))
        self.nsop_combo.grid(row=3, column=1, sticky='ew', padx=5)
        widgets_mod.ToolTip(self.nsop_combo,
            "NSOP=0 (Calculate c): dkeff computes crack length internally — "
            "use this when specimen geometry is unknown (e.g. AFMAT/database data).\n"
            "NSOP=1 (Input c): you supply measured crack length alongside ΔK and da/dN.\n"
            "NSOP=2 (Input So/Smax): supply crack-opening-stress ratio instead of c.")

        self.kmax_lbl = ttk.Label(analysis_lf, text="Kmax (MPa√m):")
        self.kmax_lbl.grid(row=4, column=0, sticky='w')
        self.kmax_entry = ttk.Entry(analysis_lf)
        self.kmax_entry.grid(row=4, column=1, sticky='ew', padx=5)
        widgets_mod.ToolTip(self.kmax_entry, "Maximum stress-intensity factor for a Kmax test.")

        self.r_lbl = ttk.Label(analysis_lf, text="Stress Ratio (R):")
        self.r_lbl.grid(row=5, column=0, sticky='w')
        self.r_entry = ttk.Entry(analysis_lf, textvariable=self.r_var)
        self.r_entry.grid(row=5, column=1, sticky='ew', padx=5)
        widgets_mod.ToolTip(self.r_entry,
            "Stress ratio R = Smin / Smax.  Range: −1 ≤ R < 1.  "
            "Typical tension-tension tests: R = 0.1.")

        self.smax_lbl = ttk.Label(analysis_lf, text="Smax (MPa):")
        self.smax_lbl.grid(row=6, column=0, sticky='w')
        self.smax_entry = ttk.Entry(analysis_lf, textvariable=self.smax_var)
        self.smax_entry.grid(row=6, column=1, sticky='ew', padx=5)
        widgets_mod.ToolTip(self.smax_entry, "Maximum gross-section stress applied during the test.")

        ttk.Label(analysis_lf, text="Specimen Width W (mm):").grid(row=7, column=0, sticky='w')
        self.w_entry = ttk.Entry(analysis_lf)
        self.w_entry.grid(row=7, column=1, sticky='ew', padx=5)
        widgets_mod.ToolTip(self.w_entry,
            "Half-width for M(T); full width for C(T)/ESE(T).  Units match LUNIT setting.")

        ttk.Label(analysis_lf, text="Specimen Thickness T (mm):").grid(row=8, column=0, sticky='w')
        self.t_entry = ttk.Entry(analysis_lf)
        self.t_entry.grid(row=8, column=1, sticky='ew', padx=5)
        widgets_mod.ToolTip(self.t_entry, "Net specimen thickness (after side-grooving if any).")

        ttk.Label(analysis_lf, text="Constraint Factor (ALP):").grid(row=9, column=0, sticky='w')
        self.alp_entry = ttk.Entry(analysis_lf)
        self.alp_entry.grid(row=9, column=1, sticky='ew', padx=5)
        widgets_mod.ToolTip(self.alp_entry,
            "Plane-stress/strain constraint factor.\n"
            "1.0 = plane stress (thin sheet).\n"
            "~2.5–3.0 = plane strain (thick specimen).\n"
            "Use the Specimen Preset dropdown below for standard ASTM E647 values.")

        ttk.Label(analysis_lf, text="Unit Conversion (LUNIT):").grid(row=10, column=0, sticky='w')
        self.lunit_combo = ttk.Combobox(
            analysis_lf, state='readonly', values=list(self.lunit_map.keys()))
        self.lunit_combo.current(0)
        self.lunit_combo.grid(row=10, column=1, sticky='ew', padx=5)
        widgets_mod.ToolTip(self.lunit_combo,
            "Controls unit conversion applied to the dkeff output before the run.\n"
            "FASTRAN expects SI (MPa, mm, m/cycle) — choose the conversion that "
            "matches your lab data units.")

        ttk.Separator(analysis_lf, orient='horizontal').grid(
            row=11, column=0, columnspan=2, sticky='ew', pady=(8, 4))

        ttk.Label(analysis_lf, text="Specimen Preset:").grid(row=12, column=0, sticky='w')
        preset_frame = ttk.Frame(analysis_lf)
        preset_frame.grid(row=12, column=1, sticky='ew', padx=5)
        self.preset_var = tk.StringVar(value="— select preset —")
        self.preset_combo = ttk.Combobox(
            preset_frame, textvariable=self.preset_var,
            state='readonly', values=list(config.DKEFF_SPECIMEN_PRESETS.keys()), width=22)
        self.preset_combo.pack(side='left', fill='x', expand=True)
        ttk.Button(preset_frame, text="Apply", command=self._apply_preset).pack(
            side='left', padx=(4, 0))
        widgets_mod.ToolTip(self.preset_combo,
            "Fill W, T, and ALP automatically from standard ASTM E647 specimen sizes.\n"
            "Select a preset then click Apply.")

        analysis_lf.columnconfigure(1, weight=1)

        # ── Lab data table ───────────────────────────────────────────────────
        tbl_container = ttk.Frame(paned, padding="5")
        paned.add(tbl_container, weight=3)
        tbl_lf = ttk.LabelFrame(
            tbl_container,
            text="③ Lab Data — ΔK (MPa√m) / da/dN (m/cycle) / c (mm, if NSOP=1)",
            padding="10")
        tbl_lf.pack(fill='both', expand=True)
        ttk.Label(tbl_lf,
                  text="Enter one measured data point per row, in ascending ΔK order.  "
                       "ΔK = stress-intensity-factor range; da/dN = crack growth rate; "
                       "c = half-crack length at that data point (only needed for NSOP=1).",
                  foreground='#444', font=('Segoe UI', 8, 'italic'),
                  wraplength=440, justify='left').pack(anchor='w', pady=(0, 6))
        grid_canvas = tk.Canvas(tbl_lf, borderwidth=0, highlightthickness=0)
        tbl_scrollbar = ttk.Scrollbar(tbl_lf, orient="vertical", command=grid_canvas.yview)
        self.grid_frame = ttk.Frame(grid_canvas)
        self.grid_frame.bind(
            "<Configure>",
            lambda e: grid_canvas.configure(scrollregion=grid_canvas.bbox("all")))
        grid_canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        grid_canvas.configure(yscrollcommand=tbl_scrollbar.set)
        grid_canvas.pack(side="left", fill="both", expand=True)
        tbl_scrollbar.pack(side="right", fill="y")
        self.grid_widgets = []

        # Output viewer — hidden until a run completes.
        # Must be packed (side='bottom') AFTER bot so it sits above bot in the layout.
        self.out_lf = ttk.LabelFrame(self, text="dkeff Output", padding="5")
        out_text_frame = ttk.Frame(self.out_lf)
        out_text_frame.pack(fill='both', expand=True)
        self.out_text = tk.Text(out_text_frame, height=8, wrap='none',
                                font=('Courier', 8), state='disabled')
        out_xsb = ttk.Scrollbar(out_text_frame, orient='horizontal',
                                 command=self.out_text.xview)
        out_ysb = ttk.Scrollbar(out_text_frame, orient='vertical',
                                 command=self.out_text.yview)
        self.out_text.configure(xscrollcommand=out_xsb.set,
                                yscrollcommand=out_ysb.set)
        self.out_text.grid(row=0, column=0, sticky='nsew')
        out_ysb.grid(row=0, column=1, sticky='ns')
        out_xsb.grid(row=1, column=0, sticky='ew')
        out_text_frame.rowconfigure(0, weight=1)
        out_text_frame.columnconfigure(0, weight=1)

        self.bot_frame = ttk.Frame(self, padding="10")
        self.bot_frame.pack(fill='x', side='bottom')
        # Prime out_lf position in the pack list (above bot_frame), then hide it.
        self.out_lf.pack(fill='x', side='bottom', padx=10, pady=(0, 5))
        self.out_lf.pack_forget()

        bot = self.bot_frame
        self.status_label = ttk.Label(
            bot,
            text="Ready.  Fill in material properties and lab data, then click "
                 "Generate dKeff Data  (step ③ → ④).")
        self.status_label.pack(side='top', fill='x', pady=(0, 5))
        ctrl = ttk.Frame(bot)
        ctrl.pack(side='top', fill='x')
        ttk.Label(ctrl, text="Output Filename:").pack(side='left', padx=(0, 5))
        ttk.Entry(ctrl, textvariable=self.output_filename_var).pack(
            side='left', fill='x', expand=True)
        widgets_mod.ToolTip(
            ttk.Entry(ctrl),   # dummy — real tooltip on the entry below
            "Name of the .dkout file written by the dkeff executable.")
        btn_validate = ttk.Button(ctrl, text="Validate Data",
                                  command=self._validate_grid_data)
        btn_validate.pack(side='left', padx=5)
        widgets_mod.ToolTip(btn_validate,
            "Check that ΔK and da/dN values are numeric and strictly ascending.  "
            "Rows with errors are highlighted in red.")
        self.generate_button = ttk.Button(
            ctrl, text="③ Generate dKeff Data", command=self._run_dkeff)
        self.generate_button.pack(side='left', padx=5)
        widgets_mod.ToolTip(self.generate_button,
            "Run the dkeff executable to apply Newman's closure correction.\n"
            "The corrected ΔKeff vs da/dN data will appear in the output panel below.\n"
            "Requires the dkeff executable path set via  File → Configure Executable Paths.")
        self.apply_button = ttk.Button(
            ctrl, text="④ Apply to Main Window", command=self._apply_to_main, state='disabled')
        self.apply_button.pack(side='left', padx=5)
        widgets_mod.ToolTip(self.apply_button,
            "Copy the corrected ΔKeff / da/dN table into the main window's "
            "Crack Growth tab (sets NTAB and CGR_TABLE).  "
            "Also transfers Sy, Su, E, and ALP back to the Material tab.")
        ttk.Button(ctrl, text="Close", command=self.destroy).pack(side='right')

    def _apply_preset(self):
        preset = config.DKEFF_SPECIMEN_PRESETS.get(self.preset_var.get())
        if preset is None:
            return
        for widget, key in ((self.w_entry, "W"), (self.t_entry, "T"), (self.alp_entry, "ALP")):
            widget.delete(0, tk.END)
            widget.insert(0, preset[key])
        self.status_label.config(
            text=f"Preset applied: W={preset['W']} mm, T={preset['T']} mm, ALP={preset['ALP']}")

    def _update_test_type_widgets(self, *args):
        is_kmax = (self.test_type_var.get() == "Kmax test")
        for w in [self.kmax_lbl, self.kmax_entry]:
            w.grid() if is_kmax else w.grid_remove()
        for w in [self.r_lbl, self.r_entry, self.smax_lbl, self.smax_entry]:
            w.grid_remove() if is_kmax else w.grid()

    def _redraw_grid(self, data):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.grid_widgets = []
        nsop_mode = self.nsop_map.get(self.nsop_var.get())
        hdr3 = "So/Smax" if nsop_mode == '2' else "Crack Length (c)"
        for col, hdr in enumerate(['ΔK', 'da/dN', hdr3]):
            if nsop_mode == '0' and col == 2:
                continue
            ttk.Label(self.grid_frame, text=hdr, font="-weight bold").grid(
                row=0, column=col, padx=5, pady=2)
        for row_idx, row_data in enumerate(data):
            row_ws = []
            for col_idx, cell in enumerate(row_data):
                if nsop_mode == '0' and col_idx == 2:
                    continue
                e = ttk.Entry(self.grid_frame, width=15)
                e.insert(0, str(cell))
                e.grid(row=row_idx + 1, column=col_idx, padx=5, pady=1)
                row_ws.append(e)
            self.grid_widgets.append(row_ws)

    def _validate_grid_data(self):
        is_valid = True
        last_dk, last_rate = -float('inf'), -float('inf')
        style = ttk.Style()
        style.configure('Invalid.TEntry', foreground='red')
        for row_ws in self.grid_widgets:
            row_ok = True
            try:
                dk = float(row_ws[0].get())
                rate = float(row_ws[1].get())
                if dk <= last_dk or rate <= last_rate:
                    row_ok = is_valid = False
                last_dk, last_rate = dk, rate
            except (ValueError, IndexError):
                row_ok = is_valid = False
            style_name = 'Invalid.TEntry' if not row_ok else 'TEntry'
            for w in row_ws:
                w.config(style=style_name)
        self.status_label.config(
            text="Data validation passed." if is_valid
            else "Validation Failed: Data must be numeric and strictly ascending.")
        return is_valid

    def _update_nsop_widgets(self, *args):
        self._redraw_grid([[w.get() for w in row] for row in self.grid_widgets])

    def _load_dkeff_input_file(self):
        fp = filedialog.askopenfilename(
            title="Select dkeff Input File",
            filetypes=(("dkeff Input", "*.dkin"), ("All Files", "*.*")),
            parent=self)
        if not fp:
            return
        try:
            with open(fp, 'r') as f:
                lines = [ln.strip() for ln in f if ln.strip()]
            datasets = []
            for i, line in enumerate(lines):
                parts = line.split()
                try:
                    is_hdr = (len(parts) in [4, 5] and
                              all(p.replace('.', '', 1).replace('-', '', 1).isdigit()
                                  for p in parts))
                    if is_hdr:
                        desc = (f"Dataset {len(datasets)+1}: R={parts[1]}, Smax={parts[2]}"
                                if len(parts) == 5
                                else f"Dataset {len(datasets)+1}: Kmax={parts[1]}")
                        datasets.append({'start_line': i, 'description': desc})
                except Exception:
                    continue
            if not datasets:
                raise ValueError("No valid datasets found in file.")
            selected_idx = 0
            if len(datasets) > 1:
                dlg = DatasetSelectionDialog(self, [d['description'] for d in datasets])
                if dlg.result_index is None:
                    return
                selected_idx = dlg.result_index
            ds = datasets[selected_idx]
            start = ds['start_line']

            def set_entry(widget, value):
                widget.delete(0, tk.END)
                widget.insert(0, value)

            self.parent.vars['MAT'].set(os.path.splitext(os.path.basename(fp))[0])
            ntyp_code, lunit_code = lines[2].split()
            self.ntyp_var.set(self.ntyp_rev_map.get(ntyp_code, "Compact C(T)"))
            self.lunit_combo.set(
                next((k for k, v in self.lunit_map.items() if v == lunit_code),
                     "Keep Same Units"))
            l4 = lines[3].split()
            set_entry(self.syield_entry, l4[0])
            set_entry(self.sult_entry, l4[1])
            set_entry(self.e_entry, l4[2])
            set_entry(self.alp_entry, l4[5] if len(l4) > 5 else '1.0')
            self.nsop_var.set(self.nsop_rev_map.get(
                l4[6] if len(l4) > 6 else '1', "Input c (NSOP=1)"))
            ph = lines[start].split()
            if len(ph) == 5:
                self.test_type_var.set("Constant R test")
                mtab, r_val, smax_val, w_val, t_val = ph
                self.r_var.set(r_val)
                self.smax_var.set(smax_val)
            else:
                self.test_type_var.set("Kmax test")
                mtab, kmax_val, w_val, t_val = ph
                set_entry(self.kmax_entry, kmax_val)
            set_entry(self.w_entry, w_val)
            set_entry(self.t_entry, t_val)
            loaded = []
            for ln in lines[start + 1: start + 1 + int(mtab)]:
                p = ln.split()
                loaded.append([p[1], p[2], p[3] if len(p) > 3 else ""])
            self._redraw_grid(loaded)
            self.output_filename_var.set(
                f"{os.path.splitext(os.path.basename(fp))[0]}.dkout")
            self.status_label.config(text=f"Loaded {ds['description']}.")
            self.apply_button.config(state='disabled')
            self._validate_grid_data()
        except Exception as e:
            messagebox.showerror("File Load Error", f"Could not load dkeff input:\n{e}", parent=self)

    def _save_dkeff_input_file(self, filepath):
        try:
            mat_name = self.parent.vars['MAT'].get()
            ntyp_code = self.ntyp_map[self.ntyp_var.get()]
            lunit_code = self.lunit_map[self.lunit_combo.get()]
            nsop_code = self.nsop_map[self.nsop_var.get()]
            dkeff_version = self.dkeff_version_var.get()
            test_type = self.test_type_var.get()
            syield = self.syield_entry.get()
            sult = self.sult_entry.get()
            e_mod = self.e_entry.get()
            alp = self.alp_entry.get()
            w_val = self.w_entry.get()
            t_val = self.t_entry.get()
            grid_data = [[w.get() for w in row] for row in self.grid_widgets]
            mtab = len(grid_data)

            lines = [
                f"dkeff input from {os.path.basename(filepath)}",
                f" {mat_name}",
                f"{ntyp_code}  {lunit_code}",
            ]
            if "dkeff13" in dkeff_version and test_type == "Kmax test":
                lines.append(f" {syield}  {sult}  {e_mod}  {alp}")
            else:
                lines.append(f" {syield}  {sult}  {e_mod}  0  0  {alp}  {nsop_code}")
            if test_type == "Kmax test":
                lines.append(f" {mtab}  {self.kmax_entry.get()}  {w_val}  {t_val}")
            else:
                lines.append(f" {mtab}  {self.r_var.get()}  {self.smax_var.get()}  {w_val}  {t_val}")
            for i, row in enumerate(grid_data):
                if nsop_code == '0':
                    lines.append(f"  {i+1} {row[0]} {row[1]}")
                else:
                    lines.append(f"  {i+1} {row[0]} {row[1]} {row[2]}")
            with open(filepath, 'w') as f:
                f.write('\n'.join(lines))
            self.dkeff_input_path = filepath
            self.input_file_label.config(text=f"Input File: {os.path.basename(filepath)}")
            self.output_filename_var.set(
                f"{os.path.splitext(os.path.basename(filepath))[0]}.dkout")
            self.status_label.config(text="Saved input file. Ready to generate data.")
            return True
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save dkeff input:\n{e}", parent=self)
            return False

    def _save_dkeff_file_as(self):
        initial_dir = getattr(self.parent.project, 'project_path', None)
        if initial_dir:
            dkeff_dir = os.path.join(initial_dir, "dkeff")
            os.makedirs(dkeff_dir, exist_ok=True)
            initial_dir = dkeff_dir
        fp = filedialog.asksaveasfilename(
            title="Save dkeff Input File",
            initialdir=initial_dir,
            defaultextension=".dkin",
            filetypes=(("dkeff Input", "*.dkin"),),
            parent=self)
        if fp:
            return self._save_dkeff_input_file(fp)
        return False

    def _validate_dkeff_inputs(self):
        """Returns a list of error strings; empty list means inputs are valid."""
        errors = []
        def require_positive(widget, label):
            try:
                v = float(widget.get())
                if v <= 0:
                    errors.append(f"{label} must be a positive number (got {v}).")
            except ValueError:
                errors.append(f"{label} must be a valid number.")

        require_positive(self.syield_entry, "Yield Stress (SYIELD)")
        require_positive(self.sult_entry,   "Ultimate Strength (SULT)")
        require_positive(self.e_entry,      "Elastic Modulus (E)")
        require_positive(self.w_entry,      "Specimen Width (W)")
        require_positive(self.t_entry,      "Specimen Thickness (T)")

        try:
            alp = float(self.alp_entry.get())
            if alp <= 0:
                errors.append(f"Constraint Factor (ALP) must be > 0 (got {alp}).")
        except ValueError:
            errors.append("Constraint Factor (ALP) must be a valid number.")

        if not self.grid_widgets:
            errors.append("Lab data table is empty — enter at least one data point.")

        return errors

    def _run_dkeff(self):
        errors = self._validate_dkeff_inputs()
        if errors:
            messagebox.showerror(
                "Input Validation Failed",
                "Fix these issues before running:\n\n  • " + "\n  • ".join(errors),
                parent=self)
            return

        if not self.dkeff_input_path and not self._save_dkeff_file_as():
            self.status_label.config(text="Status: Save cancelled. Run aborted.")
            return

        # Determine correct exe based on selected version
        version_str = self.dkeff_version_var.get()
        if "21" in version_str:
            exe_path = getattr(self.parent, 'dkeff21_exe_path', None)
            version_key = "dkeff21"
        else:
            exe_path = getattr(self.parent, 'dkeff13_exe_path', None)
            version_key = "dkeff13"

        if not exe_path or not os.path.exists(exe_path):
            messagebox.showerror(
                "dkeff Executable Not Found",
                f"Path for {version_str} is not configured or the file was not found.\n"
                "Go to File > Configure Executable Paths in the main window.",
                parent=self)
            return

        self.generate_button.config(state="disabled")
        self.apply_button.config(state="disabled")
        self.status_label.config(text=f"Status: Running {version_str}...")
        self.dkeff_output_path = os.path.join(
            os.path.dirname(self.dkeff_input_path), self.output_filename_var.get())

        runners.run_dkeff(
            exe_path,
            self.dkeff_input_path,
            self.dkeff_output_path,
            self.test_type_map[self.test_type_var.get()],
            self.dkeff_queue,
            version=version_key,
        )
        self.after(100, self._process_dkeff_queue)

    def _process_dkeff_queue(self):
        try:
            msg = self.dkeff_queue.get_nowait()
            if "ERROR" in msg:
                messagebox.showerror("dkeff Error", msg, parent=self)
                self.status_label.config(text="Status: Error!")
                self.generate_button.config(state="normal")
            elif msg == "DONE":
                self.processed_data = []
                raw_output = ""
                try:
                    with open(self.dkeff_output_path, 'r') as f:
                        raw_output = f.read()
                    in_section = False
                    for line in raw_output.splitlines():
                        if "DKEFF ELASTIC:" in line:
                            in_section = True
                            continue
                        if in_section and line.strip():
                            parts = line.split()
                            if len(parts) >= 2:
                                try:
                                    self.processed_data.append(
                                        [f"{float(parts[0]):.4f}",
                                         f"{float(parts[1]):.4E}"])
                                except (ValueError, IndexError):
                                    continue
                except Exception as e:
                    messagebox.showerror("Parse Error",
                                         f"Could not read dkeff output:\n{e}", parent=self)

                self._show_output(raw_output)
                self.status_label.config(
                    text=f"Run complete. {len(self.processed_data)} data points extracted.")
                self.generate_button.config(state="normal")
                if self.processed_data:
                    self.apply_button.config(state="normal")
        except queue.Empty:
            self.after(100, self._process_dkeff_queue)

    def _show_output(self, text):
        """Populate and reveal the output viewer panel."""
        self.out_text.config(state='normal')
        self.out_text.delete('1.0', tk.END)
        self.out_text.insert('1.0', text if text else "(no output)")
        self.out_text.config(state='disabled')
        if not self.out_lf.winfo_ismapped():
            self.out_lf.pack(fill='x', side='bottom', padx=10, pady=(0, 5))

    def _batch_convert_lkpx(self):
        """
        Converts a multi-R-ratio .lkpx material file into a multi-dataset .dkin file
        ready for dkeff.  Prompts the user for Smax/W/T per R-ratio via BatchInputDialog.
        """
        lkpx_path = filedialog.askopenfilename(
            title="Select .lkpx Material File to Convert",
            filetypes=(("LK Pro-X Material File", "*.lkpx"), ("All Files", "*.*")),
            parent=self)
        if not lkpx_path:
            return

        try:
            mat_props, datasets = parsers.parse_lkpx_for_batch(lkpx_path)
        except Exception as e:
            messagebox.showerror("Parsing Error",
                                 f"Could not parse the .lkpx file:\n{e}", parent=self)
            return

        r_ratios = sorted(datasets.keys(), key=float)
        if not r_ratios:
            messagebox.showerror("Empty File",
                                 "No R-ratio datasets found in the file.", parent=self)
            return

        dlg = BatchInputDialog(self, r_ratios)
        test_params = dlg.result
        if not test_params:
            return

        initial_dir = getattr(self.parent.project, 'project_path', None)
        if initial_dir:
            initial_dir = os.path.join(initial_dir, "dkeff")
            os.makedirs(initial_dir, exist_ok=True)
        output_path = filedialog.asksaveasfilename(
            title="Save Batch dkeff Input File As",
            initialdir=initial_dir,
            defaultextension=".dkin",
            filetypes=(("dkeff Input File", "*.dkin"), ("All Files", "*.*")),
            parent=self)
        if not output_path:
            return

        try:
            mat_name = self.parent.vars['MAT'].get()
            syield = float(mat_props.get('SYIELD', '0'))
            sult   = float(mat_props.get('SULT',   '0'))
            e_mod  = float(mat_props.get('E',      '0'))
            alp    = float(self.alp_entry.get() or '1.0')
            with open(output_path, 'w') as f:
                f.write(f"Batch conversion from {os.path.basename(lkpx_path)}\n")
                f.write(f" {mat_name}\n")
                f.write(" 2  0\n")   # NTYP=C(T), LUNIT=keep
                f.write(f" {syield:<7.1f}  {sult:<7.1f}  {e_mod:<10.1f}  0  0  {alp:<5.1f}  0\n")
                for r_ratio in r_ratios:
                    smax, width, thick = test_params[r_ratio]
                    data = datasets[r_ratio]
                    mtab = len(data)
                    f.write(f" {mtab}  {float(r_ratio):<4.2f}  {float(smax):<7.1f}"
                            f"  {float(width):<7.4f}  {float(thick):<7.4f}\n")
                    for i, (dk, dadn) in enumerate(data, start=1):
                        f.write(f"  {i:>2d} {float(dk):>8.4f} {float(dadn):>11.4E}\n")
            messagebox.showinfo(
                "Batch Convert Complete",
                f"Wrote {len(r_ratios)} R-ratio dataset(s) to:\n{output_path}\n\n"
                "Use File > Load dkeff Input File to open it.",
                parent=self)
        except Exception as e:
            messagebox.showerror("Write Error",
                                 f"Could not write output file:\n{e}", parent=self)

    def _import_lkpx_direct(self):
        """
        Bypass dkeff entirely: parse an .lkpx file and copy one R-ratio's
        ΔK / da/dN data straight into the main window's crack-growth table.
        Also imports material properties (SYIELD, SULT, E, MAT) from the file.

        Use this when the .lkpx data is already on a ΔKeff basis (as AFMAT
        database data typically is) and no closure correction is needed.
        """
        lkpx_path = filedialog.askopenfilename(
            title="Select .lkpx File to Import Directly",
            filetypes=(("LK Pro-X Material File", "*.lkpx"), ("All Files", "*.*")),
            parent=self)
        if not lkpx_path:
            return

        try:
            mat_props, datasets = parsers.parse_lkpx_for_batch(lkpx_path)
        except Exception as e:
            messagebox.showerror("Parse Error",
                                 f"Could not read .lkpx file:\n{e}", parent=self)
            return

        r_ratios = sorted(datasets.keys(), key=float)
        if not r_ratios:
            messagebox.showerror("Empty File",
                                 "No R-ratio datasets found in the file.", parent=self)
            return

        # Let the user choose which R-ratio to import
        selected_idx = 0
        if len(r_ratios) > 1:
            dlg = DatasetSelectionDialog(
                self, [f"R = {r}" for r in r_ratios])
            if dlg.result_index is None:
                return
            selected_idx = dlg.result_index

        r_key = r_ratios[selected_idx]
        raw_rows = datasets[r_key]
        if not raw_rows:
            messagebox.showerror("Empty Dataset",
                                 f"No data rows found for R = {r_key}.", parent=self)
            return

        # Format to match main GUI table_data: [[dk_str, dadn_str], ...]
        table_rows = []
        for dk, dadn in raw_rows:
            try:
                table_rows.append([f"{float(dk):.4f}", f"{float(dadn):.4E}"])
            except ValueError:
                continue

        if not table_rows:
            messagebox.showerror("Data Error",
                                 "Could not parse numeric values from the dataset.", parent=self)
            return

        # Apply material properties
        try:
            syield = float(mat_props.get('SYIELD', '0'))
            sult   = float(mat_props.get('SULT',   '0'))
            e_mod  = float(mat_props.get('E',       '0'))
        except ValueError:
            syield = sult = e_mod = 0.0

        lunit_code = self.lunit_map[self.lunit_combo.get()]
        factor = config.KSI_TO_MPA
        if lunit_code == '1':
            syield *= factor; sult *= factor; e_mod *= factor
        elif lunit_code == '2':
            syield /= factor; sult /= factor; e_mod /= factor

        if syield > 0:
            self.parent.vars['SYIELD'].set(f"{syield:.1f}")
        if sult > 0:
            self.parent.vars['SULT'].set(f"{sult:.1f}")
        if e_mod > 0:
            self.parent.vars['E'].set(f"{e_mod:.1f}")
        self.parent.vars['MAT'].set(
            os.path.splitext(os.path.basename(lkpx_path))[0])

        # Push data into main window crack-growth table (stored as JSON in CGR_TABLE StringVar)
        self.parent.vars['CGR_TABLE'].set(json.dumps(table_rows))
        self.parent.vars['NTAB'].set(str(len(table_rows)))
        self.parent._update_growth_plot()

        messagebox.showinfo(
            "Import Complete",
            f"Imported {len(table_rows)} data points from R = {r_key} directly into "
            f"the main window crack-growth table.\n\n"
            f"Material: {os.path.basename(lkpx_path)}\n"
            f"No dkeff run was performed — data is assumed to be on the ΔKeff basis.",
            parent=self)

    def _apply_to_main(self):
        if not self.processed_data:
            messagebox.showerror("Error", "No processed data to apply.", parent=self)
            return
        try:
            syield = float(self.syield_entry.get())
            sult = float(self.sult_entry.get())
            e_mod = float(self.e_entry.get())
            lunit_code = self.lunit_map[self.lunit_combo.get()]
            factor = config.KSI_TO_MPA
            if lunit_code == '1':
                syield *= factor
                sult *= factor
                e_mod *= factor
            elif lunit_code == '2':
                syield /= factor
                sult /= factor
                e_mod /= factor
            self.parent.vars['SYIELD'].set(f"{syield:.1f}")
            self.parent.vars['SULT'].set(f"{sult:.1f}")
            self.parent.vars['E'].set(f"{e_mod:.1f}")
            try:
                self.parent.vars['ALP'].set(f"{float(self.alp_entry.get()):.2f}")
            except ValueError:
                pass
            # Store table in CGR_TABLE StringVar as JSON (the standard mechanism)
            self.parent.vars['CGR_TABLE'].set(json.dumps(self.processed_data))
            self.parent.vars['NTAB'].set(str(len(self.processed_data)))
            self.parent._update_growth_plot()
            messagebox.showinfo(
                "Success",
                f"Applied {len(self.processed_data)} data points to main window.",
                parent=self)
            self.destroy()
        except ValueError:
            messagebox.showerror(
                "Value Error",
                "Could not apply data. Ensure material properties are valid numbers.",
                parent=self)


# ==============================================================
# HELPER DIALOGS
# ==============================================================
class BatchInputDialog(tk.Toplevel):
    """Gets Smax / W / T for each R-ratio before batch .lkpx conversion."""

    def __init__(self, parent, r_ratios):
        super().__init__(parent)
        self.title("Enter Batch Parameters")
        self.transient(parent)
        self.grab_set()
        self.result = None
        self.entries = {}

        ttk.Label(self, wraplength=440, justify='left', padding="10 6 10 4",
                  foreground='#1a5fa8', font=('Segoe UI', 9, 'italic'),
                  text="One row per R-ratio found in the .lkpx file.  "
                       "Enter the test Smax (MPa), specimen half-width W (mm), "
                       "and thickness T (mm) used for that R-ratio dataset.  "
                       "These values are written into the .dkin batch file headers.").pack(fill='x')

        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        sf = ttk.Frame(canvas, padding="10")
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for col, hdr in enumerate(["R-Ratio", "Smax (MPa)", "Width W (mm)", "Thickness T (mm)"]):
            ttk.Label(sf, text=hdr, font="-weight bold").grid(row=0, column=col, padx=5, pady=5)
        for i, r in enumerate(r_ratios, start=1):
            ttk.Label(sf, text=f"{r}").grid(row=i, column=0, sticky='w')
            sv = tk.StringVar(value="10.0")
            wv = tk.StringVar(value="3.0")
            tv = tk.StringVar(value="0.25")
            ttk.Entry(sf, textvariable=sv, width=10).grid(row=i, column=1, padx=5)
            ttk.Entry(sf, textvariable=wv, width=10).grid(row=i, column=2, padx=5)
            ttk.Entry(sf, textvariable=tv, width=10).grid(row=i, column=3, padx=5)
            self.entries[r] = (sv, wv, tv)

        btn_frame = ttk.Frame(self, padding="10")
        ttk.Button(btn_frame, text="Generate", command=self.on_ok).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel).pack(side='right')
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        btn_frame.pack(side='bottom', fill='x')
        self.wait_window()

    def on_ok(self):
        self.result = {r: (s.get(), w.get(), t.get()) for r, (s, w, t) in self.entries.items()}
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


class DatasetSelectionDialog(tk.Toplevel):
    """Selects one dataset from a multi-dataset .dkin file."""

    def __init__(self, parent, dataset_info):
        super().__init__(parent)
        self.title("Select Dataset")
        self.transient(parent)
        self.grab_set()
        self.result_index = None

        ttk.Label(self, text="Multiple datasets found. Select one to load:", padding=10).pack()
        lf = ttk.Frame(self, padding=(10, 0, 10, 10))
        lf.pack(fill='both', expand=True)
        self.listbox = tk.Listbox(lf, selectmode=tk.SINGLE, exportselection=False)
        for item in dataset_info:
            self.listbox.insert(tk.END, item)
        self.listbox.selection_set(0)
        self.listbox.pack(side='left', fill='both', expand=True)
        sb = ttk.Scrollbar(lf, orient="vertical", command=self.listbox.yview)
        sb.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=sb.set)

        bf = ttk.Frame(self, padding="10")
        bf.pack(fill='x')
        ttk.Button(bf, text="Load Selected", command=self.on_ok).pack(side='right', padx=5)
        ttk.Button(bf, text="Cancel", command=self.on_cancel).pack(side='right')
        self.wait_window()

    def on_ok(self):
        if self.listbox.curselection():
            self.result_index = self.listbox.curselection()[0]
        self.destroy()

    def on_cancel(self):
        self.result_index = None
        self.destroy()


# ==============================================================
# CRACK-GROWTH RATE TABLE EDITOR (Section 7b, per equation)
# ==============================================================
class CrackGrowthTableDialog(tk.Toplevel):
    """Per-equation tabular (ΔKeff, da/dN) editor for FASTRAN Section 7b."""

    def __init__(self, parent, callback, initial_data, eq_idx):
        super().__init__(parent)
        self.title(f"Crack-Growth Rate Table — Equation {eq_idx}")
        self.geometry("520x520")
        self.transient(parent)
        self.grab_set()

        self.callback = callback
        self.rows = copy.deepcopy(initial_data) if initial_data else []
        self.row_widgets = []

        hint = ttk.Label(
            self, padding=(10, 8), justify='left', wraplength=480,
            foreground='#1a5fa8', font=('Segoe UI', 9, 'italic'),
            text=("Enter ΔKeff (MPa√m) and da/dN (m/cycle) pairs in strictly ascending "
                  "ΔKeff order — FASTRAN interpolates between rows during the analysis.  "
                  "NTAB in the Crack Growth tab is automatically set to the number of rows "
                  "saved here, which overrides the Paris law constants (C1, C2).  "
                  "Set NTAB = 0 in the Crack Growth tab to revert to the Paris law."))
        hint.pack(fill='x')

        body = ttk.Frame(self, padding=10)
        body.pack(fill='both', expand=True)

        # Header
        for i, hdr in enumerate(["ΔKeff", "da/dN", "Actions"]):
            ttk.Label(body, text=hdr, font="-weight bold").grid(
                row=0, column=i, padx=5, pady=5,
                columnspan=(3 if hdr == "Actions" else 1))

        self.table_frame = ttk.Frame(body)
        self.table_frame.grid(row=1, column=0, columnspan=4, sticky='nsew')

        ctrl = ttk.Frame(self, padding=(10, 0))
        ctrl.pack(fill='x')
        ttk.Button(ctrl, text="Add Row", command=self._add_row).pack(side='left', padx=2)

        bottom = ttk.Frame(self, padding=10)
        bottom.pack(fill='x', side='bottom')
        ttk.Button(bottom, text="Save & Close", command=self._save_and_close).pack(side='right', padx=2)
        ttk.Button(bottom, text="Cancel", command=self.destroy).pack(side='right')

        self._redraw()

    def _redraw(self):
        for w in self.table_frame.winfo_children():
            w.destroy()
        self.row_widgets.clear()
        for i, (dk, rate) in enumerate(self.rows):
            dk_e = ttk.Entry(self.table_frame, width=18)
            dk_e.insert(0, str(dk))
            dk_e.grid(row=i, column=0, padx=5, pady=2)
            r_e = ttk.Entry(self.table_frame, width=18)
            r_e.insert(0, str(rate))
            r_e.grid(row=i, column=1, padx=5, pady=2)
            up = ttk.Button(self.table_frame, text="↑", width=3,
                            command=lambda i=i: self._move(i, -1))
            up.grid(row=i, column=2, padx=(10, 2))
            dn = ttk.Button(self.table_frame, text="↓", width=3,
                            command=lambda i=i: self._move(i, 1))
            dn.grid(row=i, column=3, padx=2)
            de = ttk.Button(self.table_frame, text="Delete", width=8,
                            command=lambda i=i: self._delete(i))
            de.grid(row=i, column=4, padx=2)
            if i == 0:
                up.config(state="disabled")
            if i == len(self.rows) - 1:
                dn.config(state="disabled")
            self.row_widgets.append((dk_e, r_e))

    def _sync_from_widgets(self):
        for i, (dk_e, r_e) in enumerate(self.row_widgets):
            if i < len(self.rows):
                self.rows[i] = [dk_e.get(), r_e.get()]

    def _add_row(self):
        self._sync_from_widgets()
        self.rows.append(['0.0', '0.0'])
        self._redraw()

    def _delete(self, idx):
        self._sync_from_widgets()
        if 0 <= idx < len(self.rows):
            self.rows.pop(idx)
            self._redraw()

    def _move(self, idx, delta):
        self._sync_from_widgets()
        new_idx = idx + delta
        if 0 <= new_idx < len(self.rows):
            self.rows[idx], self.rows[new_idx] = self.rows[new_idx], self.rows[idx]
            self._redraw()

    def _save_and_close(self):
        self._sync_from_widgets()
        if self.callback:
            self.callback(self.rows)
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
class BetaTableDialog(tk.Toplevel):
    """
    β boundary-correction table (c/W vs Fc) editor for NTYP 99, -99, and -16.

    Rows are [[c/W, Fc], ...] in ascending c/W order.  FASTRAN linearly
    interpolates between rows at runtime.  The dialog is intentionally
    parallel to CrackGrowthTableDialog so users recognise the pattern.
    """

    def __init__(self, parent, callback, initial_data, ntyp=-16):
        super().__init__(parent)
        self.title("β Correction Table  (c/W vs Fc)")
        self.geometry("500x500")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.callback = callback
        self.rows = copy.deepcopy(initial_data) if initial_data else []
        self.row_widgets = []

        if abs(ntyp) == 16:
            hint = ("Enter c/W (crack half-length ÷ half-width) and Fc (β correction "
                    "factor) pairs in strictly ascending c/W order.\n\n"
                    "For a countersunk-hole corner crack: tabulate Fcs values from "
                    "Shivakumar & Newman, NASA TM-107604 (1992) for your countersink "
                    "angle (CS_ANGLE) and depth ratio (CS_DEPTH_RATIO = t_cs/B).")
        else:
            hint = ("Enter c/W (crack half-length ÷ half-width) and Fc (boundary "
                    "correction factor) pairs in strictly ascending c/W order.\n"
                    "FASTRAN interpolates linearly between rows.")

        ttk.Label(self, padding=(10, 8), justify='left', wraplength=460,
                  foreground='#1a5fa8', font=('Segoe UI', 9, 'italic'),
                  text=hint).pack(fill='x')

        body = ttk.Frame(self, padding=10)
        body.pack(fill='both', expand=True)

        for col, hdr in enumerate(["c/W", "Fc", "Actions"]):
            ttk.Label(body, text=hdr, font="-weight bold").grid(
                row=0, column=col, padx=5, pady=5,
                columnspan=(3 if hdr == "Actions" else 1))

        self.table_frame = ttk.Frame(body)
        self.table_frame.grid(row=1, column=0, columnspan=5, sticky='nsew')
        body.rowconfigure(1, weight=1)

        ctrl = ttk.Frame(self, padding=(10, 0))
        ctrl.pack(fill='x')
        ttk.Button(ctrl, text="Add Row", command=self._add_row).pack(side='left', padx=2)

        bottom = ttk.Frame(self, padding=10)
        bottom.pack(fill='x', side='bottom')
        ttk.Button(bottom, text="Save & Close", command=self._save_and_close).pack(side='right', padx=2)
        ttk.Button(bottom, text="Cancel",       command=self.destroy).pack(side='right')

        self._redraw()

    # ── table rendering ───────────────────────────────────────────────────────

    def _redraw(self):
        for w in self.table_frame.winfo_children():
            w.destroy()
        self.row_widgets.clear()
        for i, (cw, fc) in enumerate(self.rows):
            cw_e = ttk.Entry(self.table_frame, width=16)
            cw_e.insert(0, str(cw))
            cw_e.grid(row=i, column=0, padx=5, pady=2)
            fc_e = ttk.Entry(self.table_frame, width=16)
            fc_e.insert(0, str(fc))
            fc_e.grid(row=i, column=1, padx=5, pady=2)
            up = ttk.Button(self.table_frame, text="↑", width=3,
                            command=lambda i=i: self._move(i, -1))
            up.grid(row=i, column=2, padx=(10, 2))
            dn = ttk.Button(self.table_frame, text="↓", width=3,
                            command=lambda i=i: self._move(i, 1))
            dn.grid(row=i, column=3, padx=2)
            de = ttk.Button(self.table_frame, text="Delete", width=8,
                            command=lambda i=i: self._delete(i))
            de.grid(row=i, column=4, padx=2)
            if i == 0:
                up.config(state="disabled")
            if i == len(self.rows) - 1:
                dn.config(state="disabled")
            self.row_widgets.append((cw_e, fc_e))

    def _sync_from_widgets(self):
        for i, (cw_e, fc_e) in enumerate(self.row_widgets):
            if i < len(self.rows):
                self.rows[i] = [cw_e.get(), fc_e.get()]

    def _add_row(self):
        self._sync_from_widgets()
        self.rows.append(['0.0', '1.0'])
        self._redraw()

    def _delete(self, idx):
        self._sync_from_widgets()
        if 0 <= idx < len(self.rows):
            self.rows.pop(idx)
            self._redraw()

    def _move(self, idx, delta):
        self._sync_from_widgets()
        new_idx = idx + delta
        if 0 <= new_idx < len(self.rows):
            self.rows[idx], self.rows[new_idx] = self.rows[new_idx], self.rows[idx]
            self._redraw()

    def _save_and_close(self):
        self._sync_from_widgets()
        valid = []
        for cw, fc in self.rows:
            try:
                valid.append([float(cw), float(fc)])
            except (ValueError, TypeError):
                pass
        if self.callback:
            self.callback(valid)
        self.destroy()
