# fastran_gui.py
"""
fastran_gui.py
--------------
Main application script for the FASTRAN Input Generator.

This script creates the main application window and orchestrates the interaction
between the various modules to provide the full functionality of the GUI.
This version uses a project-based workflow managed by the ProjectManager class.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import queue
import shutil
import xml.etree.ElementTree as ET
from tkinter.simpledialog import askstring

# Matplotlib for plot canvas creation
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Import all custom application modules
import config
import utils
import parsers
import widgets
import editors
import plots
import runners
from project import ProjectManager

class FastranGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FASTRAN GUI")
        self.geometry("900x800")
        
        # --- Core application state variables ---
        self.project = ProjectManager()
        self.fastran_exe_path = None
        self.dkeff_exe_path = None
        self.config_filename = "fastran_gui.cfg"
        self.log_queue = queue.Queue()
        
        # --- Data model for the analysis ---
        self._init_vars()
        self.block_data = []
        self.table_data = [['0.0', '0.0']]
        self.sif_table_data = []

        # --- UI components that need to be accessed by methods ---
        self.table_widgets = []
        self.sif_table_widgets = []
        self.plot_x_data = []
        self.plot_y_data = []

        self._load_app_config()
        self._create_widgets()
        self._update_all_states()
        
    def _init_vars(self):
        """Initializes all tk.StringVar variables from the defaults in config.py."""
        self.vars = {key: tk.StringVar(value=val) for key, val in config.DEFAULT_VALUES.items()}
        
        # Explicitly create the descriptive StringVars that are not in the defaults dictionary.
        self.vars['NALP_DESC'] = tk.StringVar()
        self.vars['NEP_DESC'] = tk.StringVar()
        self.vars['NEQN_DESC'] = tk.StringVar()
        self.vars['NTYP_DESC'] = tk.StringVar()
        self.vars['NTYP_CAT_DESC'] = tk.StringVar()
        self.vars['LTYP_DESC'] = tk.StringVar()
        self.vars['NFOPT_DESC'] = tk.StringVar()
        self.vars['IRATE_DESC'] = tk.StringVar()
        self.vars['NGC_DESC'] = tk.StringVar()
        self.vars['NODKL_DESC'] = tk.StringVar()
        self.vars['NDKTH_DESC'] = tk.StringVar()
        self.vars['NDKE_DESC'] = tk.StringVar()
        self.vars['LFAST_DESC'] = tk.StringVar()
        self.vars['KCONST_DESC'] = tk.StringVar()
        self.vars['NTCMAX_DESC'] = tk.StringVar()
        self.vars['KTH_DESC'] = tk.StringVar()
        
        # Set initial values for descriptive dropdowns
        for key in self.vars:
            if key.endswith('_DESC'):
                base_key = key.replace('_DESC', '')
                map_name = f"{base_key.lower()}_map"
                if hasattr(config, map_name):
                    self.vars[key].set(list(getattr(config, map_name).keys())[0])
       
        # Add traces to variables that control the UI state
        self.vars['NTYP_CAT_DESC'].trace_add('write', self._update_ntyp_options)
        for key in ['NALP_DESC', 'NFOPT_DESC', 'NGC_DESC', 'KTH_DESC', 'NTYP_DESC', 'LTYP_DESC', 'IRATE_DESC', 'SPECTRA']:
            self.vars[key].trace_add('write', self._update_all_states)

    def _update_ui_for_project(self):
        """Updates the GUI title and labels to reflect the loaded project."""
        if self.project.project_path:
            project_name = self.project.metadata.get("project_name", "Untitled")
            self.title(f"FASTRAN GUI - {project_name}")
            self.input_file_label.config(text=f"Project: {os.path.basename(self.project.project_path)}")
        else:
            self.title("FASTRAN GUI")
            self.input_file_label.config(text="No Project Loaded")

    def _new_project(self):
        """Creates a new FASTRAN project."""
        path = filedialog.askdirectory(title="Select a Location for the New Project Folder")
        if not path: return

        project_name = askstring("New Project", "Enter the project name:", parent=self)
        if not project_name: return

        project_path = os.path.join(path, f"{project_name}.frproj")
        
        if os.path.exists(project_path):
            messagebox.showerror("Error", "A project with this name already exists in the selected location.")
            return

        self.project.create_project(project_path, name=project_name)
        self._reset_all_fields()
        self._update_ui_for_project()
        self.status_var.set(f"Created new project: {project_name}")

    def _open_project(self):
        """Opens an existing FASTRAN project."""
        path = filedialog.askdirectory(title="Select Project Folder (.frproj)")
        if not path: return
        
        # Allow selecting the parent folder for convenience
        if not path.endswith(".frproj"):
            potential_path = os.path.join(path, os.path.basename(path) + ".frproj")
            if os.path.exists(potential_path):
                path = potential_path
            else:
                # Check if the selected folder itself contains a .frproj folder
                frproj_folders = [d for d in os.listdir(path) if d.endswith(".frproj")]
                if len(frproj_folders) == 1:
                    path = os.path.join(path, frproj_folders[0])
                else:
                    messagebox.showwarning("Open Project", "No valid .frproj folder found in the selected directory.")
                    return
        try:
            metadata, settings = self.project.load_project(path)
            
            if settings:
                for key, value in settings.items():
                    if key in self.vars:
                        self.vars[key].set(value)
            else:
                self._reset_all_fields()

            for key in self.vars:
                if key.endswith('_DESC'):
                    base_key = key.replace('_DESC', '')
                    rev_map_name = f"{base_key.lower()}_rev_map"
                    if hasattr(config, rev_map_name):
                        rev_map = getattr(config, rev_map_name)
                        code = self.vars[base_key].get()
                        self.vars[key].set(rev_map.get(code, "Unknown"))

            self._update_ui_for_project()
            self._update_all_states()
            self.status_var.set(f"Successfully loaded project: {metadata.get('project_name')}")

        except Exception as e:
            messagebox.showerror("Project Load Error", f"Failed to load project.\n{e}")
            self.project = ProjectManager()

    def _save_project(self):
        """Saves the current GUI state to the active project's settings.json."""
        if not self.project.project_path:
            messagebox.showwarning("Warning", "No project is currently loaded. Use 'New Project' or 'Open Project' first.")
            return

        try:
            current_settings = {key: var.get() for key, var in self.vars.items()}
            self.project.save_project(settings=current_settings)
            self.status_var.set("Project saved successfully.")
        except Exception as e:
            messagebox.showerror("Project Save Error", f"Failed to save project.\n{e}")

    # --- UI Creation Methods ---

    def _create_widgets(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        tools_menu = tk.Menu(menubar, tearoff=0)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        menubar.add_cascade(label="Help", menu=help_menu)

        file_menu.add_command(label="New Project...", command=self._new_project)
        file_menu.add_command(label="Open Project...", command=self._open_project)
        file_menu.add_command(label="Save Project", command=self._save_project)
        file_menu.add_separator()
        file_menu.add_command(label="Open FASTRAN Output File...", command=self._open_and_process_output)
        file_menu.add_separator()
        file_menu.add_command(label="Set FASTRAN Path...", command=self._set_fastran_path)
        file_menu.add_command(label="Set dkeff Path...", command=self._set_dkeff_path)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        
        tools_menu.add_command(label="Material Data Generator (dkeff)...", command=self._open_dkeff_window)
        tools_menu.add_command(label="Batch Convert .lkpx to dkeff Input...", command=self._batch_convert_lkpx)

        help_menu.add_command(label="Help...", command=self._show_help)
        help_menu.add_command(label="About...", command=self._show_about)

        top_frame = ttk.Frame(self, padding="5")
        top_frame.pack(side="top", fill="x", pady=5)
        self.run_button = ttk.Button(top_frame, text="Save Project & Run FASTRAN", command=self._initiate_run)
        self.run_button.pack(side="right", padx=5)
        
        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill='both', padx=5, pady=0)
        self.tab1 = ttk.Frame(notebook, padding="10")
        self.tab2 = ttk.Frame(notebook, padding="10")
        self.tab3 = ttk.Frame(notebook, padding="10")
        notebook.add(self.tab1, text='General & Material')
        notebook.add(self.tab2, text='Crack Growth')
        notebook.add(self.tab3, text='Geometry & Loading')
        
        self._create_tab1()
        self._create_tab2()
        self._create_tab3()
        
        self.status_var = tk.StringVar(value="Status: Ready. Please create or open a project.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w', padding=5)
        status_bar.pack(side="bottom", fill="x")

    def _create_entry_row(self, parent, label, var_key, row, col=0, width=15, tooltip_text=None, state=tk.NORMAL, numeric=False):
        lbl = ttk.Label(parent, text=label)
        lbl.grid(row=row, column=col*2, sticky='w', padx=5, pady=2)
        entry_options = {'textvariable': self.vars[var_key], 'width': width, 'state': state}
        if numeric:
            vcmd = (self.register(self._validate_numeric_input), '%W', '%P')
            entry_options['validate'] = 'focusout'
            entry_options['validatecommand'] = vcmd
        ent = ttk.Entry(parent, **entry_options)
        ent.grid(row=row, column=col*2+1, sticky='ew', padx=5)
        if tooltip_text:
            widgets.ToolTip(ent, text=tooltip_text)
            widgets.ToolTip(lbl, text=tooltip_text)
        return lbl, ent

    def _create_combo_row(self, parent, label, var_key, row, values, col=0, tooltip_text=None, width=15):
        lbl = ttk.Label(parent, text=label)
        lbl.grid(row=row, column=col*2, sticky='w', padx=5, pady=2)
        combo = ttk.Combobox(parent, textvariable=self.vars[var_key], values=values, state='readonly', width=width)
        combo.grid(row=row, column=col*2+1, sticky='ew', padx=5)
        if tooltip_text:
            widgets.ToolTip(combo, text=tooltip_text)
            widgets.ToolTip(lbl, text=tooltip_text)
        return lbl, combo

    def _create_tab1(self):
        lf1 = ttk.LabelFrame(self.tab1, text="Project Information", padding="10")
        lf1.pack(fill="x", pady=5)
        lf1.columnconfigure(1, weight=1)
        self.input_file_label = ttk.Label(lf1, text="No Project Loaded", relief="sunken", padding=2, anchor='w')
        self.input_file_label.grid(row=0, column=0, columnspan=2, sticky='ew', padx=5, pady=2)
        
        lf23 = ttk.LabelFrame(self.tab1, text="Loading and Material", padding="10")
        lf23.pack(fill="x", pady=5)
        lf23.columnconfigure(1, weight=1)
        nfopt_frame = ttk.Frame(lf23)
        nfopt_frame.grid(row=0, column=0, columnspan=4, sticky='ew', pady=(0, 5))
        nfopt_frame.columnconfigure(1, weight=1)
        self._create_combo_row(nfopt_frame, "Loading Option (NFOPT):", 'NFOPT_DESC', 0, list(config.nfopt_map.keys()), col=0, tooltip_text="Defines the type of spectrum loading.", width=35)
        
        spec_frame = ttk.Frame(lf23)
        spec_frame.grid(row=1, column=0, columnspan=4, sticky='ew')
        spec_frame.columnconfigure(1, weight=1)
        self.spec_label, self.spec_entry = self._create_entry_row(spec_frame, "Spectrum File:", 'SPECTRA', 0, 0, width=40, tooltip_text="Filename of the spectrum loading file.\nUsed only for NFOPT = 5, 8, 9, 10.")
        self.browse_spec_button = ttk.Button(spec_frame, text="Browse...", command=self._browse_for_spectrum_file)
        self.browse_spec_button.grid(row=0, column=2, padx=5)
        self.edit_spec_button = ttk.Button(spec_frame, text="Edit Spectrum", command=self._open_spectrum_editor, state="disabled")
        self.edit_spec_button.grid(row=0, column=3, padx=5)
        self.edit_blocks_button = ttk.Button(spec_frame, text="Edit Blocks...", command=self._open_block_editor)
        self.edit_blocks_button.grid(row=0, column=2, padx=5)
        
        mat_frame = ttk.Frame(lf23)
        mat_frame.grid(row=2, column=0, columnspan=4, sticky='ew')
        mat_frame.columnconfigure(1, weight=1)
        self._create_entry_row(mat_frame, "Material Title:", 'MAT', 0, 0, width=40, tooltip_text="Any 60-character description of the material.")
        ttk.Button(mat_frame, text="Open Material Generator...", command=self._open_dkeff_window).grid(row=0, column=2, padx=5)
        
        lf4 = ttk.LabelFrame(self.tab1, text="Material Properties", padding="10")
        lf4.pack(fill="x", pady=5)
        self._create_entry_row(lf4, "Yield Stress (SYIELD):", 'SYIELD', 0, 0, tooltip_text="Yield stress (0.2 percent offset).", numeric=True)
        self._create_entry_row(lf4, "Ultimate Strength (SULT):", 'SULT', 0, 1, tooltip_text="Ultimate tensile strength.", numeric=True)
        self._create_entry_row(lf4, "Elastic Modulus (E):", 'E', 1, 0, tooltip_text="Elastic modulus.", numeric=True)
        self._create_entry_row(lf4, "Poisson's Ratio (ETA):", 'ETA', 1, 1, tooltip_text="Poisson's ratio for plane strain.\nSet to 0 for plane stress (normally used).", numeric=True)
        self._create_entry_row(lf4, "Tensile Constraint (ALP):", 'ALP', 2, 0, tooltip_text="Tensile constraint factor.\n1.0 for plane-stress, 3.0 for plane-strain.", numeric=True)
        self._create_entry_row(lf4, "Comp. Constraint (BETAT):", 'BETAT', 2, 1, tooltip_text="Compressive constraint factor for intact material at crack tip.", numeric=True)
        self._create_entry_row(lf4, "Comp. Constraint (BETAW):", 'BETAW', 3, 0, tooltip_text="Compressive constraint factor along crack surface (or wake).", numeric=True)
        self._create_combo_row(lf4, "Constraint Opt (NALP):", 'NALP_DESC', 4, list(config.nalp_map.keys()), col=0, tooltip_text="0: Constraint factor (ALP) is constant as input.\n1: Constraint factor is variable (computed by the program).")
        self._create_combo_row(lf4, "Plasticity Opt (NEP):", 'NEP_DESC', 4, list(config.nep_map.keys()), col=1, tooltip_text="Effective SIF option.\n0: Elastic\n1: Plasticity-corrected (cyclic) - RECOMMENDED\n2: Closure-corrected (monotonic) - Use with caution")

    def _create_tab2(self):
        canvas = tk.Canvas(self.tab2, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab2, orient="vertical", command=canvas.yview)
        content_frame = ttk.Frame(canvas, padding="10")
        content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        content_frame.columnconfigure(0, weight=1)
        
        lf56 = ttk.LabelFrame(content_frame, text="Sections 5 & 6: Growth Rate & Fracture Properties", padding="10")
        lf56.grid(row=0, column=0, sticky="ew")
        self._create_combo_row(lf56, "IRATE:", 'IRATE_DESC', 0, list(config.irate_map.keys()), 0, tooltip_text="Number of crack-growth rate relations (J=1 to IRATE).", width=22)
        self.ngc_lbl, self.ngc_combo = self._create_combo_row(lf56, "NGC:", 'NGC_DESC', 0, list(config.ngc_map.keys()), 1, tooltip_text="Enable (1) or disable (0) the small-to-large crack transition.\nOnly used for IRATE=4.")
        self.crkngc_lbl, self.crkngc_entry = self._create_entry_row(lf56, "CRKNGC:", 'CRKNGC', 0, 2, tooltip_text="The crack length or depth where small-to-large crack transition occurs.", numeric=True)
        self._create_entry_row(lf56, "Coefficient (C1):", 'C1', 1, 0, tooltip_text="Crack-growth coefficient C1.", numeric=True)
        self._create_entry_row(lf56, "Power (C2):", 'C2', 1, 1, tooltip_text="Crack-growth power C2.", numeric=True)
        self._create_entry_row(lf56, "Threshold (C3):", 'C3', 2, 0, tooltip_text="Threshold constant C3.", numeric=True)
        self._create_entry_row(lf56, "Threshold (C4):", 'C4', 2, 1, tooltip_text="Threshold constant C4.", numeric=True)
        self._create_entry_row(lf56, "Fracture Tough. (C5):", 'C5', 3, 0, tooltip_text="Cyclic fracture toughness, C5.", numeric=True)
        self._create_entry_row(lf56, "Fracture Power (C6):", 'C6', 3, 1, tooltip_text="Power on fracture term, C6.", numeric=True)
        self._create_entry_row(lf56, "Threshold Power (C7):", 'C7', 4, 0, tooltip_text="Power on threshold term, C7.", numeric=True)
        self._create_entry_row(lf56, "Elastic-Plastic (KF):", 'KF', 4, 1, tooltip_text="Elastic-plastic fracture toughness, KF.", numeric=True)
        self._create_entry_row(lf56, "Toughness Param. (m):", 'M', 5, 0, tooltip_text="Fracture toughness parameter (0 <= m <= 1).", numeric=True)
        self._create_combo_row(lf56, "Equation (NEQN):", 'NEQN_DESC', 5, list(config.neqn_map.keys()), col=1, tooltip_text="Selects the crack-growth rate equation.\n0: FASTRAN equation\n1: NASGRO equation")
        
        self.lf7 = ttk.LabelFrame(content_frame, text="Section 7: Crack Growth Table & Plot", padding="10")
        self.lf7.grid(row=1, column=0, sticky="ew", pady=5)
        self.lf7.columnconfigure(1, weight=1)

        table_area_frame = ttk.Frame(self.lf7)
        table_area_frame.grid(row=0, column=0, sticky='nsew')
        table_ctrl_frame = ttk.Frame(table_area_frame)
        table_ctrl_frame.pack(fill='x', pady=2)
        ntab_lbl = ttk.Label(table_ctrl_frame, text="Num. Points (NTAB):")
        ntab_lbl.pack(side="left")
        ntab_tip = "If > 1, indicates number of points for tabular input.\nIf 0, program uses the equation from Section 6."
        ntab_spinbox = ttk.Spinbox(table_ctrl_frame, from_=0, to=100, textvariable=self.vars['NTAB'], width=5, command=self._update_table_from_ntab)
        ntab_spinbox.pack(side="left", padx=5)
        widgets.ToolTip(ntab_lbl, ntab_tip); widgets.ToolTip(ntab_spinbox, ntab_tip)
        self.ndkth_lbl = ttk.Label(table_ctrl_frame, text="NDKTH:")
        self.ndkth_lbl.pack(side="left", padx=(10, 0))
        self.ndkth_combo = ttk.Combobox(table_ctrl_frame, textvariable=self.vars['NDKTH_DESC'], values=list(config.ndkth_map.keys()), state='readonly', width=18)
        self.ndkth_combo.pack(side="left", padx=5)
        ndkth_tip = "Defines how the table is used.\n0: Direct table lookup.\n1: FASTRAN form (modifies table with threshold/fracture props).\n2: NASGRO form."
        widgets.ToolTip(self.ndkth_lbl, ntab_tip); widgets.ToolTip(self.ndkth_combo, ndkth_tip)
        
        table_action_frame = ttk.Frame(table_area_frame)
        table_action_frame.pack(fill='x', pady=5)
        ttk.Button(table_action_frame, text="Paste from Clipboard", command=self._paste_into_table).pack(side='left')
        ttk.Button(table_action_frame, text="Update Plot", command=self._update_growth_rate_plot).pack(side='left', padx=5)
        ttk.Button(table_action_frame, text="Validate Table", command=self._validate_growth_rate_table).pack(side='left', padx=5)

        table_scroll_container = ttk.Frame(table_area_frame)
        table_scroll_container.pack(fill="both", expand=True)
        table_scroll_container.config(height=250) 
        table_scroll_container.pack_propagate(False) 
        table_canvas = tk.Canvas(table_scroll_container, borderwidth=0, highlightthickness=0)
        table_scrollbar = ttk.Scrollbar(table_scroll_container, orient="vertical", command=table_canvas.yview)
        table_canvas.configure(yscrollcommand=table_scrollbar.set)
        table_scrollbar.pack(side="right", fill="y")
        table_canvas.pack(side="left", fill="both", expand=True)
        self.table_frame_container = ttk.Frame(table_canvas, padding="5")
        table_canvas.create_window((0, 0), window=self.table_frame_container, anchor="nw")
        self.table_frame_container.bind("<Configure>", lambda e: table_canvas.configure(scrollregion=table_canvas.bbox("all")))

        self.growth_rate_plot_frame = ttk.LabelFrame(self.lf7, text="da/dN vs. dK_eff", padding=5)
        self.growth_rate_plot_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
        fig_growth = Figure(figsize=(4, 4), dpi=100)
        fig_growth.set_tight_layout(True)
        self.growth_rate_ax = fig_growth.add_subplot(111)
        self.growth_rate_canvas = FigureCanvasTkAgg(fig_growth, master=self.growth_rate_plot_frame)
        self.growth_rate_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        self._redraw_table()
        
        self.lf8 = ttk.LabelFrame(content_frame, text="Section 8: Transition Parameters (NALP=1 only)", padding="10")
        self.lf8.grid(row=2, column=0, sticky="ew", pady=5)
        rate1_tip = "Crack-growth rate near the start of transition from flat-to-slant growth."
        rate2_tip = "Crack-growth rate near the end of the transition from flat-to-slant growth."
        self._create_entry_row(self.lf8, "RATE1:", 'RATE1', 0, 0, tooltip_text=rate1_tip, numeric=True)
        self._create_entry_row(self.lf8, "ALP1:", 'ALP1', 0, 1, tooltip_text="Constraint factor (alpha) at RATE1.", numeric=True)
        self._create_entry_row(self.lf8, "BETAT1:", 'BETAT1', 0, 2, tooltip_text="Compressive yielding factor (beta_t) at RATE1.", numeric=True)
        self._create_entry_row(self.lf8, "BETAW1:", 'BETAW1', 0, 3, tooltip_text="Compressive wake yielding factor (beta_w) at RATE1.", numeric=True)
        self._create_entry_row(self.lf8, "RATE2:", 'RATE2', 1, 0, tooltip_text=rate2_tip, numeric=True)
        self._create_entry_row(self.lf8, "ALP2:", 'ALP2', 1, 1, tooltip_text="Constraint factor (alpha) at RATE2.", numeric=True)
        self._create_entry_row(self.lf8, "BETAT2:", 'BETAT2', 1, 2, tooltip_text="Compressive yielding factor (beta_t) at RATE2.", numeric=True)
        self._create_entry_row(self.lf8, "BETAW2:", 'BETAW2', 1, 3, tooltip_text="Compressive wake yielding factor (beta_w) at RATE2.", numeric=True)
    
    def _create_tab3(self):
        canvas = tk.Canvas(self.tab3, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab3, orient="vertical", command=canvas.yview)
        content_frame = ttk.Frame(canvas, padding="10")
        content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        lf9 = ttk.LabelFrame(content_frame, text="Section 9: Data Output Options", padding="10")
        lf10 = ttk.LabelFrame(content_frame, text="Section 10: Specimen & Loading", padding="10")
        lf11 = ttk.LabelFrame(content_frame, text="Sections 11 & 13: Dimensions", padding="10")
        lf15 = ttk.LabelFrame(content_frame, text="Section 15: Pre-Crack Loading", padding="10")
        lf16 = ttk.LabelFrame(content_frame, text="Section 16: Special Options", padding="10")
        self.lf17 = ttk.LabelFrame(content_frame, text="Section 17: Primary Loading", padding="10")
        self.lf18 = ttk.LabelFrame(content_frame, text="Section 18: Load-Reduction Threshold Test", padding="10")
        self.conditional_frame_container = ttk.Frame(content_frame)
        self.lf12 = ttk.LabelFrame(self.conditional_frame_container, text="Section 12: Custom SIF", padding="10")
        self.lf14 = ttk.LabelFrame(self.conditional_frame_container, text="Section 14: Special Parameters", padding="10")

        nipt_tooltip = "Print interval for detailed internal states (e.g., plastic zone size).\nSet to 0 to disable this extra printout (recommended)."
        nprt_tooltip = "Print interval for the main results table (crack length vs. cycles).\nSet to 0 to use the 'DCPR' crack increment for printing."
        self._create_entry_row(lf9, "NIPT:", "NIPT", 0, 0, tooltip_text=nipt_tooltip, numeric=True)
        self._create_entry_row(lf9, "NPRT:", "NPRT", 0, 1, tooltip_text=nprt_tooltip, numeric=True)
        self._create_entry_row(lf9, "LSTEP:", "LSTEP", 1, 0, tooltip_text="Cycle counting option for variable-amplitude loading.\n1 = cycle-by-cycle, 2 = block-by-block. Typically 1.", numeric=True)
        self._create_combo_row(lf9, "NDKE:", "NDKE_DESC", 1, list(config.ndke_map.keys()), col=1, tooltip_text="Option for printing effective stress-intensity factors.\n0 = Print elastic dK. 1 = Print effective dK.")
        self._create_entry_row(lf9, "DCPR:", "DCPR", 2, 0, tooltip_text="Crack-length increment for printing results.\nUsed when NPRT is set to 0.", numeric=True)
        
        lf10.columnconfigure(1, weight=1); lf10.columnconfigure(3, weight=1)
        self._create_combo_row(lf10, "Specimen Category:", 'NTYP_CAT_DESC', 0, list(config.ntyp_categories.keys()), width=30, tooltip_text="Select a category to filter the specimen types below.")
        self.ntyp_lbl, self.ntyp_combo = self._create_combo_row(lf10, "Specimen Type (NTYP):", 'NTYP_DESC', 1, [], width=30, tooltip_text="Code that defines the geometry of the cracked component.")
        self._create_combo_row(lf10, "Loading Type (LTYP):", 'LTYP_DESC', 2, list(config.ltyp_map.keys()), tooltip_text="Code for loading type.\n0 = tension, 1 = bending, 2 = combined.")
        self._create_combo_row(lf10, "LFAST:", 'LFAST_DESC', 3, list(config.lfast_map.keys()), width=25, tooltip_text="Selects the crack-closure model. Option 0 is the standard model.")
        self._create_entry_row(lf10, "Num. Notch Elem. (NS):", 'NS', 4, tooltip_text="Number of elements used to model the notch-root radius (typically 1).", numeric=True)
        self.invert_lbl, self.invert_entry = self._create_entry_row(lf10, "INVERT:", "INVERT", 5, numeric=True)
        self.invert_tooltip = widgets.ToolTip(self.invert_entry, ""); widgets.ToolTip(self.invert_lbl, "")
        self._create_combo_row(lf10, "KCONST:", "KCONST_DESC", 6, list(config.kconst_map.keys()), tooltip_text="Loading control option.\n0 = constant stress loading, 1 = constant SIF range loading.")
        self.ntcmax_lbl, self.ntcmax_combo = self._create_combo_row(lf10, "NTCMAX:", "NTCMAX_DESC", 7, list(config.ntcmax_map.keys()))
        
        sif_ctrl_frame = ttk.Frame(self.lf12); sif_ctrl_frame.pack(fill='x', pady=2)
        ktab_tooltip = "Number of SIF data pairs for user-input table.\nIf 0, a user-defined equation in subroutine SIF99 is assumed.\nMaximum is 50."
        ktab_lbl = ttk.Label(sif_ctrl_frame, text="Num. SIF Pairs (KTAB):"); ktab_lbl.pack(side="left"); widgets.ToolTip(ktab_lbl, ktab_tooltip)
        ktab_spinbox = ttk.Spinbox(sif_ctrl_frame, from_=0, to=50, textvariable=self.vars['KTAB'], width=5, command=self._update_sif_table_from_ktab); ktab_spinbox.pack(side="left", padx=5); widgets.ToolTip(ktab_spinbox, ktab_tooltip)
        ttk.Button(sif_ctrl_frame, text="Paste from Clipboard", command=self._paste_into_sif_table).pack(side='left', padx=(10, 0))
        self.sif_table_container = ttk.Frame(self.lf12, padding="5"); self.sif_table_container.pack(fill="both", expand=True)
        self._redraw_sif_table()

        self.gamma_frame = ttk.Frame(self.lf14); self._create_entry_row(self.gamma_frame, "GAMMA (Sb/S):", "GAMMA", 0, 0, tooltip_text="Ratio of outer fiber bending stress to remote tensile stress.", numeric=True)
        self.radius_frame = ttk.Frame(self.lf14); self._create_entry_row(self.radius_frame, "Cylinder Radius:", "RADIUS", 0, 0, tooltip_text="Radius of the pressurized cylinder.", numeric=True)
        self.lap_joint_frame = ttk.Frame(self.lf14)
        self._create_entry_row(self.lap_joint_frame, "Rivet Pitch:", "RIVETS", 0, 0, tooltip_text="Rivet pitch or linear spacing.", numeric=True)
        self._create_entry_row(self.lap_joint_frame, "Rivet Load Factor (RLF1):", "RLF1", 0, 1, tooltip_text="Rivet load factor (0 to 1). RLF1 + RLF2 must equal 1.", numeric=True)
        self._create_entry_row(self.lap_joint_frame, "By-pass Load Factor (RLF2):", "RLF2", 1, 0, tooltip_text="By-pass load factor (1 to 0).", numeric=True)
        self._create_entry_row(self.lap_joint_frame, "Interference (DELTA):", "DELTA", 1, 1, tooltip_text="Change in rivet radius.", numeric=True)
        self._create_combo_row(self.lap_joint_frame, "Rivet-Load Decay (NODKL):", "NODKL_DESC", 2, list(config.nodkl_map.keys()), col=0, width=25, tooltip_text="Option for rivet-load decay due to crack growth.\n0=no decay, 1=decay used.")
        self._create_entry_row(self.lap_joint_frame, "Bending/Tension (GAMMA):", "GAMMA", 3, 0, tooltip_text="Ratio of bending stress to gross-section tensile stress for the lap-splice joint.", numeric=True)
        
        self._create_entry_row(lf11, "Width/Half-Width (W):", "W", 0, 0, tooltip_text="Enter the HALF-WIDTH for Middle-Crack Tension (NTYP=1).\nEnter the FULL-WIDTH for all other types (e.g., C(T), Single-Edge Crack).", numeric=True)
        self._create_entry_row(lf11, "Thickness (T):", "T", 0, 1, tooltip_text="Specimen thickness (t).", numeric=True)
        self._create_entry_row(lf11, "Initial Crack Len (CI):", "CI", 1, 0, tooltip_text="Initial crack length (ci). For cracks at a hole, this is c_i + r.", numeric=True)
        self._create_entry_row(lf11, "Initial Crack Dep (AI):", "AI", 1, 1, tooltip_text="Initial crack depth (ai) for surface/corner cracks.", numeric=True)
        self._create_entry_row(lf11, "Final Crack Len (CF):", "CF", 2, 0, tooltip_text="Analysis terminates when crack length exceeds this value.", numeric=True)
        self._create_entry_row(lf11, "Hole/Notch Radius (RAD):", "RAD", 2, 1, tooltip_text="Radius (r) of a circular hole or semi-circular edge notch.", numeric=True)
        self._create_entry_row(lf11, "Starter Notch Len (CN):", "CN", 3, 0, tooltip_text="Length of the starter notch (cn). If CN=CI, no pre-cracking.", numeric=True)
        self._create_entry_row(lf11, "Starter Notch Dep (AN):", "AN", 3, 1, tooltip_text="Depth of the starter notch (an).", numeric=True)
        self._create_entry_row(lf11, "Notch Half-Height (HN):", "HN", 4, 0, tooltip_text="Half-height of the starter notch (hn).", numeric=True)
        self._create_entry_row(lf11, "Fastener Radius (RADF):", "RADF", 4, 1, tooltip_text="Radius of fastener (rf). Set to 0 for open hole.\nAccounts for fastener effects on closure.", numeric=True)
        
        precrack_tip = "Constant-amplitude loading to grow crack from\nstarter notch (CN) to initial crack length (CI).\nRequired inputs, but only used if CN < CI."
        self._create_entry_row(lf15, "Max Stress (SMAX):", "SMAX", 0, 0, tooltip_text=precrack_tip, numeric=True)
        self._create_entry_row(lf15, "Min Stress (SMIN):", "SMIN", 0, 1, tooltip_text=precrack_tip, numeric=True)
        
        self._create_entry_row(lf16, "NRC:", "NRC", 0, 0, tooltip_text="0: Normal\n-1: Used with LFAST=4 for manual S'o/Smax input.", numeric=True)
        self._create_entry_row(lf16, "DVALUE:", "DVALUE", 0, 1, tooltip_text="Value for NRC option.\nIf NRC=-1, this is the S'o/Smax ratio for LFAST=4.", numeric=True)
        self._create_entry_row(lf16, "NCYCLE1:", "NCYCLE1", 1, 0, tooltip_text="Start cycle for stress history output.", numeric=True)
        self._create_entry_row(lf16, "NCYCLE2:", "NCYCLE2", 1, 1, tooltip_text="End cycle for stress history output.", numeric=True)

        self.ca_loading_frame = ttk.Frame(self.lf17)
        self._create_entry_row(self.ca_loading_frame, "Max Stress (SMAXP):", "SMAXP", 0, 0, tooltip_text="Maximum applied stress for the primary loading block.", numeric=True)
        self._create_entry_row(self.ca_loading_frame, "Min Stress (SMINP):", "SMINP", 0, 1, tooltip_text="Minimum applied stress for the primary loading block.", numeric=True)
        self._create_entry_row(self.ca_loading_frame, "Cycles (NCYCP):", "NCYCP", 1, 0, tooltip_text="Number of cycles for the primary loading block.", numeric=True)
        
        self.nfopt0_params_frame = ttk.Frame(self.lf17)
        self._create_entry_row(self.nfopt0_params_frame, "SCALE:", "SCALE", 0, 0, tooltip_text="A scale factor applied to the SMAXP and SMINP values.", numeric=True)
        
        self.standard_loading_frame = ttk.Frame(self.lf17)
        self._create_entry_row(self.standard_loading_frame, "MAXSEQ:", "MAXSEQ", 0, 0, tooltip_text="Maximum number of sequences to be run.\nFor NFOPT=1, number of blocks in the sequence.", numeric=True)
        self._create_entry_row(self.standard_loading_frame, "MAXBLK:", "MAXBLK", 0, 1, tooltip_text="Maximum number of blocks (or flights) to be run in total.", numeric=True)
        self._create_entry_row(self.standard_loading_frame, "LPRINT:", "LPRINT", 1, 0, tooltip_text="Print option for variable-amplitude load history.\n0 = no print, 1 = print loads that exceed SMAX/SMIN.", numeric=True)
        self._create_entry_row(self.standard_loading_frame, "MAXLPR:", "MAXLPR", 1, 1, tooltip_text="Maximum number of variable-amplitude load levels to be printed.", numeric=True)
        self.speak_lbl, self.speak_entry_main = self._create_entry_row(self.standard_loading_frame, "SPEAK:", "SPEAK", 2, 0, tooltip_text="Peak stress in spectrum.\nUsed as a multiplier for normalized spectra.", numeric=True)
        self.smean_lbl, self.smean_entry = self._create_entry_row(self.standard_loading_frame, "SMEAN:", "SMEAN", 2, 1, tooltip_text="Mean stress for TWIST and Mini-TWIST spectra.", numeric=True)
        self.nrep_lbl, self.nrep_ent = self._create_entry_row(self.standard_loading_frame, "NREP:", "NREP", 3, 0, tooltip_text="Number of repetitions of the spectrum (NFOPT=8 only).", numeric=True)
        self.marker_lbl, self.marker_ent = self._create_entry_row(self.standard_loading_frame, "MARKER:", "MARKER", 3, 1, tooltip_text="Marker code for the last point in the repeated block (NFOPT=8 only).", numeric=True)
        
        self.block_editor_button_frame = ttk.Frame(self.lf17)
        ttk.Button(self.block_editor_button_frame, text="Edit Loading Sequence...", command=self._open_block_editor).pack(pady=10)
        
        self._create_combo_row(self.lf18, "Test Type (KTH):", "KTH_DESC", 0, list(config.kth_map.keys()), width=25, tooltip_text="Selects the load-reduction threshold test type (0 for normal analysis).")
        self.smaxth_lbl, self.smaxth_entry = self._create_entry_row(self.lf18, "Start SMAX (SMAXTH):", "SMAXTH", 1, 0, tooltip_text="Initial maximum stress for the start of the threshold test.", numeric=True)
        self.rth_lbl, self.rth_entry = self._create_entry_row(self.lf18, "Stress Ratio (RTH):", "RTH", 1, 1, tooltip_text="Stress ratio (Smin/Smax) for the threshold test.", numeric=True)
        self.const_lbl, self.const_entry = self._create_entry_row(self.lf18, "Constant (CONST):", "CONST", 2, 0, tooltip_text="Constant K-gradient (C) for KTH=1, or dK/da for KTH=2.", numeric=True)
        self.prt_lbl, self.prt_entry = self._create_entry_row(self.lf18, "Percent (PRT):", "PRT", 2, 1, tooltip_text="Load-reduction percentage per step for KTH=3.", numeric=True)

        lf9.pack(fill="x", pady=5, anchor="n")
        lf10.pack(fill="x", pady=5, anchor="n")
        self.conditional_frame_container.pack(fill="x", anchor="n")
        lf11.pack(fill="x", pady=5, anchor="n")
        lf15.pack(fill="x", pady=5, anchor="n")
        lf16.pack(fill="x", pady=5, anchor="n")
        self.lf17.pack(fill="x", pady=5, anchor="n")
        self.lf18.pack(fill="x", pady=5, anchor="n")
        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    # --------------------------------------------------------------------------
    # Application Logic Methods (Callbacks, Handlers, etc.)
    # --------------------------------------------------------------------------

    def _reset_all_fields(self):
        """Resets all GUI variables and data structures to their default state."""
        for key, value in config.DEFAULT_VALUES.items():
            if key in self.vars:
                self.vars[key].set(value)

        # Reset dropdowns to their default option
        for key in self.vars:
            if key.endswith('_DESC'):
                base_key = key.replace('_DESC', '')
                map_name = f"{base_key.lower()}_map"
                if hasattr(config, map_name):
                    self.vars[key].set(list(getattr(config, map_name).keys())[0])

        self.table_data = [['0.0', '0.0']]
        self.vars['NTAB'].set(str(len(self.table_data)))
        self._redraw_table()
        self.block_data = []

    def _validate_numeric_input(self, widget_name, new_value):
        """Validates that input in an entry is numeric, coloring text red if not."""
        widget = self.nametowidget(widget_name)
        if not new_value or new_value == "-":
            widget.config(foreground='black')
            return True
        try:
            float(new_value)
            widget.config(foreground='black')
        except ValueError:
            widget.config(foreground='red')
        return True

    def _load_app_config(self):
        """Loads saved executable paths from the config file."""
        if not os.path.exists(self.config_filename): return
        try:
            with open(self.config_filename, 'r') as f:
                for line in f:
                    key, value = line.strip().split('=', 1)
                    if key == 'fastran_path': self.fastran_exe_path = value
                    elif key == 'dkeff_path': self.dkeff_exe_path = value
        except Exception as e:
            messagebox.showerror("Config Error", f"Failed to load configuration file.\n{e}")

    def _save_app_config(self):
        """Saves the FASTRAN and dkeff executable paths to the config file."""
        try:
            with open(self.config_filename, 'w') as f:
                if self.fastran_exe_path: f.write(f"fastran_path={self.fastran_exe_path}\n")
                if self.dkeff_exe_path: f.write(f"dkeff_path={self.dkeff_exe_path}\n")
        except Exception as e:
            messagebox.showerror("Config Error", f"Failed to save configuration file.\n{e}")

    def _set_fastran_path(self):
        """Opens a dialog to select the FASTRAN.exe and saves the path."""
        filepath = filedialog.askopenfilename(title="Select FASTRAN Executable", filetypes=(("Executable", "*.exe"), ("All Files", "*.*")))
        if filepath:
            self.fastran_exe_path = filepath
            self._save_app_config()
            self.status_var.set(f"FASTRAN path set to: {self.fastran_exe_path}")

    def _set_dkeff_path(self):
        """Opens a dialog to select the dkeff.exe and saves the path."""
        filepath = filedialog.askopenfilename(title="Select dkeff Executable", filetypes=(("Executable", "*.exe"), ("All Files", "*.*")))
        if filepath:
            self.dkeff_exe_path = filepath
            self._save_app_config()
            self.status_var.set(f"dkeff path set to: {self.dkeff_exe_path}")

    def _show_help(self):
        """Opens the help window."""
        widgets.HelpWindow(self)

    def _on_spectrum_created(self, filename):
        """Callback for when the spectrum editor saves a file."""
        if filename:
            self.vars['SPECTRA'].set(filename)
            if self.project.project_path:
                self.spectrum_full_path = os.path.join(os.path.dirname(self.project.get_path("input")), filename)

    def _on_blocks_saved(self, returned_data):
        """Callback for when the block editor is closed."""
        params = returned_data.get('params', {})
        self.block_data = returned_data.get('blocks', [])
        for key, value in params.items():
            if key in self.vars:
                self.vars[key].set(value)
        self.status_var.set(f"Updated with {len(self.block_data)} loading blocks.")

    def _open_and_process_output(self):
        """Opens and processes a FASTRAN output file for the post-processing dashboard."""
        filepath = filedialog.askopenfilename(
            title="Open FASTRAN Output File",
            filetypes=(
                ("FASTRAN Output", "*.fou *.txt"), 
                ("All Files", "*.*")
            )
        )
        if not filepath: return
        
        header, data, summary_dict, parsed_input_params = parsers.parse_project_output_file(filepath)
        
        final_input_params = parsed_input_params
        if self.project.project_path:
             key_inputs_from_gui = {
                "Material Name": self.vars['MAT'].get(),
                "Spectrum Name": self.vars['SPECTRA'].get(),
                "Specimen Type (NTYP)": config.ntyp_rev_map.get(self.vars['NTYP'].get(), "Unknown"),
                "Loading Option (NFOPT)": config.nfopt_rev_map.get(self.vars['NFOPT'].get(), "Unknown"),
                "Max Stress": self.vars['SMAX'].get(),
                "Initial Crack Len (CI)": self.vars['CI'].get(),
                "Initial Crack Dep (AI)": self.vars['AI'].get(),
                "Width/Half-Width (W)": self.vars['W'].get(),
                "Thickness (T)": self.vars['T'].get(),
                "Tensile Constraint (ALP)": self.vars['ALP'].get()
            }
             final_input_params = {**key_inputs_from_gui, **parsed_input_params}

        if header and data and summary_dict:
            editors.PostProcessingWindow(self, header, data, final_input_params, summary_dict)
        else:
            messagebox.showerror("Error", "Could not parse the selected output file. It may be incomplete or incorrectly formatted.", parent=self)
            
    def _update_all_states(self, *args):
        """Calls all individual state-updating methods."""
        self._update_nalp_widgets()
        self._update_irate_widgets()
        self._update_ntyp_widgets()
        self._update_kth_widgets()
        self._update_nfopt_widgets()

    def _update_ntyp_options(self, *args):
        """Updates the NTYP combobox based on the selected category."""
        category = self.vars['NTYP_CAT_DESC'].get()
        filtered_types = config.ntyp_categories.get(category, [])
        self.ntyp_combo['values'] = filtered_types
        if filtered_types and self.vars['NTYP_DESC'].get() not in filtered_types:
            self.vars['NTYP_DESC'].set(filtered_types[0])

    def _update_nalp_widgets(self):
        """Shows or hides the transition parameters frame based on NALP."""
        is_variable = config.nalp_map.get(self.vars['NALP_DESC'].get()) == '1'
        self.lf8.grid() if is_variable else self.lf8.grid_remove()

    def _update_irate_widgets(self):
        """Enables or disables widgets related to the IRATE=4 option."""
        is_irate4 = config.irate_map.get(self.vars['IRATE_DESC'].get()) == '4'
        state = tk.NORMAL if is_irate4 else tk.DISABLED
        for widget in [self.ngc_lbl, self.ngc_combo, self.crkngc_lbl, self.crkngc_entry]:
            widget.config(state=state)
        if not is_irate4:
            self.vars['NGC_DESC'].set(config.ngc_rev_map['0'])
        is_ngc_enabled = config.ngc_map.get(self.vars['NGC_DESC'].get()) == '1'
        self.crkngc_entry.config(state=tk.NORMAL if (is_irate4 and is_ngc_enabled) else tk.DISABLED)

    def _update_ntyp_widgets(self):
        """Shows or hides special geometry frames based on NTYP."""
        ntyp_code = config.ntyp_map.get(self.vars['NTYP_DESC'].get())
        ltyp_code = config.ltyp_map.get(self.vars['LTYP_DESC'].get())
        
        self.lf12.pack_forget(); self.gamma_frame.pack_forget(); self.radius_frame.pack_forget(); self.lap_joint_frame.pack_forget()
        
        show_lf14 = False
        if ntyp_code in ['99', '-99']: self.lf12.pack(fill="x", pady=5, anchor="n")
        if ntyp_code == '5': self.radius_frame.pack(fill='x'); show_lf14=True
        elif ntyp_code in ['-12', '-13']: self.lap_joint_frame.pack(fill='x'); show_lf14=True
        elif (ntyp_code in ['0', '7'] and ltyp_code == '2'): self.gamma_frame.pack(fill='x'); show_lf14=True
        
        self.lf14.pack(fill="x", pady=5, anchor="n") if show_lf14 else self.lf14.pack_forget()

    def _update_kth_widgets(self):
        """Enables or disables threshold test parameters based on KTH selection."""
        kth_code = config.kth_map.get(self.vars['KTH_DESC'].get(), '0')
        smaxth_state = tk.NORMAL if kth_code in ['1', '2', '3', '4'] else tk.DISABLED
        const_state = tk.NORMAL if kth_code in ['1', '2'] else tk.DISABLED
        prt_state = tk.NORMAL if kth_code == '3' else tk.DISABLED
        for widget in [self.smaxth_lbl, self.smaxth_entry, self.rth_lbl, self.rth_entry]: widget.config(state=smaxth_state)
        for widget in [self.const_lbl, self.const_entry]: widget.config(state=const_state)
        for widget in [self.prt_lbl, self.prt_entry]: widget.config(state=prt_state)
        
    def _update_nfopt_widgets(self):
        """Updates the primary loading section based on the NFOPT selection."""
        nfopt_code = config.nfopt_map.get(self.vars['NFOPT_DESC'].get(), '0')
        is_file_based = nfopt_code in ['5', '8', '9', '10']
        is_block_based = nfopt_code == '1'

        for w in [self.spec_entry, self.spec_label, self.browse_spec_button, self.edit_spec_button, self.edit_blocks_button, self.ca_loading_frame, self.nfopt0_params_frame, self.standard_loading_frame, self.block_editor_button_frame]:
            if hasattr(w, 'pack_forget'): w.pack_forget()
            if hasattr(w, 'grid_forget'): w.grid_forget()

        self.spec_entry.config(state=tk.NORMAL if is_file_based else tk.DISABLED)
        self.browse_spec_button.grid() if is_file_based else self.browse_spec_button.grid_remove()
        self.edit_spec_button.grid() if is_file_based else self.edit_spec_button.grid_remove()
        self.edit_blocks_button.grid() if is_block_based else self.edit_blocks_button.grid_remove()

        if nfopt_code == '0':
            self.standard_loading_frame.pack(fill='x'); self.nfopt0_params_frame.pack(fill='x'); self.ca_loading_frame.pack(fill='x')
        elif nfopt_code == '1':
            self.block_editor_button_frame.pack(fill='x')
        else:
            self.standard_loading_frame.pack(fill='x')

        show_speak = nfopt_code in ['4', '5', '6', '7', '8', '9', '10']
        show_smean = nfopt_code in ['2', '3', '6']
        show_nrep = nfopt_code == '8'
        for w in [self.speak_lbl, self.speak_entry_main]: w.grid() if show_speak else w.grid_remove()
        for w in [self.smean_lbl, self.smean_entry]: w.grid() if show_smean else w.grid_remove()
        for w in [self.nrep_lbl, self.nrep_ent, self.marker_lbl, self.marker_ent]: w.grid() if show_nrep else w.grid_remove()

    def _run_validation_checks(self):
        """Performs basic validation before saving or running."""
        try:
            if utils.safe_float(self.vars['CF'].get()) <= utils.safe_float(self.vars['CI'].get()):
                messagebox.showerror("Validation Error", "Final crack length (CF) must be greater than initial (CI).")
                return False
        except Exception as e:
            messagebox.showerror("Validation Error", f"Invalid numeric value in input fields: {e}")
            return False
        return True

    def _browse_for_spectrum_file(self):
        """Opens a file dialog to select an external spectrum file and copies it to the project."""
        if not self.project.project_path:
            messagebox.showwarning("Warning", "Please open or create a project first.", parent=self)
            return
    
        filepath = filedialog.askopenfilename(
            title="Select External Spectrum File to Import",
            filetypes=(("Spectrum Files", "*.txt *.spx *.sub"), ("All Files", "*.*"))
        )
        if not filepath: return
        
        try:
            # Copy the selected file into the project's input directory
            destination_folder = self.project.get_path("input")
            destination_path = os.path.join(destination_folder, os.path.basename(filepath))
            shutil.copy(filepath, destination_path)
            
            # Update the GUI to use the newly copied file
            self.vars['SPECTRA'].set(os.path.basename(destination_path))
            self.status_var.set(f"Imported and linked spectrum file: {os.path.basename(destination_path)}")
    
        except Exception as e:
            messagebox.showerror("Import Error", f"Could not copy spectrum file into project.\n\nError: {e}", parent=self)
    
    def _initiate_run(self):
        if not self.project.project_path:
            messagebox.showerror("Error", "Cannot run without an active project. Please create or open a project.")
            return
        self._save_project()
        current_values = {key: var.get() for key, var in self.vars.items()}
        current_table_data = [[w.get() for w in row] for row in self.table_widgets]
        input_file_path = self.project.get_path("input")
        if not input_file_path.endswith('.fin'): input_file_path = os.path.splitext(input_file_path)[0] + '.fin'
        success = parsers.generate_fastran_file(self.project, current_values, current_table_data, self.block_data, config.__dict__)
        if not success:
            self.status_var.set("Status: Failed to generate input file. Aborting run."); return
        if not self.fastran_exe_path or not os.path.exists(self.fastran_exe_path):
            messagebox.showwarning("Setup Required", "Path to FASTRAN.exe is not set."); return
        self.run_button.config(state="disabled"); self.status_var.set("Status: Running FASTRAN...")
        self.plot_x_data.clear(); self.plot_y_data.clear()
        is_realtime_plot = utils.safe_int(self.vars['NPRT'].get()) <= 0
        self._create_log_window(show_realtime_features=is_realtime_plot)
        runners.run_fastran(self.project, self.fastran_exe_path, self.log_queue)
        self.after(100, self._process_log_queue)

    def _process_log_queue(self):
        try:
            while True:
                line = self.log_queue.get_nowait()
                if line is None: # Sentinel value
                    self.run_button.config(state="normal")
                    self.status_var.set("Status: FASTRAN run finished.")
                    header, data, summary_dict, parsed_inputs = parsers.parse_project_output_file(self.project)
                    if header and data:
                        gui_inputs = { "Specimen Type (NTYP)": config.ntyp_rev_map.get(self.vars['NTYP'].get(), "Unknown"), "Loading Option (NFOPT)": config.nfopt_rev_map.get(self.vars['NFOPT'].get(), "Unknown"), "Max Stress": self.vars['SMAX'].get(), "Initial Crack Len (CI)": self.vars['CI'].get(), "Initial Crack Dep (AI)": self.vars['AI'].get(), "Width/Half-Width (W)": self.vars['W'].get(), "Thickness (T)": self.vars['T'].get(), "Tensile Constraint (ALP)": self.vars['ALP'].get() }
                        final_params = {**gui_inputs, **parsed_inputs}
                        editors.PostProcessingWindow(self, header, data, final_params, summary_dict)
                    return
                elif "ERROR" in line: self.log_text.insert(tk.END, line, 'error')
                else:
                    self.log_text.insert(tk.END, line)
                    if self._update_plot_data_from_log_line(line): self._update_realtime_plot()
                self.log_text.see(tk.END)
        except queue.Empty:
            self.after(100, self._process_log_queue)

    def _create_log_window(self, show_realtime_features=True):
        log_window = tk.Toplevel(self); log_window.title("FASTRAN Output Log"); log_window.geometry("800x600"); log_window.transient(self)
        paned_window = ttk.PanedWindow(log_window, orient=tk.VERTICAL); paned_window.pack(fill='both', expand=True)
        text_frame = ttk.Frame(paned_window); paned_window.add(text_frame, weight=2)
        self.log_text = tk.Text(text_frame, wrap='word', font=("Courier", 9)); scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set); self.log_text.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y"); self.log_text.tag_config('error', foreground='red')
        if show_realtime_features:
            plot_frame = ttk.Frame(paned_window); paned_window.add(plot_frame, weight=1)
            fig = Figure(dpi=100); fig.set_tight_layout(True)
            self.realtime_ax = fig.add_subplot(111); self.realtime_canvas = FigureCanvasTkAgg(fig, master=plot_frame)
            self.realtime_canvas.get_tk_widget().pack(fill='both', expand=True); self._update_realtime_plot()
        else: self.realtime_ax = None; self.realtime_canvas = None

    def _update_plot_data_from_log_line(self, line):
        try:
            parts = line.split()
            if len(parts) > 4 and utils.safe_float(parts[0], None) is not None:
                crack_len = utils.safe_float(parts[1]); cycles = utils.safe_float(parts[3])
                if cycles > 0 and crack_len > 0: self.plot_x_data.append(cycles); self.plot_y_data.append(crack_len); return True
        except (ValueError, IndexError): pass
        return False
        
    def _update_realtime_plot(self):
        if not hasattr(self, 'realtime_ax') or not self.realtime_ax: return
        plots.plot_real_time_growth(self.realtime_ax, self.plot_x_data, self.plot_y_data)
        if hasattr(self, 'realtime_canvas'): self.realtime_canvas.draw()
            
    def _update_growth_rate_plot(self, event=None):
        current_table_data = [[w.get() for w in row] for row in self.table_widgets]
        plots.plot_growth_rate(self.growth_rate_ax, current_table_data)
        self.growth_rate_canvas.draw()
            
    def _redraw_table(self):
        for widget in self.table_frame_container.winfo_children(): widget.destroy()
        self.table_widgets = []
        ttk.Label(self.table_frame_container, text="dK_eff", font="-weight bold").grid(row=0, column=0, padx=5, pady=2)
        ttk.Label(self.table_frame_container, text="da/dN", font="-weight bold").grid(row=0, column=1, padx=5, pady=2)
        for i, data_row in enumerate(self.table_data):
            dkeff, rate = data_row
            dkeff_entry = ttk.Entry(self.table_frame_container, width=15); dkeff_entry.insert(0, dkeff); dkeff_entry.grid(row=i + 1, column=0, padx=5, pady=2)
            dkeff_entry.bind("<FocusOut>", self._update_growth_rate_plot)
            rate_entry = ttk.Entry(self.table_frame_container, width=15); rate_entry.insert(0, rate); rate_entry.grid(row=i + 1, column=1, padx=5, pady=2)
            rate_entry.bind("<FocusOut>", self._update_growth_rate_plot)
            self.table_widgets.append([dkeff_entry, rate_entry])
        self._update_growth_rate_plot()

    def _validate_growth_rate_table(self):
        last_dkeff, last_rate = -float('inf'), -float('inf'); is_valid = True
        style = ttk.Style(); style.configure('Invalid.TEntry', foreground='red')
        for row in self.table_widgets:
            row_is_valid = True
            try:
                dkeff, rate = float(row[0].get()), float(row[1].get())
                if dkeff <= last_dkeff or rate <= last_rate: row_is_valid = False
                last_dkeff, last_rate = dkeff, rate
            except ValueError: row_is_valid = False
            for widget in row: widget.config(style='TEntry' if row_is_valid else 'Invalid.TEntry')
            if not row_is_valid: is_valid = False
        messagebox.showinfo("Validation", "Table is valid." if is_valid else "Validation Failed: Values must be numeric and in ascending order.", parent=self.lf7)

    def _update_table_from_ntab(self):
        try:
            new_size = int(self.vars['NTAB'].get())
            if new_size < 0: return
            current_table_data = [[w.get() for w in row] for row in self.table_widgets]
            while len(current_table_data) < new_size: current_table_data.append(['0.0', '0.0'])
            self.table_data = current_table_data[:new_size]
            self._redraw_table()
        except (tk.TclError, ValueError): pass

    def _paste_into_table(self):
        try:
            clipboard_data = self.clipboard_get().strip().split('\n')
            pasted_data = [line.split()[:2] for line in clipboard_data if line]
            if not pasted_data: return
            self.table_data = pasted_data
            self.vars['NTAB'].set(str(len(pasted_data)))
            self._redraw_table()
        except (tk.TclError, ValueError):
            messagebox.showerror("Paste Error", "Could not parse data from clipboard. Ensure it is two-column, tab- or space-separated data.", parent=self.lf7)

    def _redraw_sif_table(self):
        for widget in self.sif_table_container.winfo_children(): widget.destroy()
        self.sif_table_widgets = []
        ttk.Label(self.sif_table_container, text="c/w", font="-weight bold").grid(row=0, column=0, padx=5, pady=2)
        ttk.Label(self.sif_table_container, text="Fc", font="-weight bold").grid(row=0, column=1, padx=5, pady=2)
        for i, data_row in enumerate(self.sif_table_data):
            cw, fc = data_row
            cw_entry = ttk.Entry(self.sif_table_container, width=15); cw_entry.insert(0, cw); cw_entry.grid(row=i + 1, column=0, padx=5, pady=2)
            fc_entry = ttk.Entry(self.sif_table_container, width=15); fc_entry.insert(0, fc); fc_entry.grid(row=i + 1, column=1, padx=5, pady=2)
            self.sif_table_widgets.append([cw_entry, fc_entry])

    def _update_sif_table_from_ktab(self):
        try:
            new_size = int(self.vars['KTAB'].get())
            if new_size < 0: return
            current_table_data = [[w.get() for w in row] for row in self.sif_table_widgets]
            while len(current_table_data) < new_size: current_table_data.append(['0.0', '0.0'])
            self.sif_table_data = current_table_data[:new_size]
            self._redraw_sif_table()
        except (ValueError, tk.TclError): pass

    def _paste_into_sif_table(self):
        try:
            clipboard_data = self.clipboard_get().strip().split('\n')
            pasted_data = [line.split()[:2] for line in clipboard_data if line]
            if not pasted_data: return
            self.sif_table_data = pasted_data
            self.vars['KTAB'].set(str(len(pasted_data)))
            self._redraw_sif_table()
        except (tk.TclError, ValueError):
            messagebox.showerror("Paste Error", "Could not parse SIF data from clipboard. Ensure it is two-column, tab- or space-separated data.", parent=self.lf12)

    def _open_dkeff_window(self):
        if not self.dkeff_exe_path:
            messagebox.showinfo("Path Required", "Please set the path to dkeff.exe first.", parent=self)
            self._set_dkeff_path()
        if self.dkeff_exe_path:
            editors.DkeffWindow(self)

    def _open_spectrum_editor(self):
        """Opens the project-aware spectrum editor window."""
        if not self.project.project_path:
            messagebox.showwarning("Warning", "Please open or create a project first.", parent=self)
            return
        
        spectrum_filename = self.vars['SPECTRA'].get()
        editors.SpectrumCreatorWindow(self, self._on_spectrum_created, self.project, spectrum_filename)

    def _open_block_editor(self):
        initial_params = {
            'MAXSEQ': self.vars['MAXSEQ'].get(), 'MAXBLK': self.vars['MAXBLK'].get(),
            'LPRINT': self.vars['LPRINT'].get(), 'MAXLPR': self.vars['MAXLPR'].get(),
            'SCALE': self.vars.get('SCALE', '1.0')
        }
        editors.BlockEditorWindow(self, self._on_blocks_saved, self.block_data, initial_params)

    def _batch_convert_lkpx(self):
        lkpx_path = filedialog.askopenfilename(title="Select .lkpx Material File", filetypes=(("Material Files", "*.lkpx"), ("All Files", "*.*")))
        if not lkpx_path: return
        try:
            tree = ET.parse(lkpx_path)
            root = tree.getroot()
            self.vars['MAT'].set(root.findtext('.//Material/Name', ''))
            self.vars['SYIELD'].set(root.findtext('.//PropertyData[@property="yld"]/Data', '0.0'))
            self.vars['SULT'].set(root.findtext('.//PropertyData[@property="ult_strength"]/Data', '0.0'))
            self.vars['E'].set(root.findtext('.//PropertyData[@property="e"]/Data', '0.0'))
            
            datasets = root.findall('.//DataSet')
            self.r_ratio_options = {}
            for ds in datasets:
                r_ratio_node = ds.find("./var[@id='Stress Ratio']")
                if r_ratio_node is not None:
                    r_ratio = float(r_ratio_node.get('val'))
                    data_table_node = ds.find('./DataTable/Data')
                    if data_table_node is not None:
                        table = []
                        for row in data_table_node.findall('row'):
                            dk_eff_node = row.find("./FieldData[@pos='1']")
                            dadn_node = row.find("./FieldData[@pos='2']")
                            if dk_eff_node is not None and dadn_node is not None:
                                table.append([dk_eff_node.text, dadn_node.text, ''])
                        self.r_ratio_options[r_ratio] = table
            
            if not self.r_ratio_options:
                messagebox.showerror("Error", "No valid R-ratio datasets found in the .lkpx file.", parent=self)
                return

            dialog = editors.BatchInputDialog(self, list(self.r_ratio_options.keys()))
            if not dialog.result: return

            save_dir = filedialog.askdirectory(title="Select Folder to Save .dkin Files")
            if not save_dir: return

            progress_window = widgets.ProgressWindow(self, title="Batch Processing...", message="Generating .dkin files...")
            progress_window.start()
            
            for r_ratio, params in dialog.result.items():
                smax, w, t = params
                filename = f"{self.vars['MAT'].get()}_R{r_ratio}.dkin"
                self._generate_dkin_file(save_dir, filename, r_ratio, smax, w, t)

            progress_window.stop()
            messagebox.showinfo("Success", f"Successfully generated {len(dialog.result)} .dkin files in:\n{save_dir}")

        except Exception as e:
            messagebox.showerror("Batch Convert Error", f"An error occurred: {e}", parent=self)

    def _generate_dkin_file(self, directory, filename, r_ratio, smax, w, t):
        filepath = os.path.join(directory, filename)
        table = self.r_ratio_options.get(r_ratio)
        if not table: return

        lines = [
            f"dkeff input from {filename}",
            f" {self.vars['MAT'].get()}",
            "2  0", # NTYP=2 (C(T)), LUNIT=0
            f" {self.vars['SYIELD'].get()}  {self.vars['SULT'].get()}  {self.vars['E'].get()}  0  0  1.8  1",
            f" {len(table)}  {r_ratio}  {smax}  {w}  {t}"
        ]
        for i, row_data in enumerate(table, 1):
            lines.append(f"  {i} {row_data[0]} {row_data[1]} {row_data[2]}")
        
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))

    def _show_about(self):
        about_text = (
            "FASTRAN GUI v3.0 (Modular)\n\n"
            "This application provides a graphical user interface for the\n"
            "FASTRAN fatigue crack growth analysis code.\n\n"
            "Developed using Python and Tkinter.\n"
            "Refactoring assistance by an AI model."
        )
        messagebox.showinfo("About FASTRAN GUI", about_text)

if __name__ == "__main__":
    app = FastranGui()
    app.mainloop()