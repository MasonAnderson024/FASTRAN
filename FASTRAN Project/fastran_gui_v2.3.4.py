# fastran_gui.py
"""
fastran_gui.py
--------------
Main Application: FASTRAN GUI - Engineering Edition (Government/Defense Compliant)
Version: 3.0 (Security & Enterprise Features Enabled)

Features:
- Project Management (Sandboxing)
- Security (Integrity Checks, Audit Logs)
- Dynamic Visualization (Schematics, Real-time Plots)
- Material Library (JSON)
- Sensitivity Analysis (Batch Mode)
- Comparison Tools (Post-Processor)
- Legacy Support (Import .txt/.in)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import queue
import threading
import json

# --- Custom Modules ---
import config           # Rules & Defaults
import project          # File I/O & Sandbox logic
import security         # NIST Compliance (Hashing, Logging)
import utils            # Helper functions
import parsers          # Input Generation / Output Reading
import runners          # Threaded Execution
import plots            # Matplotlib Logic
import widgets          # Custom UI Widgets (Canvas, Tooltips)
import materials        # Material Library Manager
import batch            # Sensitivity Analysis Engine
import importers        # Legacy File Support
import exporters        # CSV Export Logic
import postprocessor    # Multi-run Comparison Window
import editors          # Toplevel Editor Windows (Spectrum, Block, DkEff)
import dialogs          # Help / Progress Toplevel Windows

class FastranGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FASTRAN GUI - Engineering Edition")
        self.geometry("1280x900")
        
        # --- State Management ---
        self.project = project.ProjectManager() # Starts empty
        self.log_queue = queue.Queue()
        self.fastran_exe_path = None
        self.dkeff_exe_path = None
        self.help_window = None
        self.run_progress = None
        
        # --- Configuration ---
        self._load_external_config()
        self._init_vars()
        
        # --- UI Construction ---
        self._create_menu()
        self._create_layout()
        
        # --- Background Monitoring ---
        # Starts the loop to listen for messages from execution threads
        self.after(100, self._monitor_execution_queue)

    # Per-equation crack-growth keys (Section 6 + 7a). Eq 1 uses base keys;
    # eq 2..4 use suffixed copies (e.g., C1_2, NTAB_3) for IRATE=2 or 4.
    PER_EQ_KEYS = ('C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7',
                   'KF', 'M', 'NEQN', 'NTAB', 'NDKTH')
    MAX_EQUATIONS = 4

    def _init_vars(self):
        """Initialize all Tkinter variables from config defaults."""
        self.vars = {}
        for key, value in config.DEFAULT_VALUES.items():
            self.vars[key] = tk.StringVar(value=value)

        # Pre-create suffixed vars for equations 2..MAX_EQUATIONS using the
        # same defaults as the base keys, so IRATE>1 has somewhere to store
        # independent constants without breaking save/load state serialization.
        for eq_idx in range(2, self.MAX_EQUATIONS + 1):
            for key in self.PER_EQ_KEYS:
                self.vars[f"{key}_{eq_idx}"] = tk.StringVar(
                    value=config.DEFAULT_VALUES.get(key, '0'))

        # Per-equation crack-growth tables (Section 7b). Each holds a JSON-encoded
        # list of [dk, rate] pairs so the existing JSON save/load state code
        # round-trips them with no special handling.
        self.vars['CGR_TABLE'] = tk.StringVar(value='[]')
        for eq_idx in range(2, self.MAX_EQUATIONS + 1):
            self.vars[f'CGR_TABLE_{eq_idx}'] = tk.StringVar(value='[]')

        # Trace critical variables for real-time plotting (Geometry & Crack Growth)
        # Note: NTYP/NFOPT traces are handled by Combobox bindings
        self.vars['C1'].trace_add("write", self._update_growth_plot)
        self.vars['C2'].trace_add("write", self._update_growth_plot)

    def _var_for(self, key, eq_idx):
        """Return the StringVar for a Section-6/7a key at the given equation index (1-based)."""
        return self.vars[key] if eq_idx == 1 else self.vars[f"{key}_{eq_idx}"]

    def _load_external_config(self):
        """Finds the EXEs (FASTRAN/DKEFF) from local config."""
        cfg_file = "fastran_gui.cfg"
        if os.path.exists(cfg_file):
            try:
                with open(cfg_file, 'r') as f:
                    for line in f:
                        if "=" in line:
                            key, val = line.strip().split("=", 1)
                            if key == "fastran_path": self.fastran_exe_path = val.strip()
                            if key == "dkeff_path": self.dkeff_exe_path = val.strip()
            except Exception as e:
                print(f"Config Load Error: {e}")

    # ------------------------------------------------------------------
    # LAYOUT BUILDER
    # ------------------------------------------------------------------
    def _create_layout(self):
        # Top Bar: Project Status
        top_frame = ttk.Frame(self, padding="10 5 10 0")
        top_frame.pack(fill='x')
        self.lbl_project = ttk.Label(
            top_frame, 
            text="No Project Loaded (Results will not be saved)", 
            foreground="red", 
            font=('Segoe UI', 10, 'bold')
        )
        self.lbl_project.pack(side='left')

        # Main Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Tab 1: Geometry (Visual)
        self.tab_geo = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_geo, text="1. Geometry")
        self._build_geometry_tab(self.tab_geo)
        
        # Tab 2: Material
        self.tab_mat = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_mat, text="2. Material")
        self._build_material_tab(self.tab_mat)
        
        # Tab 3: Loading
        self.tab_load = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_load, text="3. Loading")
        self._build_loading_tab(self.tab_load)
        
        # Tab 4: Crack Growth (Analysis)
        self.tab_crack = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_crack, text="4. Crack Growth")
        self._build_crack_growth_tab(self.tab_crack)
        
        # Tab 5: Sensitivity (Batch)
        self.tab_batch = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_batch, text="5. Sensitivity")
        self._build_batch_tab(self.tab_batch)

        # Bottom Bar: Execution & Status
        bot_frame = ttk.Frame(self, padding="10")
        bot_frame.pack(fill='x', side='bottom')
        
        # Run Button
        self.btn_run = ttk.Button(bot_frame, text="RUN ANALYSIS", command=self.run_analysis, state='disabled', width=20)
        self.btn_run.pack(side='right', padx=5)
        
        # Status Log
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(bot_frame, textvariable=self.status_var, relief='sunken', anchor='w').pack(side='left', fill='x', expand=True)

    # ------------------------------------------------------------------
    # TAB 1: GEOMETRY
    # ------------------------------------------------------------------
    def _build_geometry_tab(self, parent):
        paned = ttk.PanedWindow(parent, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=10, pady=10)
        
        left = ttk.Frame(paned, padding=10)
        right = ttk.LabelFrame(paned, text="Specimen Schematic", padding=10)
        paned.add(left, weight=1)
        paned.add(right, weight=1)
        
        # NTYP Selector
        ttk.Label(left, text="Geometry Type (NTYP):").pack(anchor='w')
        cb = ttk.Combobox(left, textvariable=self.vars['NTYP'], values=config.GEOMETRY_OPTIONS, state='readonly')
        cb.pack(fill='x', pady=5)
        cb.bind("<<ComboboxSelected>>", self._on_ntyp_change)
        
        # Standard Dimensions (Section 11: W T CI AI CN AN HN RAD RADF)
        grp = ttk.LabelFrame(left, text="Dimensions (Length Units)", padding=10)
        grp.pack(fill='x', pady=10)
        self._add_entry(grp, "Width (W):",         'W',    0, 0)
        self._add_entry(grp, "Thickness (B/T):",   'B',    0, 1)
        self._add_entry(grp, "Init. Crack (Ci):",  'CI',   1, 0)
        self._add_entry(grp, "Init. Depth (Ai):",  'AI',   1, 1)
        self._add_entry(grp, "Notch (Cn):",        'CN',   2, 0)
        self._add_entry(grp, "Notch Depth (An):",  'AN',   2, 1)
        self._add_entry(grp, "Notch Half-Ht (Hn):",'HN',   3, 0)
        self._add_entry(grp, "Hole Radius (RAD):", 'RAD',  3, 1)
        self._add_entry(grp, "Fastener (RADF):",   'RADF', 4, 0)
        self._add_entry(grp, "Final Crack (Cf):",  'CF',   4, 1)

        # Dynamic Special Inputs (Section 14)
        self.special_frame = ttk.LabelFrame(left, text="Special Requirements", padding=10)
        self.special_frame.pack(fill='x', pady=10)

        # Live dimension readout (must pack before the canvas so it claims
        # the bottom strip; canvas then expand-fills the remainder).
        self.dim_readout = ttk.Label(right, font=('Consolas', 9), foreground='#444',
                                     anchor='w')
        self.dim_readout.pack(side='bottom', fill='x', padx=4, pady=(4, 2))
        for k in ('W', 'B', 'CI', 'CN', 'CF'):
            self.vars[k].trace_add('write', self._update_dim_readout)
        self._update_dim_readout()

        # Visualization Widget
        self.geo_canvas = widgets.GeometryCanvas(right)
        self.geo_canvas.pack(fill='both', expand=True)

    def _update_dim_readout(self, *_):
        parts = []
        for key, label in (('W', 'W'), ('B', 'T'), ('CI', 'Ci'),
                           ('CN', 'Cn'), ('CF', 'Cf')):
            try:
                parts.append(f"{label}={float(self.vars[key].get()):g}")
            except (ValueError, TypeError, KeyError):
                parts.append(f"{label}=?")
        self.dim_readout.config(text="   ".join(parts))

    def _on_ntyp_change(self, event=None):
        """Update schematic and special fields."""
        try:
            ntyp_id = int(self.vars['NTYP'].get().split(':')[0])
            self.geo_canvas.update_diagram(ntyp_id)
            
            # Reset special frame
            for w in self.special_frame.winfo_children(): w.destroy()
            
            # Fetch rules
            specials = config.NTYP_DATA.get(ntyp_id, {}).get('special', [])
            if not specials:
                ttk.Label(self.special_frame, text="No special inputs required for this geometry.", font=('Segoe UI', 8, 'italic')).pack()
            else:
                for req in specials:
                    # Create var if missing
                    if req not in self.vars: self.vars[req] = tk.StringVar(value="0.0")
                    f = ttk.Frame(self.special_frame)
                    f.pack(fill='x', pady=2)
                    ttk.Label(f, text=f"{req}:").pack(side='left')
                    ttk.Entry(f, textvariable=self.vars[req]).pack(side='right', expand=True, fill='x')
        except: pass

    # ------------------------------------------------------------------
    # TAB 2: MATERIAL (Library Enabled)
    # ------------------------------------------------------------------
    def _build_material_tab(self, parent):
        f = ttk.Frame(parent, padding=20)
        f.pack(fill='both', expand=True)
        
        # Material Library Controls
        lib_frame = ttk.LabelFrame(f, text="Material Library (JSON)", padding=10)
        lib_frame.pack(fill='x', pady=10)
        ttk.Button(lib_frame, text="Load Material...", command=self._load_material_dialog).pack(side='left', padx=5)
        ttk.Button(lib_frame, text="Save Current to Library...", command=self._save_material_dialog).pack(side='left', padx=5)

        # Properties
        grp = ttk.LabelFrame(f, text="Properties", padding=10)
        grp.pack(fill='x', pady=10)
        self._add_entry(grp, "Material Name:", 'MAT', 0, 0)
        self._add_entry(grp, "Yield (Sy):", 'SYIELD', 1, 0)
        self._add_entry(grp, "Ultimate (Su):", 'SULT', 1, 1)
        self._add_entry(grp, "Modulus (E):", 'E', 2, 0)
        self._add_entry(grp, "Constraint (ALP):", 'ALP', 2, 1)

    # ------------------------------------------------------------------
    # TAB 3: LOADING
    # ------------------------------------------------------------------
    def _build_loading_tab(self, parent):
        f = ttk.Frame(parent, padding=20)
        f.pack(fill='both', expand=True)
        
        ttk.Label(f, text="Loading Type (NFOPT):").grid(row=0, column=0, sticky='w')
        cb = ttk.Combobox(f, textvariable=self.vars['NFOPT'], values=config.LOADING_OPTIONS, state='readonly', width=40)
        cb.grid(row=0, column=1, sticky='ew')
        cb.bind("<<ComboboxSelected>>", self._on_nfopt_change)
        
        self.load_grid = ttk.LabelFrame(f, text="Stress Parameters", padding=10)
        self.load_grid.grid(row=1, column=0, columnspan=2, sticky='ew', pady=20)
        
        self._add_entry(self.load_grid, "Max Stress (Smax):", 'SMAX', 0, 0)
        self._add_entry(self.load_grid, "Ratio (R):", 'R', 0, 1)
        self._add_entry(self.load_grid, "Frequency:", 'FW', 1, 0)
        
        # Dynamic Label for Invert/Clip
        self.lbl_invert = ttk.Label(self.load_grid, text="Invert/Clip:")
        self.lbl_invert.grid(row=1, column=2, sticky='e', padx=5)
        ttk.Entry(self.load_grid, textvariable=self.vars['INVERT'], width=10).grid(row=1, column=3, sticky='w')

        # Spectrum/Block editor launchers (visibility driven by NFOPT)
        self.spectrum_frame = ttk.LabelFrame(f, text="Spectrum File", padding=10)
        self.spectrum_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=5)
        ttk.Label(self.spectrum_frame, text="Filename:").grid(row=0, column=0, sticky='e', padx=5)
        ttk.Entry(self.spectrum_frame, textvariable=self.vars['SPECTRA'], width=30).grid(row=0, column=1, sticky='w')
        ttk.Button(self.spectrum_frame, text="Browse...", command=self._browse_spectrum_file).grid(row=0, column=2, padx=5)
        ttk.Button(self.spectrum_frame, text="Edit Spectrum...", command=self._launch_spectrum_editor).grid(row=0, column=3, padx=5)

        self.block_frame = ttk.LabelFrame(f, text="Block Loading (NFOPT=1)", padding=10)
        self.block_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=5)
        ttk.Button(self.block_frame, text="Edit Block Loading...", command=self._launch_block_editor).pack(side='left', padx=5)
        ttk.Label(self.block_frame, text="(Define variable-amplitude block sequence)").pack(side='left', padx=10)

        # Section 10: Specimen / loading options
        sec10 = ttk.LabelFrame(f, text="Specimen & Loading Options (Section 10)", padding=10)
        sec10.grid(row=4, column=0, columnspan=2, sticky='ew', pady=5)
        self._add_combobox(sec10, "LTYP:",   'LTYP',   config.LTYP_OPTIONS,   0, 0)
        self._add_combobox(sec10, "LFAST:",  'LFAST',  config.LFAST_OPTIONS,  1, 0)
        self._add_combobox(sec10, "KCONST:", 'KCONST', config.KCONST_OPTIONS, 2, 0)
        self._add_entry(sec10, "NS:",     'NS',     3, 0)
        self._add_entry(sec10, "NTCMAX:", 'NTCMAX', 3, 1)

        # Section 16: Proof test / constant So
        sec16 = ttk.LabelFrame(f, text="Proof Test / Constant So (Section 16)", padding=10)
        sec16.grid(row=5, column=0, columnspan=2, sticky='ew', pady=5)
        self._add_entry(sec16, "NRC:",     'NRC',     0, 0)
        self._add_entry(sec16, "DVALUE:",  'DVALUE',  0, 1)
        self._add_entry(sec16, "NCYCLE1:", 'NCYCLE1', 1, 0)
        self._add_entry(sec16, "NCYCLE2:", 'NCYCLE2', 1, 1)

        # Apply initial visibility
        self._on_nfopt_change()

    def _browse_spectrum_file(self):
        if not self.project.project_path:
            messagebox.showwarning("No Project", "Open or create a project first.")
            return
        f = filedialog.askopenfilename(
            initialdir=self.project.get_path('input'),
            filetypes=[("Text", "*.txt"), ("All Files", "*.*")])
        if f:
            self.vars['SPECTRA'].set(os.path.basename(f))

    def _on_nfopt_change(self, event=None):
        try:
            nfopt_id = int(self.vars['NFOPT'].get().split(':')[0])
            rule = config.NFOPT_DATA.get(nfopt_id, {})
            self.lbl_invert.config(text=f"{rule.get('invert_label', 'Invert')}:")
            needs_spectrum = bool(rule.get('requires_spectrum'))
            needs_block = bool(rule.get('requires_block'))
            if hasattr(self, 'spectrum_frame'):
                if needs_spectrum:
                    self.spectrum_frame.grid()
                else:
                    self.spectrum_frame.grid_remove()
            if hasattr(self, 'block_frame'):
                if needs_block:
                    self.block_frame.grid()
                else:
                    self.block_frame.grid_remove()
        except: pass

    # ------------------------------------------------------------------
    # TAB 4: CRACK GROWTH
    # ------------------------------------------------------------------
    def _build_crack_growth_tab(self, parent):
        paned = ttk.PanedWindow(parent, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=10, pady=10)
        
        left = ttk.Frame(paned, padding=10)
        right = ttk.LabelFrame(paned, text="Paris Law Preview", padding=10)
        paned.add(left, weight=3) # 60%
        paned.add(right, weight=2) # 40%
        
        # Options
        opt_f = ttk.Frame(left); opt_f.pack(fill='x')
        ttk.Label(opt_f, text="Model Option (IRATE):").pack(side='left')
        cb = ttk.Combobox(opt_f, textvariable=self.vars['IRATE'], values=['1', '2', '4'], width=5, state='readonly')
        cb.pack(side='left', padx=5)
        cb.bind("<<ComboboxSelected>>", self._on_irate_change)
        widgets.ToolTip(cb, "1 = Single law\n2 = Two independent laws (c- and a-directions)\n4 = Small/large-crack transition")

        # Section 9: Output Options
        sec9 = ttk.LabelFrame(left, text="Output Options (Section 9)", padding=10)
        sec9.pack(fill='x', pady=8)
        self._add_entry(sec9, "NIPT:",  'NIPT',  0, 0)
        self._add_entry(sec9, "NPRT:",  'NPRT',  0, 1)
        self._add_entry(sec9, "LSTEP:", 'LSTEP', 1, 0)
        self._add_entry(sec9, "NDKE:",  'NDKE',  1, 1)
        self._add_entry(sec9, "DCPR:",  'DCPR',  2, 0)

        # Constants Container (Dynamic — rebuilt by _on_irate_change)
        self.constants_frame = ttk.Frame(left)
        self.constants_frame.pack(fill='both', expand=True, pady=10)
        self._build_constants_panel()

        # Plot
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        self.plot_fig = Figure(figsize=(4, 3), dpi=100)
        self.plot_ax = self.plot_fig.add_subplot(111)
        plots.setup_growth_plot(self.plot_ax)
        self.plot_canvas = FigureCanvasTkAgg(self.plot_fig, master=right)
        self.plot_canvas.get_tk_widget().pack(fill='both', expand=True)

    def _render_growth_inputs_for_eq(self, parent, eq_idx):
        """Render Section 6/7a inputs for a single equation (1-indexed)."""
        grp = ttk.LabelFrame(parent, text="Paris Constants (da/dN = C1 * dK^C2)", padding=10)
        grp.pack(fill='x')
        self._add_eq_entry(grp, "C1 (Coeff):", 'C1', eq_idx, 0, 0)
        self._add_eq_entry(grp, "C2 (Exp):",   'C2', eq_idx, 0, 1)
        self._add_eq_entry(grp, "C3:",         'C3', eq_idx, 1, 0)
        self._add_eq_entry(grp, "C4:",         'C4', eq_idx, 1, 1)

        grp2 = ttk.LabelFrame(parent, text="Thresholds", padding=10)
        grp2.pack(fill='x', pady=5)
        self._add_eq_entry(grp2, "DKth (C5):", 'C5', eq_idx, 0, 0)
        self._add_eq_entry(grp2, "C6:",        'C6', eq_idx, 0, 1)
        self._add_eq_entry(grp2, "C7:",        'C7', eq_idx, 1, 0)

        grp3 = ttk.LabelFrame(parent, text="Closure / Tabular", padding=10)
        grp3.pack(fill='x', pady=5)
        self._add_eq_entry(grp3, "KF:",   'KF',   eq_idx, 0, 0)
        self._add_eq_entry(grp3, "m:",    'M',    eq_idx, 0, 1)
        self._add_eq_entry(grp3, "NEQN:", 'NEQN', eq_idx, 1, 0)
        self._add_eq_entry(grp3, "NTAB:", 'NTAB', eq_idx, 1, 1)
        self._add_eq_entry(grp3, "NDKTH:",'NDKTH',eq_idx, 2, 0)
        ttk.Button(grp3, text="Edit Table...",
                   command=lambda i=eq_idx: self._launch_cgr_table_editor(i)
                   ).grid(row=2, column=2, columnspan=2, sticky='w', padx=10)

    def _add_eq_entry(self, parent, label, key, eq_idx, r, c):
        ttk.Label(parent, text=label).grid(row=r, column=c*2, sticky='e', padx=5, pady=5)
        ttk.Entry(parent, textvariable=self._var_for(key, eq_idx), width=12).grid(
            row=r, column=c*2+1, sticky='w', padx=5)

    def _build_constants_panel(self):
        """Build (or rebuild) the IRATE-driven Notebook of equation panels."""
        for w in self.constants_frame.winfo_children():
            w.destroy()
        try:
            irate = int(self.vars['IRATE'].get())
        except (TypeError, ValueError):
            irate = 1
        irate = max(1, min(self.MAX_EQUATIONS, irate))

        if irate == 1:
            # Single law — render inline (no notebook chrome)
            self._render_growth_inputs_for_eq(self.constants_frame, 1)
            return

        nb = ttk.Notebook(self.constants_frame)
        nb.pack(fill='both', expand=True)
        eq_labels = {
            2: ("Eq 1 (c-dir)", "Eq 2 (a-dir)"),
            4: ("Eq 1 (Small / c)", "Eq 2 (Small / a)",
                "Eq 3 (Large / c)", "Eq 4 (Large / a)"),
        }
        labels = eq_labels.get(irate, tuple(f"Equation {i}" for i in range(1, irate + 1)))
        for i in range(1, irate + 1):
            tab = ttk.Frame(nb, padding=8)
            nb.add(tab, text=labels[i - 1])
            self._render_growth_inputs_for_eq(tab, i)

    def _on_irate_change(self, event=None):
        self._build_constants_panel()
        self._update_growth_plot()

    def _update_growth_plot(self, *args):
        try:
            c1 = self.vars['C1'].get()
            c2 = self.vars['C2'].get()
            self.plot_ax.clear()
            plots.plot_paris_law(self.plot_ax, c1, c2, 0, 0)
            self.plot_canvas.draw()
        except: pass

    # ------------------------------------------------------------------
    # TAB 5: SENSITIVITY (Batch)
    # ------------------------------------------------------------------
    def _build_batch_tab(self, parent):
        paned = ttk.PanedWindow(parent, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=10, pady=10)
        
        left = ttk.LabelFrame(paned, text="Parametric Setup", padding=10)
        right = ttk.LabelFrame(paned, text="Design Curve", padding=10)
        paned.add(left, weight=1)
        paned.add(right, weight=2)
        
        # Controls
        ttk.Label(left, text="Variable to Sweep:").pack(anchor='w')
        self.batch_var = tk.StringVar()
        cb = ttk.Combobox(left, textvariable=self.batch_var, values=['SMAX', 'R', 'CI', 'W', 'SYIELD'], state='readonly')
        cb.pack(fill='x', pady=5); cb.current(0)
        
        gf = ttk.Frame(left); gf.pack(fill='x', pady=10)
        self.batch_start = tk.StringVar(value="100"); self.batch_end = tk.StringVar(value="200"); self.batch_steps = tk.StringVar(value="5")
        
        ttk.Label(gf, text="Start:").grid(row=0, column=0, sticky='e')
        ttk.Entry(gf, textvariable=self.batch_start, width=8).grid(row=0, column=1)
        ttk.Label(gf, text="End:").grid(row=1, column=0, sticky='e')
        ttk.Entry(gf, textvariable=self.batch_end, width=8).grid(row=1, column=1)
        ttk.Label(gf, text="Steps:").grid(row=2, column=0, sticky='e')
        ttk.Entry(gf, textvariable=self.batch_steps, width=8).grid(row=2, column=1)
        
        ttk.Button(left, text="Generate & Run Batch", command=self._run_batch_analysis).pack(fill='x', pady=20)
        self.batch_progress = ttk.Progressbar(left, mode='determinate'); self.batch_progress.pack(fill='x')
        
        # Plot
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        self.batch_fig = Figure(figsize=(5, 4), dpi=100)
        self.batch_ax = self.batch_fig.add_subplot(111)
        self.batch_ax.grid(True)
        self.batch_canvas = FigureCanvasTkAgg(self.batch_fig, master=right)
        self.batch_canvas.get_tk_widget().pack(fill='both', expand=True)

    # ------------------------------------------------------------------
    # MENU & ACTIONS
    # ------------------------------------------------------------------
    def _create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project...", command=self._new_project)
        file_menu.add_command(label="Open Project...", command=self._open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Import Legacy Input...", command=self._import_legacy_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Spectrum Editor...", command=self._launch_spectrum_editor)
        tools_menu.add_command(label="Block Loading Editor...", command=self._launch_block_editor)
        tools_menu.add_separator()
        tools_menu.add_command(label="Material Data Generator (DkEff)...", command=self._launch_dkeff)

        # Results Menu
        self.results_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Results", menu=self.results_menu)
        self.results_menu.add_command(label="Export to CSV...", command=self._export_results_csv)
        self.results_menu.add_command(label="Compare Runs (Overlay)...", command=self._launch_postprocessor)
        self.results_menu.add_command(label="Open Output Folder", command=self._open_output_folder)
        self.results_menu.entryconfig("Export to CSV...", state="disabled")

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Help...", command=self._show_help)

    # ------------------------------------------------------------------
    # PROJECT MANAGEMENT
    # ------------------------------------------------------------------
    def _new_project(self):
        d = filedialog.askdirectory(title="Select Parent Directory")
        if d:
            name = simpledialog.askstring("Project Name", "Enter project name:")
            if name:
                path = os.path.join(d, name)
                self.project.create_project(path, name)
                self.lbl_project.config(text=f"Project: {name}", foreground="green")
                self.btn_run.config(state='normal')
                self._save_gui_state() # Init settings

    def _open_project(self):
        d = filedialog.askdirectory(title="Select Project Folder (.frproj)")
        if d:
            self.project.load_project(d)
            self.lbl_project.config(text=f"Project: {self.project.metadata.get('name', 'Loaded')}", foreground="green")
            self.btn_run.config(state='normal')
            self._load_gui_state()
            self.results_menu.entryconfig("Export to CSV...", state="normal")

    def _save_gui_state(self):
        if not self.project.project_path: return
        state = {k: v.get() for k, v in self.vars.items()}
        try:
            with open(os.path.join(self.project.get_path('config'), 'settings.json'), 'w') as f:
                json.dump(state, f, indent=4)
        except: pass

    def _load_gui_state(self):
        if not self.project.project_path: return
        fpath = os.path.join(self.project.get_path('config'), 'settings.json')
        if os.path.exists(fpath):
            try:
                with open(fpath, 'r') as f:
                    state = json.load(f)
                for k, v in state.items():
                    if k in self.vars: self.vars[k].set(v)
                # Migrate legacy bare-integer values for combobox-driven fields
                # (older saves predate the LTYP/LFAST/KCONST combobox upgrade).
                for key, options in (('LTYP', config.LTYP_OPTIONS),
                                     ('LFAST', config.LFAST_OPTIONS),
                                     ('KCONST', config.KCONST_OPTIONS)):
                    cur = self.vars[key].get()
                    if ':' not in cur:
                        self.vars[key].set(config.label_for_int(cur, options))
                self._on_ntyp_change()
                self._on_nfopt_change()
                self._on_irate_change()
            except: pass

    # ------------------------------------------------------------------
    # EXECUTION
    # ------------------------------------------------------------------
    def _validate_run_inputs(self):
        """
        Pre-run sanity checks. Returns (errors, warnings) — both lists of
        human-readable strings. Errors block the run; warnings prompt the
        user to confirm.
        """
        errors, warnings = [], []

        def num(key):
            try:
                return float(self.vars[key].get())
            except (ValueError, TypeError, KeyError):
                return None

        # Crack-size ordering
        ci, cf, cn = num('CI'), num('CF'), num('CN')
        if ci is None or cf is None:
            errors.append("Initial (Ci) and final (Cf) crack must be valid numbers.")
        elif cf <= ci:
            errors.append(f"Final crack Cf ({cf}) must be > initial crack Ci ({ci}).")
        if cn is not None and ci is not None and cn > ci:
            errors.append(f"Notch Cn ({cn}) cannot exceed initial crack Ci ({ci}).")

        # Critical dimensions / properties must be positive
        for key, label in (('W', 'Width'), ('B', 'Thickness'),
                           ('E', "Young's modulus")):
            v = num(key)
            if v is None:
                errors.append(f"{label} ({key}) must be a valid number.")
            elif v <= 0:
                warnings.append(f"{label} ({key}) is non-positive: {v}")

        # Flow-stress check (Smax must stay below (SYIELD+SULT)/2 per FASTRAN docs)
        sy, su, smax = num('SYIELD'), num('SULT'), num('SMAX')
        if sy is not None and su is not None and sy > 0 and su > 0 and smax is not None:
            sflow = (sy + su) / 2.0
            if smax >= sflow:
                warnings.append(
                    f"Smax ({smax}) >= flow stress ({sflow:.1f} = avg of yield and ultimate). "
                    "FASTRAN may reject this load level.")

        # Spectrum file presence (only if NFOPT requires it)
        try:
            nfopt = int(self.vars['NFOPT'].get().split(':')[0])
        except (ValueError, AttributeError):
            nfopt = -1
        rule = config.NFOPT_DATA.get(nfopt, {})
        if rule.get('requires_spectrum') and self.project.project_path:
            fname = self.vars['SPECTRA'].get().strip()
            if not fname:
                errors.append(f"NFOPT={nfopt} requires a spectrum file but the SPECTRA field is empty.")
            else:
                full = os.path.join(self.project.get_path('input'), fname)
                if not os.path.exists(full):
                    errors.append(
                        f"Spectrum file not found in project input/: {fname} "
                        f"(NFOPT={nfopt} requires one).")

        return errors, warnings

    def run_analysis(self):
        if not self.project.project_path: return

        # 1. Validation
        errors, warnings = self._validate_run_inputs()
        if errors:
            messagebox.showerror(
                "Validation Errors",
                "Fix these issues before running:\n\n  • " + "\n  • ".join(errors))
            return
        if warnings:
            msg = ("Possible issues detected:\n\n  • " + "\n  • ".join(warnings)
                   + "\n\nRun anyway?")
            if not messagebox.askyesno("Validation Warnings", msg):
                return

        # 2. Save State
        self._save_gui_state()

        # 3. Generate Input
        inp_path = os.path.join(self.project.get_path('input'), "analysis_input.txt")
        success, msg = parsers.generate_fastran_input(inp_path, self.vars)
        if not success:
            messagebox.showerror("Gen Error", msg)
            return

        # 4. Run (Secure)
        self.status_var.set("Running FASTRAN...")
        self.btn_run.config(state='disabled')
        runners.run_fastran(
            self.fastran_exe_path, inp_path, self.project.get_path('output'),
            self.log_queue, self.project.project_path
        )
        self.run_progress = dialogs.ProgressWindow(
            self, title="Running FASTRAN", message="Analysis in progress..."
        )
        self.run_progress.start()

    def _close_run_progress(self):
        if self.run_progress is not None:
            try:
                self.run_progress.stop()
            except tk.TclError:
                pass
            self.run_progress = None

    def _run_batch_analysis(self):
        if not self.project.project_path: return
        
        # Setup Batch Manager
        raw_vars = {k: v.get() for k, v in self.vars.items()}
        self.batch_mgr = batch.BatchManager(self.project, raw_vars)
        
        target = self.batch_var.get()
        success, msg = self.batch_mgr.generate_jobs(
            target, self.batch_start.get(), self.batch_end.get(), self.batch_steps.get()
        )
        
        if not success:
            messagebox.showerror("Batch Error", msg); return
            
        self.batch_progress['maximum'] = len(self.batch_mgr.jobs)
        self.batch_progress['value'] = 0
        self.status_var.set("Running Batch Analysis...")
        
        threading.Thread(target=self._execute_batch_thread, daemon=True).start()

    def _execute_batch_thread(self):
        """Threaded batch runner"""
        results_x = []; results_y = []
        for idx, job in enumerate(self.batch_mgr.jobs):
            q = queue.Queue()
            runners.run_fastran(
                self.fastran_exe_path, job['input_path'], self.project.get_path('output'), q, self.project.project_path
            )
            # Simple wait loop
            while True:
                try:
                    msg = q.get(timeout=0.5)
                    if "PROCESS FINISHED" in msg or "ERROR" in msg: break
                except queue.Empty: pass
            
            # Extract
            out_path = os.path.join(self.project.get_path('output'), job['output_filename'])
            cycles = self.batch_mgr.extract_cycles(out_path)
            results_x.append(job['val']); results_y.append(cycles)
            
            self.after(0, self._update_batch_progress, idx+1, results_x, results_y)
        
        self.after(0, lambda: self.status_var.set("Batch Complete."))

    def _update_batch_progress(self, count, xs, ys):
        self.batch_progress['value'] = count
        self.batch_ax.clear()
        self.batch_ax.plot(xs, ys, 'o-', linewidth=2)
        self.batch_ax.set_xlabel(self.batch_var.get())
        self.batch_ax.set_ylabel("Cycles")
        self.batch_ax.grid(True)
        self.batch_canvas.draw()

    def _monitor_execution_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if "PROCESS FINISHED" in msg:
                    self._close_run_progress()
                    self.status_var.set("Run Complete.")
                    self.btn_run.config(state='normal')
                    self.results_menu.entryconfig("Export to CSV...", state="normal")
                    messagebox.showinfo("Success", "Analysis Complete.")
                elif "ERROR" in msg or "SECURITY BLOCK" in msg:
                    self._close_run_progress()
                    self.status_var.set("Run Failed.")
                    self.btn_run.config(state='normal')
                    messagebox.showerror("Error", msg)
        except queue.Empty: pass
        finally: self.after(200, self._monitor_execution_queue)

    # ------------------------------------------------------------------
    # DIALOGS & HANDLERS
    # ------------------------------------------------------------------
    def _save_material_dialog(self):
        name = simpledialog.askstring("Save Material", "Material Name:")
        if name:
            data = {k: self.vars[k].get() for k in self.vars}
            mgr = materials.MaterialManager()
            mgr.save_material(name, data)

    def _load_material_dialog(self):
        mgr = materials.MaterialManager()
        f = filedialog.askopenfilename(initialdir=mgr.materials_dir, filetypes=[("JSON", "*.json")])
        if f:
            data = mgr.load_material(f)
            if data:
                for k, v in data.items():
                    if k in self.vars: self.vars[k].set(v)
                self._update_growth_plot()

    def _import_legacy_dialog(self):
        f = filedialog.askopenfilename(filetypes=[("Text", "*.txt *.in")])
        if f:
            success, data = importers.parse_fastran_input(f)
            if success:
                for k, v in data.items():
                    if k in self.vars: self.vars[k].set(v)
                self._on_ntyp_change()
                self._update_growth_plot()
                messagebox.showinfo("Import", "Legacy file imported.")
            else:
                messagebox.showerror("Import Error", data)

    def _export_results_csv(self):
        out_dir = self.project.get_path("output")
        # Find latest
        files = [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith('.fou')]
        if not files: return
        latest = max(files, key=os.path.getmtime)
        
        save_path = filedialog.asksaveasfilename(defaultextension=".csv")
        if save_path:
            exporters.export_to_csv(latest, save_path)
            messagebox.showinfo("Export", "CSV Saved.")

    def _launch_postprocessor(self):
        if not self.project.project_path: return
        postprocessor.ComparisonWindow(self, self.project)

    # ------------------------------------------------------------------
    # EDITOR LAUNCHERS
    # ------------------------------------------------------------------
    def _launch_spectrum_editor(self):
        if not self.project.project_path:
            messagebox.showwarning("No Project", "Open or create a project first.")
            return
        filename = self.vars['SPECTRA'].get().strip() or "spectrum.txt"

        def _on_save(saved_filename):
            self.vars['SPECTRA'].set(saved_filename)

        editors.SpectrumCreatorWindow(self, _on_save, self.project, filename)

    def _launch_block_editor(self):
        if not self.project.project_path:
            messagebox.showwarning("No Project", "Open or create a project first.")
            return

        cfg_path = os.path.join(self.project.get_path('config'), 'block_loading.json')
        initial_data = None
        initial_params = {k: self.vars[k].get() for k in
                          ('MAXSEQ', 'MAXBLK', 'SCALE', 'LPRINT', 'MAXLPR')}
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, 'r') as f:
                    saved = json.load(f)
                initial_data = saved.get('blocks')
                initial_params.update(saved.get('params', {}))
            except Exception:
                pass

        def _on_save(result):
            try:
                with open(cfg_path, 'w') as f:
                    json.dump(result, f, indent=2)
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save block data:\n{e}")
                return
            for k, v in result.get('params', {}).items():
                if k in self.vars:
                    self.vars[k].set(v)

        editors.BlockEditorWindow(self, _on_save, initial_data, initial_params)

    def _launch_dkeff(self):
        editors.DkeffWindow(self)

    def _cgr_table_var(self, eq_idx):
        return self.vars['CGR_TABLE'] if eq_idx == 1 else self.vars[f'CGR_TABLE_{eq_idx}']

    def _launch_cgr_table_editor(self, eq_idx):
        var = self._cgr_table_var(eq_idx)
        try:
            initial = json.loads(var.get() or '[]')
        except json.JSONDecodeError:
            initial = []

        def _on_save(rows):
            var.set(json.dumps(rows))
            self._var_for('NTAB', eq_idx).set(str(len(rows)))

        editors.CrackGrowthTableDialog(self, _on_save, initial, eq_idx)

    def _show_help(self):
        if self.help_window is None or not self.help_window.winfo_exists():
            self.help_window = dialogs.HelpWindow(self)
        else:
            self.help_window.lift()
            self.help_window.focus_set()

    def _open_output_folder(self):
        if self.project.project_path:
            os.startfile(self.project.get_path("output"))

    def _add_entry(self, parent, label, var, r, c, tooltip=None):
        ttk.Label(parent, text=label).grid(row=r, column=c*2, sticky='e', padx=5, pady=5)
        e = ttk.Entry(parent, textvariable=self.vars[var], width=12)
        e.grid(row=r, column=c*2+1, sticky='w', padx=5)
        tip = tooltip if tooltip is not None else config.TOOLTIPS.get(var)
        if tip:
            widgets.ToolTip(e, tip)
        return e

    def _add_combobox(self, parent, label, var, options, r, c, tooltip=None):
        ttk.Label(parent, text=label).grid(row=r, column=c*2, sticky='e', padx=5, pady=5)
        cb = ttk.Combobox(parent, textvariable=self.vars[var], values=options,
                          state='readonly', width=max(40, max(len(o) for o in options)))
        cb.grid(row=r, column=c*2+1, columnspan=3, sticky='w', padx=5)
        tip = tooltip if tooltip is not None else config.TOOLTIPS.get(var)
        if tip:
            widgets.ToolTip(cb, tip)
        return cb


if __name__ == "__main__":
    app = FastranGui()
    app.mainloop()