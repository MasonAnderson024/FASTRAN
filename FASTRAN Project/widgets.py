# widgets.py
"""
widgets.py
----------
Custom reusable Tkinter widgets for the FASTRAN GUI. This module contains
self-contained UI components like help windows, progress bars, and tooltips.
"""

import tkinter as tk
from tkinter import ttk, messagebox

# NOTE: For easier maintenance in the future, you could move this large
# help text block into its own separate file (e.g., 'help_guide.txt')
# and read it from there. For now, embedding it is fine.
HELP_CONTENT = """
================================
 FASTRAN GUI - Quick Help Guide
================================

This guide provides a simplified explanation of the input fields available in the GUI.
For more detailed information, please consult the "Short-User Guide-FASTRAN Ver.5.78f.pdf".

-----------------------------------------------------------------------------
  Tab 1: General & Material
-----------------------------------------------------------------------------

[ Spectrum & Material Files ]

  Spectrum File (SPECTRA)
  - The filename of the spectrum loading file.
  - This is only used when the Loading Option (NFOPT) is set to 5, 8, 9, or 10.
  - For all other loading options, you can use a cstamp filename (e.g., cstamp.txt).
  
  *Important:* If you select a loading option that uses a spectrum file 
  (NFOPT 5, 8, 9, or 10), you must provide a path to a correctly formatted spectrum 
  file. Using the default cstamp.txt will cause the analysis to fail.

  Material Title (MAT)
  - A descriptive name for the material (up to 60 characters).

[ Material Properties ]

  Yield Stress (SYIELD)
  - The stress at which the material begins to deform plastically (0.2% offset).

  Ultimate Strength (SULT)
  - The maximum stress a material can withstand before breaking.

  Elastic Modulus (E)
  - A measure of the material's stiffness.

  Poisson's Ratio (ETA)
  - Describes the material's tendency to deform in perpendicular directions when stretched.
  - Use 0 for plane stress conditions.
  
  *Note on Stress Limits:* FASTRAN calculates a Flow Stress (Sflow) as the average of 
  the Yield and Ultimate strengths. Ensure your maximum applied stress (Smax) in any 
  loading sequence is less than this value to avoid calculation errors.

[ Constraint Factors ]

  Tensile Constraint (ALP)
  - A factor that defines the state of stress at the crack tip.
  - Common values: 1.0 for plane stress, 3.0 for plane strain.

  Compressive Constraint (BETAT / BETAW)
  - Factors for compressive yielding. BETAT is for the material ahead of the 
    crack tip, and BETAW is for the material in the crack wake.

[ Material Options ]

  Constraint Opt (NALP)
  - Defines how the constraint factor (ALP) is treated.
  - 0: Constant -> Uses the user-input ALP value throughout the analysis.
  - 1: Variable -> The program calculates a variable ALP based on crack growth rates.

  Plasticity Opt (NEP)
  - Defines the plasticity correction method for the stress intensity factor.
  - 0: Elastic -> No plasticity correction.
  - 1: Plasticity-Corrected -> Modifies the crack length by adding a portion of 
    the *cyclic* plastic zone. (RECOMMENDED)
  - 2: Closure Corrected -> Modifies the crack length by adding a portion of the 
    *monotonic* plastic zone. (Use with caution)

-----------------------------------------------------------------------------
  Tab 2: Crack Growth
-----------------------------------------------------------------------------

[ Growth Rate Options ]

  IRATE
  - Defines the number of crack growth rate curves to use.
  - 1: One curve for both crack length and depth.
  - 2: Two independent curves (one for length, one for depth).
  - 4: Four independent curves (small and large cracks for both length and depth).

  NGC / CRKNGC
  - Enables the transition from small-crack to large-crack behavior 
    (only used when IRATE=4).
  - NGC=1 enables the transition.
  - CRKNGC is the crack size at which the transition occurs.

[ Growth Rate Equation & Properties ]

  C1-C7, KF, m
  
  Steady Crack Growth
  - C1: Scaling constant that defines the vertical position of the crack-growth
    plot line; a higher C1 means faster growth for a given stress level
  - C2: Slope of the central, straight-line portion of the da/dN vs dKeff line
    on a log-log plot

 Threshold Behavior: Define Crack Growth Threshold (dK0)
  - C3: Baseline threshold
  - C4: Adjusts the baseline based on stress ratio (R)
  - C7: Controls how sharply the curve bends as it approaches threshold; a high
    value creates an abrupt "knee" where crack growth rates plumit to 0

 Fracture Behavior
  - C5: Cyclic toughness
  - C6: Fracture power; controls how abruptly the crack growth rate accelerates
    as Kmax approaches C5
  - KF: Elastic-plastic fracture toughness
  - m: Accounts for geometry and stress state of the componenet

  Equation (NEQN)
  - Selects the crack growth law to be used.
  - 0: FASTRAN Equation
  - 1: NASGRO Equation

[ Crack Growth Table (NTAB > 0) ]

  Num. Points (NTAB)
  - If greater than 1, the program will use a table of (dK_eff, da/dN) data 
    instead of the equation. NTAB is the number of points in the table.

  NDKTH
  - Defines how the table data is interpreted and applied.
  - 0: Direct table lookup.
  - 1: FASTRAN tabular form, which modifies the table data with threshold and 
    fracture properties.
  - 2: NASGRO tabular form, similar to option 1 but uses a different formulation.

[ Transition Parameters (NALP = 1 only) ]

  RATE1, ALP1, RATE2, ALP2, etc.
  - These parameters define the crack growth rates (RATE1, RATE2) at which the 
    transition from flat-to-slant crack growth occurs, and the corresponding 
    constraint factors (ALP1, ALP2).
 
 *Important:* The data in this table must be in strictly ascending order for both 
 the dK_eff and da/dN columns. Duplicate or decreasing values will cause an error in FASTRAN.

-----------------------------------------------------------------------------
  Tab 3: Geometry & Loading
-----------------------------------------------------------------------------

[ Specimen & Crack Geometry ]

  Specimen Type (NTYP)
  - Defines the geometry of the cracked component (e.g., Center Crack, Surface Crack, Crack at Hole).

  W, T, CI, AI, CF, RAD
  - W: Width (or half-width for middle-crack tension specimens)
  - T: Thickness
  - CI: Initial crack length
  - AI: Initial crack depth (for surface/corner cracks)
  - CF: Final crack length at which the analysis stops.
  - RAD: Radius of a hole or notch.

  CN, AN, HN
  - Dimensions of the starter notch from which a crack initiates.
  - If CN = CI, there is no pre-cracking stage.

[ Loading ]

  Loading Option (NFOPT)
  - Defines the type of loading to be applied.
  - 0: Constant-Amplitude (simple max/min loading).
  - 1: Variable/Block Loading (user-defined blocks of loads).
  - 2-7, 10: Standardized spectra (e.g., TWIST, FALSTAFF).
  - 8, 9: Spectra read from an external file.

  Pre-Crack Loading (SMAX / SMIN)
  - The constant-amplitude max and min stress levels used to grow the crack 
    from the initial notch (CN) to the initial crack size (CI).
  - These inputs are required but are only used if CN is different from CI.

  Primary Loading (MAXSEQ, SPEAK, SMEAN, etc.)
  - These fields control the application of the primary fatigue loading defined by NFOPT.
  - SPEAK: The highest stress in a spectrum, used to scale the spectrum data.
  - SMEAN: The mean stress for certain spectra like TWIST.
  - MAXSEQ: Total number of blocks or flights in a sequence.

[ Output & Advanced Options ]

  Output Options
  These parameters control how frequently the results are printed to the output 
    file. There are two main methods: printing by analysis step (NPRT) or printing 
      by a physical crack increment (DCPR).

  NPRT (Print by Step Interval)
  - If NPRT > 0: The program will print a line of results every NPRT-th analysis increment.
  - If NPRT = 0: The program switches to printing based on the crack length, 
    using the DCPR value below. This is the recommended mode for smooth real-time plotting.

  DCPR (Print by Crack Increment)
  - Defines the specific crack length increment (e.g., 0.01) at which results are printed.
  - This is only active when NPRT is set to 0.

  Detailed Internal Log (For Debugging)
  These parameters control an optional, highly detailed log for advanced 
  analysis and debugging. For most runs, these can be ignored.

  NIPT (Internal Log Activation)
  - If NIPT > 0: Enables the detailed log, which prints internal data like 
    plastic zone size and contact stresses.
  - If NIPT = 0: Disables this detailed log. This is the normal setting.

  LSTEP (Internal Log Detail)
  - Defines how many load steps are shown within the detailed NIPT log.
  - This is only active when NIPT is greater than 0.
  
  LFAST
  - Selects the crack-closure model. Option 0 is the standard, most common choice.

  Threshold Test (KTH)
  - Enables a load-reduction threshold test instead of a standard fatigue analysis.
  - This is a special-purpose test, and should typically be left at 0 for normal analyses.
"""

class HelpWindow(tk.Toplevel):
    """
    A separate Toplevel window for displaying help content with search functionality.
    """
    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.title("FASTRAN GUI - Help")
        self.geometry("800x650")

        self.last_search_query = ""
        self.last_match_end = "1.0"

        # --- Search Frame ---
        search_frame = ttk.Frame(self, padding="5")
        search_frame.pack(fill='x', side='bottom')

        ttk.Label(search_frame, text="Search:").pack(side='left', padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side='left', fill='x', expand=True)
        self.find_button = ttk.Button(search_frame, text="Find Next", command=self.find_next)
        self.find_button.pack(side='left', padx=5)
        self.reset_button = ttk.Button(search_frame, text="Reset", command=self.reset_search)
        self.reset_button.pack(side='left', padx=5)

        # --- Text Area with Scrollbar ---
        text_container = ttk.Frame(self)
        text_container.pack(fill='both', expand=True)
        self.text_widget = tk.Text(text_container, wrap='word', undo=False, font=("tahoma", "9"))
        scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        self.text_widget.pack(side="left", fill="both", expand=True, padx=(5,0), pady=5)
        scrollbar.pack(side="right", fill="y", padx=(0,5), pady=5)
        
        self.text_widget.insert('1.0', HELP_CONTENT)
        self.text_widget.config(state='disabled') # Make text read-only

        self.text_widget.tag_configure("highlight", background="yellow", foreground="black")

        self.bind('<Control-f>', self.focus_search)
        self.bind('<Command-f>', self.focus_search) # For macOS
        self.search_entry.bind('<Return>', self.find_next)

        self.transient(parent)
        self.focus_set()

    def focus_search(self, event=None):
        """Callback to focus the search entry widget."""
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)
        return "break"

    def reset_search(self, event=None):
        """Removes highlights, clears the search box, and resets search position."""
        self.text_widget.tag_remove("highlight", '1.0', tk.END)
        self.search_var.set("")
        self.last_search_query = ""
        self.last_match_end = "1.0"

    def find_next(self, event=None):
        """Finds and highlights the next occurrence of the search query sequentially."""
        self.text_widget.config(state='normal')
        query = self.search_var.get()
        if not query:
            self.text_widget.config(state='disabled')
            return

        if query != self.last_search_query:
            self.last_search_query = query
            self.last_match_end = "1.0"

        self.text_widget.tag_remove("highlight", "1.0", tk.END)
        pos = self.text_widget.search(query, self.last_match_end, stopindex=tk.END, nocase=True)

        if not pos:
            if messagebox.askyesno("Find", "End of document reached.\nContinue search from beginning?", parent=self):
                self.last_match_end = "1.0"
                pos = self.text_widget.search(query, self.last_match_end, stopindex=tk.END, nocase=True)
            else:
                self.last_search_query = ""
                self.last_match_end = "1.0"
                self.text_widget.config(state='disabled')
                return

        if pos:
            end_pos = f"{pos}+{len(query)}c"
            self.text_widget.tag_add("highlight", pos, end_pos)
            self.text_widget.see(pos)
            self.last_match_end = end_pos
            self.search_entry.focus_set()
        else:
            messagebox.showinfo("Find", f"Text '{query}' not found.", parent=self)
            self.last_search_query = ""
            self.last_match_end = "1.0"

        self.text_widget.config(state='disabled')


class ProgressWindow(tk.Toplevel):
    """
    A simple loading screen with an indeterminate progress bar. It appears
    centered over its parent and prevents interaction with other windows.
    """
    def __init__(self, parent: tk.Misc, title="Processing...", message="Please wait..."):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x100")
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None) # Prevent user from closing

        ttk.Label(self, text=message, padding=(20, 10)).pack()
        self.progress = ttk.Progressbar(self, mode='indeterminate', length=260)
        self.progress.pack(pady=10)
        
        # Center the window over its parent
        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        self_width = self.winfo_width()
        self_height = self.winfo_height()
        x_pos = parent_x + (parent_width // 2) - (self_width // 2)
        y_pos = parent_y + (parent_height // 2) - (self_height // 2)
        self.geometry(f"+{x_pos}+{y_pos}")

    def start(self):
        self.progress.start(10)

    def stop(self):
        self.progress.stop()
        self.destroy()


class ToolTip:
    """
    Creates a tooltip for a given widget that appears after a short delay.
    """
    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip) # 500ms delay

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def showtip(self):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                       background="#ffffe0", relief='solid', borderwidth=1,
                       font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None