# postprocessor.py
"""
postprocessor.py
----------------
Results Comparison Module for FASTRAN GUI.

Responsibilities:
1. Visualization: ComparisonWindow class for overlaying multiple analysis runs.
2. Data Aggregation: Collects results from the 'output' folder.
3. Plotting: Provides interactive plotting (Zoom, Pan, Save) via Matplotlib.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import parsers
import utils

class ComparisonWindow(tk.Toplevel):
    def __init__(self, parent, project_manager):
        """
        Args:
            parent: The main GUI window.
            project_manager: The project instance (to locate output files).
        """
        super().__init__(parent)
        self.title("Results Comparison / Post-Processor")
        self.geometry("1100x750")
        self.project = project_manager
        
        # Data Cache: Prevents re-parsing files every time we toggle a checkbox
        # Structure: {filename: {'headers': [], 'data': {col_name: [values]}}}
        self.cache = {} 
        
        # Track active files
        self.file_vars = {} # {filename: BooleanVar}
        
        self._create_layout()
        self._load_file_list()

    def _create_layout(self):
        # Main Split: Controls (Left) vs Plot (Right)
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=10, pady=10)
        
        # --- LEFT: Controls ---
        left_frame = ttk.Frame(paned, width=300)
        paned.add(left_frame, weight=1)
        
        # 1. Axis Selection
        axis_grp = ttk.LabelFrame(left_frame, text="Plot Axes", padding=10)
        axis_grp.pack(fill='x', pady=5)
        
        ttk.Label(axis_grp, text="X-Axis:").pack(anchor='w')
        self.x_var = tk.StringVar(value="CYCLES")
        self.cb_x = ttk.Combobox(axis_grp, textvariable=self.x_var, state='readonly')
        self.cb_x.pack(fill='x')
        self.cb_x.bind("<<ComboboxSelected>>", self._update_plot)
        
        ttk.Label(axis_grp, text="Y-Axis:").pack(anchor='w', pady=(5,0))
        self.y_var = tk.StringVar(value="C-LENGTH")
        self.cb_y = ttk.Combobox(axis_grp, textvariable=self.y_var, state='readonly')
        self.cb_y.pack(fill='x')
        self.cb_y.bind("<<ComboboxSelected>>", self._update_plot)

        # 2. Scale Toggles
        self.log_x = tk.BooleanVar(value=False)
        self.log_y = tk.BooleanVar(value=False)
        
        chk_frame = ttk.Frame(axis_grp)
        chk_frame.pack(fill='x', pady=5)
        ttk.Checkbutton(chk_frame, text="Log X", variable=self.log_x, command=self._update_plot).pack(side='left')
        ttk.Checkbutton(chk_frame, text="Log Y", variable=self.log_y, command=self._update_plot).pack(side='left', padx=10)

        # 3. File List (Scrollable Checkboxes)
        file_grp = ttk.LabelFrame(left_frame, text="Select Runs to Overlay", padding=10)
        file_grp.pack(fill='both', expand=True, pady=10)
        
        # Scrollbar mechanics
        canvas = tk.Canvas(file_grp, highlightthickness=0)
        scrollbar = ttk.Scrollbar(file_grp, orient="vertical", command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas)
        
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- RIGHT: Plot ---
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)
        
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.grid(True)
        self.ax.set_title("Multi-Run Comparison")
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add Standard Matplotlib Toolbar (Zoom, Pan, Save)
        toolbar = NavigationToolbar2Tk(self.canvas, right_frame)
        toolbar.update()
        toolbar.pack(side='bottom', fill='x')

    def _load_file_list(self):
        """Scans output folder for .fou files and populates checkboxes."""
        if not self.project.project_path: return
        
        out_dir = self.project.get_path("output")
        if not os.path.exists(out_dir): return
        
        # Get all output files
        files = [f for f in os.listdir(out_dir) if f.endswith(".fou")]
        # Sort by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(out_dir, x)), reverse=True)
        
        if not files:
            ttk.Label(self.scroll_frame, text="No output files found.").pack()
            return

        for f in files:
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(self.scroll_frame, text=f, variable=var, command=self._update_plot)
            chk.pack(anchor='w', pady=2)
            self.file_vars[f] = var
            
        # Select the most recent one by default so the user sees something immediately
        if files:
            self.file_vars[files[0]].set(True)
            self._update_plot()

    def _get_data(self, filename):
        """Lazy loader: Parses file only if not already in cache."""
        if filename not in self.cache:
            path = os.path.join(self.project.get_path("output"), filename)
            headers, data = parsers.parse_output_table(path)
            
            if headers and data:
                self.cache[filename] = {'headers': headers, 'data': data}
                
                # Update axis dropdowns if they are empty or generic
                # We prefer using headers from the actual data
                if 'CYCLES' not in self.cb_x['values'] or len(self.cb_x['values']) < 2:
                    self.cb_x['values'] = headers
                    self.cb_y['values'] = headers
            else:
                self.cache[filename] = None # Mark as invalid
                
        return self.cache[filename]

    def _update_plot(self, event=None):
        """Redraws the plot based on checked files and selected axes."""
        self.ax.clear()
        self.ax.grid(True)
        
        x_key = self.x_var.get()
        y_key = self.y_var.get()
        
        has_data = False
        
        # Iterate through all files
        for filename, var in self.file_vars.items():
            if var.get(): # If checked
                file_info = self._get_data(filename)
                
                if file_info:
                    data = file_info['data']
                    
                    # Ensure the selected axes exist in this file
                    if x_key in data and y_key in data:
                        self.ax.plot(data[x_key], data[y_key], label=filename, linewidth=2)
                        has_data = True
        
        if has_data:
            self.ax.set_xlabel(x_key)
            self.ax.set_ylabel(y_key)
            self.ax.legend()
            
            # Log Logic
            if self.log_x.get(): self.ax.set_xscale('log')
            if self.log_y.get(): self.ax.set_yscale('log')
            
        else:
            self.ax.text(0.5, 0.5, "Select runs to compare", ha='center', transform=self.ax.transAxes)
            
        self.canvas.draw()