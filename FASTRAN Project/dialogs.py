"""
dialogs.py
----------
Top-level utility windows for the FASTRAN GUI:
  - HelpWindow      — searchable help text viewer
  - ProgressWindow  — modal indeterminate-progress dialog

HELP_CONTENT lives here so the help text is bundled with the viewer.
"""

import tkinter as tk
from tkinter import ttk, messagebox


HELP_CONTENT = """
================================
 FASTRAN GUI — Quick Help Guide
================================

This guide provides a simplified explanation of the input fields and workflow
for each tab in the GUI.  For the complete technical reference, consult:
  "Short-User Guide-FASTRAN Ver.5.78f.pdf"

New users should work left-to-right through the five tabs in order:
  1. Geometry → 2. Material → 3. Loading → 4. Crack Growth → 5. Sensitivity

Then click "RUN ANALYSIS" at the bottom of the window.

-----------------------------------------------------------------------------
  Project Management
-----------------------------------------------------------------------------

The FASTRAN GUI organises each analysis as a self-contained *project folder*
that holds all input files, output files, and settings in one place.

  File > New Project
  - Creates a fresh project folder (input/, output/, config/ sub-folders).
  - You must create or open a project before the RUN button is enabled.

  File > Open Project
  - Reopens an existing project folder and restores the last saved GUI state.

  File > Save Project State
  - Writes the current values of all GUI fields to config/settings.json so
    they are restored exactly the next time you open this project.

  File > Import Legacy .txt / .in
  - Reads an old-style FASTRAN text input file and populates the GUI fields
    so you can view and edit it using the modern interface.

  Tools > Export Results to CSV
  - Converts the most recent .fou output file to a comma-separated spreadsheet.

  Tools > Compare Runs / Post-Processor
  - Opens a multi-run overlay window to plot results from several .fou files
    on the same axes.

-----------------------------------------------------------------------------
  Material Library
-----------------------------------------------------------------------------

The Material Library stores frequently used sets of material properties as a
JSON file (materials_library.json) in the project folder.

  On the Material tab:
    "Load Material..."
    - Choose a saved material by name; all property fields are filled in.

    "Save Current to Library..."
    - Prompts for a name and writes every material field (including crack-growth
      tables, NALP, NEP, ALP, BETAT, BETAW) to the library for future reuse.

  Tip: After running the dkeff Material Data Generator and clicking
  "Apply to Main Window", save the result to the library so you never have
  to re-run dkeff for the same dataset.

-----------------------------------------------------------------------------
  Tab 1 — Geometry
-----------------------------------------------------------------------------

Select the specimen geometry that most closely matches your physical coupon or
structural detail.  The schematic updates in real time as you type.

[ Specimen Type (NTYP) ]

  The drop-down lists all 25 supported FASTRAN geometry types.  Common choices:

    0  — Surface crack in a plate (tension or bending)
    1  — Center-crack tension M(T) specimen
    2  — Compact C(T) or ESE(T) specimen
    3  — Single-edge crack tension SE(T)
    4  — Single-edge crack bend SE(B)
   -1  — One corner crack at a circular hole
   -2  — Two corner cracks at a circular hole (symmetric)
   -3  — One through crack at a circular hole
   -4  — Two through cracks at a circular hole (symmetric)
   -12 — Lap-splice joint with through cracks (riveted structure)
   99  — User-defined geometry (Fc vs c/w table)

  Changing NTYP may reveal additional "Special Inputs" fields (e.g., Hole
  Radius, Rivet Pitch) that are required for that geometry.

[ Specimen Dimensions ]

  W  — Width (or half-width for M(T) specimens). Same units as CI, CF.
  B  — Full plate thickness (maps to T in the FASTRAN input file).
  CI — Initial crack length c_i. Must be less than CF.
  AI — Initial crack depth a_i (for surface / corner cracks only).
  CN — Starter notch length c_n. Set CN = CI if there is no pre-cracking stage.
  AN — Starter notch depth a_n (surface / corner crack notches).
  HN — Starter notch half-height h_n.
  RAD  — Radius of a circular hole or semi-circular edge notch.
  RADF — Fastener radius. 0 = open hole; set equal to RAD for a tight fastener.
  CF — Final crack length at which the analysis stops.

  *Note:* All dimensions must be in consistent units (all SI or all English).
  Use the Unit Conversion (LUNIT) field on the Loading tab to convert.

[ Schematic Views ]

  The geometry schematic shows two stacked views:
    Plan View  — Looking down on the specimen from above (crack length direction).
    Section A–A — Through-thickness cross-section (crack depth direction).

  Use the checkboxes above the schematic to show / hide each view.
  The "Save Image" button exports the current schematic as a PNG or PDF.

-----------------------------------------------------------------------------
  Tab 2 — Material
-----------------------------------------------------------------------------

Enter the mechanical properties of the material being analysed.

[ Properties ]

  Material Name (MAT)
  - Free-text label (up to 60 characters) that appears in the FASTRAN output
    header for identification.

  Yield Stress (SYIELD)
  - 0.2% offset yield strength in the selected stress units.

  Ultimate Strength (SULT)
  - Ultimate tensile strength.  Must be greater than SYIELD; the GUI will
    prevent the run if SYIELD ≥ SULT.

  Elastic Modulus (E)
  - Young's modulus (stiffness).

  Poisson's Ratio (ETA)
  - Use 0 for plane-stress analyses (thin sheet/plate).
  - Use the actual Poisson's ratio (e.g., 0.33 for aluminium) for plane-strain.

  *Flow Stress warning:* FASTRAN computes Sflow = (SYIELD + SULT) / 2.
  If the maximum applied stress in your load history exceeds Sflow, the
  net-section yielding failure mode will trigger.

[ Constraint & Plasticity Options ]

  Constraint Factor (ALP)
  - Controls the triaxiality of stress at the crack tip.
  - 1.0 = plane stress (thin sheet)
  - 1.73 = Irwin plane-strain estimate
  - 3.0 = full plane strain (thick section)
  - For mixed behaviour, use the default 1.8 and let NALP=1 adjust it.

  Compressive Tip Constraint (BETAT)
  - Constrains the compressive yield zone ahead of the crack tip.
  - Typically 1.0.  Reduce slightly (e.g., 0.5–0.9) only for very thin sheets.

  Compressive Wake Constraint (BETAW)
  - Constrains compressive yielding in the crack wake (closure contact region).
  - Typically 1.0.

  Constraint Option (NALP)
  - 0: Constant — ALP is fixed at the user-input value throughout the analysis.
  - 1: Variable — ALP transitions automatically between ALP1 and ALP2 based on
    crack-growth rate (da/dN).  RATE1, ALP1, RATE2, ALP2 must be set on the
    Crack Growth tab.  Use this when the specimen transitions from flat to slant
    fracture during the test.

  Plasticity Option (NEP)
  - 0: Elastic — no plasticity correction to the stress-intensity factor.
  - 1: Cyclic plastic zone correction (RECOMMENDED) — adds a fraction of the
    cyclic plastic zone to the crack length.  This is Newman's standard method.
  - 2: Monotonic plastic zone correction — uses the larger monotonic zone.
    Use with caution; it is less physically motivated for fatigue loading.

[ Material Library ]

  Use "Load Material..." and "Save Current to Library..." to store and recall
  material property sets (including crack-growth data).

-----------------------------------------------------------------------------
  Tab 3 — Loading
-----------------------------------------------------------------------------

Choose how the fatigue load is applied to the specimen.

[ Loading Type (NFOPT) ]

  0  — Constant Amplitude: simple Smax / R sine-wave cycling.
  1  — Block/Flight Loading: user-defined variable-amplitude block sequence
       (use "Edit Block Loading..." to build the sequence).
  2  — TWIST transport aircraft spectrum (requires spectrum file).
  3  — Mini-TWIST shortened transport spectrum (requires spectrum file).
  4  — FALSTAFF fighter aircraft spectrum (requires spectrum file).
  5  — Short FALSTAFF (requires spectrum file).
  6  — Gaussian random spectrum (requires spectrum file).
  7  — Felix/28 helicopter spectrum (requires spectrum file).
  8  — External spectrum file — general purpose (requires spectrum file).
  9  — External spectrum file — NASALOAD format (requires spectrum file).
  10 — External spectrum file — alternate format (requires spectrum file).

  *Spectrum files (NFOPT ≥ 2):*  You must provide a correctly formatted
  spectrum file.  Browse for an existing file or use "Edit Spectrum..." to
  create one using the built-in Spectrum Creator.  Using a placeholder
  filename will cause the FASTRAN run to fail.

[ Stress Parameters ]

  Smax
  - Maximum applied stress for NFOPT=0 (constant amplitude) and for the
    pre-cracking stage (Section 15).

  R  — Stress ratio R = Smin / Smax.  Smin is computed as Smax × R.

  Frequency (FW)
  - Loading frequency in Hz.  Stored for reference; not used in crack-growth
    calculations unless a rate-dependent growth law is active.

  Invert / Clip (label changes with NFOPT)
  - NFOPT=0/1: 0=normal, 1=invert the sign of all stresses.
  - NFOPT=2/3 (TWIST): clip level — 0=none, 2–5=Levels II–V.
  - Other NFOPT: see the user guide for the spectrum-specific interpretation.
    The label above this field updates automatically when NFOPT is changed.

  SPEAK — Peak scaling stress for spectrum loading (NFOPT 4–10).  All
          spectrum stress values are multiplied by SPEAK.
  SMEAN — Mean stress offset for TWIST / Mini-TWIST / Gaussian (NFOPT=2,3,6).

[ Spectrum File ]

  Enter the filename of the spectrum file in the project's input/ folder,
  or use "Browse..." to locate it.  "Edit Spectrum..." opens the Spectrum
  Creator to build a new spectrum from scratch.

[ Block Loading (NFOPT=1) ]

  "Edit Block Loading..." opens the Block Editor where you define the number
  of load levels, stress levels, and repeat counts for each block or flight.

[ Specimen & Loading Options (Section 10) ]

  LTYP  — Loading sub-type for certain geometries.
           0: Remote tension (input S).
           1: Remote bending (input outer-fibre stress Sb).
           2: Combined tension + bending (input S and γ = Sb/S).

  LFAST — Crack-closure model.
           0: Full Newman crack-closure model (standard — most accurate).
           1: SOBAR equivalent (faster for long runs).
           2–4: Special closure options for advanced users.

  KCONST — 0: Apply remote stress as loading (normal).
            1: Apply K (stress-intensity factor) directly — NTYP=1 or 2 only.

  NS    — Number of notch elements (≥1 for notch only; ≥2 for notch at hole).

  NTCMAX — 0: Normal notch constraint.
            1: First cycle is plane-stress (ALP=1) for negative-NTYP geometries.

[ Proof Test / Constant So (Section 16) ]

  NRC, DVALUE, NCYCLE1, NCYCLE2
  - Used to simulate a proof-test overload before or after the main fatigue
    cycling.  For most standard crack-growth analyses, leave these at 0.

-----------------------------------------------------------------------------
  Tab 4 — Crack Growth
-----------------------------------------------------------------------------

Define the material crack-growth behaviour.  Either use the Paris law
equation (C1–C7) or load tabular ΔKeff / da/dN data.

[ Model Option (IRATE) ]

  1 — Single law: one da/dN curve used for both crack length (c) and depth (a).
  2 — Two independent laws: separate curves for the c- and a-directions.
  4 — Small/large crack transition: four curves (small and large, c and a).

  NGC / CRKNGC (IRATE=4 only)
  - NGC=1 enables the small-to-large crack transition.
  - CRKNGC is the transition crack size; cracks smaller than this use the
    small-crack law.  Typical value: 0.00025 m (0.01 in).

[ Paris Law Constants (C1–C7) ]

  The FASTRAN crack-growth equation is:
    da/dN = C1 · ΔKeff^C2 · [threshold term] · [fracture term]

  Steady-state growth:
    C1 — Scaling coefficient (vertical position on a log-log da/dN plot).
         A higher C1 means faster growth at any given ΔK.
    C2 — Slope exponent on the log-log plot.

  Threshold behaviour (set C3=C4=C7=0 to disable):
    C3 — Baseline threshold constant.
         ΔKo = C3·(1−R)^C4  (if C4 > 0)
         ΔKo = C3·(1+C4·R) (if C4 < 0)
    C4 — R-ratio modifier for the threshold.
    C7 — Sharpness of the threshold knee.  Higher values create an abrupt
         cut-off (crack won't grow below ΔKo).

  Fracture behaviour (set C5=0 to use KF/m instead):
    C5 — Cyclic fracture toughness.  Set to 9999 to use KF and m.
    C6 — Power on the fracture term (controls how abruptly growth accelerates
         as Kmax approaches C5).
    KF — Elastic-plastic fracture toughness.  Used with m to compute KIe.
    m  — 0=brittle (LEFM), 1=fully ductile.

  Equation (NEQN):
    0 — FASTRAN equation (standard).
    1 — NASGRO equation (alternate formulation).

[ Tabular Data (NTAB > 0) ]

  When NTAB > 0, the table of (ΔKeff, da/dN) data *overrides* the C1–C7
  constants.  The da/dN preview plot switches from the Paris curve to the
  tabular points automatically.

  NTAB  — Number of data points in the table.  Set via "Edit Table..." button.
  NDKTH — 0: direct table lookup.
           1: FASTRAN tabular form (applies threshold / fracture corrections).
           2: NASGRO tabular form.

  *Tip:* Use Tools > Material Data Generator (dkeff) to convert raw lab data
  (ΔK vs da/dN from an ASTM E647 test) into a properly corrected ΔKeff table,
  then click "Apply to Main Window" to import it here automatically.

[ Output Options (Section 9) ]

  NPRT — Output interval.  Negative value: print every |NPRT| crack increments
         (recommended for smooth post-processing plots).  Positive: print every
         NPRT analysis steps.  0: use DCPR.
  DCPR — Crack-growth increment (e.g., 0.0001 m) at which results are printed
         when NPRT = 0.
  NIPT — 0: internal closure log off (normal).  >0: print detailed internal data
         every NIPT increments (debugging only).
  LSTEP — Load steps per NIPT printout (usually 1).
  NDKE — 0: print elastic ΔK.  1: print effective ΔK (ΔKeff).

[ Variable Constraint Transition (NALP=1 only) ]

  When NALP=1 is selected on the Material tab, you must provide the rates and
  corresponding constraint factors that define the flat-to-slant transition:

  RATE1 / ALP1 / BETAT1 / BETAW1
  - Transition onset: at da/dN = RATE1, ALP shifts from the initial value to ALP1.

  RATE2 / ALP2 / BETAT2 / BETAW2
  - Transition complete: at da/dN = RATE2, ALP reaches ALP2.
  - RATE2 must be greater than RATE1.

  Typical aluminium values:
    RATE1=1e-7 m/cycle, ALP1=2.0, RATE2=2.5e-6 m/cycle, ALP2=1.0

-----------------------------------------------------------------------------
  Tab 5 — Sensitivity
-----------------------------------------------------------------------------

The Sensitivity tab runs FASTRAN repeatedly while sweeping one input variable
over a range.  The result is a parametric "design curve" showing how the
predicted fatigue life (cycles to failure) changes with that variable.

  Sweep Parameter — Choose which variable to vary (e.g., CI, CF, Smax, W).
  Min / Max / Steps — Define the sweep range and the number of evenly spaced
    points.

  Click "Run Sensitivity Analysis" to launch the batch run.  Progress is shown
  in the status bar.  Results appear as a line chart on the right side.

  "Export Design Curve CSV" saves the (parameter, cycles) pairs to a file.

  Tips:
  - A sweep over CI (initial crack size) shows how sensitive life is to
    initial flaw assumptions — important for inspection planning.
  - A sweep over Smax shows the load-life relationship at a glance.
  - Run a full analysis on Tab 4 first to confirm the baseline case runs
    cleanly before launching a sensitivity sweep.

-----------------------------------------------------------------------------
  Tools — Material Data Generator (dkeff)
-----------------------------------------------------------------------------

The dkeff tool converts raw fatigue crack-growth test data into the effective
stress-intensity-factor range (ΔKeff) vs. crack-growth-rate (da/dN) table that
FASTRAN uses in Section 7b.

Open it from the main window via  Tools > Material Data Generator (DkEff)...

[ Executable Versions ]

  dkeff13 (Legacy)
  - Older protocol: stdin sequence is IKEFF (=1 for file input), test type,
    input filename, output filename.

  dkeff21f (New)
  - Updated protocol: stdin sequence is test type, input filename, output filename
    (the IKEFF prompt is absent).

  Configure the path to each EXE via  File > Configure Executable Paths...

[ Specimen Presets ]

  The "Specimen Preset" drop-down fills W, T, and ALP automatically for six
  standard ASTM E647 specimen geometries:
    M(T) 3" / 4" — middle-crack tension panels
    C(T) 0.5T / 1T / 2T — compact tension specimens
    ESE(T) — extended single-edge crack tension

  Override individual fields after applying a preset if your specimen differs.

[ Input Parameters ]

  Specimen Type (NTYP)
  - 1: Middle-crack tension M(T)
  - 2: Compact tension C(T)
  - 3: ESE(T)

  Test Type
  - Constant R test: data collected at fixed stress ratio R.  Supply R and Smax.
  - Kmax test:       data collected at constant Kmax.  Supply Kmax.

  Analysis Mode (NSOP)
  - NSOP=0: dkeff calculates crack length internally from ΔK and da/dN only.
    Use this for database-sourced data where measured crack length is not available.
  - NSOP=1: you supply measured crack length c alongside ΔK and da/dN.
    Most common mode for raw ASTM E647 test records.
  - NSOP=2: you supply the crack-opening-stress ratio So/Smax instead of c.
    Used for advanced closure analysis.

  Specimen Dimensions
  - W:   Width (half-width for M(T)).
  - T:   Thickness.
  - ALP: Constraint factor (1.0=plane stress, 3.0=plane strain).

  Material Properties
  - SYIELD, SULT, E must be positive and in the same units as the test data.
  - These are required before a dkeff run can proceed.

  Unit Conversion (LUNIT)
  - 0: Keep same units — no conversion applied.
  - 1: English → SI  (ksi·√in → MPa·√m; multiplies stresses by 6.895).
  - 2: SI → English  (MPa·√m → ksi·√in; divides stresses by 6.895).

[ Lab Data Table ]

  Each row represents one test data point.  Columns:
    ΔK      — stress-intensity-factor range
    da/dN   — crack-growth rate
    c (or So/Smax) — depending on NSOP

  Data must be strictly ascending in both ΔK and da/dN.
  Use the "Validate Data" button to check for ordering errors before running.

[ Workflow ]

  ① Enter material properties (SYIELD, SULT, E) and analysis parameters.
  ② Enter lab data in the table, or load an existing .dkin file via
     File > Load dkeff Input File.
  ③ Click "Validate Data" to check for ordering errors.
  ④ Click "② Generate dKeff Data" to run the dkeff executable.
  ⑤ Review the raw output in the "dkeff Output" panel that appears below.
  ⑥ Click "③ Apply to Main Window" to copy the resulting ΔKeff table and
     material properties back into the FASTRAN GUI.  The crack-growth preview
     plot on Tab 4 will update automatically.

[ Importing .lkpx Files (LK Pro-X) ]

  File > Import .lkpx Direct to Main Window
  - Parses a LK Pro-X material database file and lets you choose one R-ratio
    dataset.  The selected ΔK / da/dN pairs are written directly into the
    CGR_TABLE on Tab 4 — no dkeff run required.

  File > Batch Convert .lkpx File
  - Converts a multi-R-ratio .lkpx file into a single multi-dataset .dkin file
    suitable for processing one dataset at a time through dkeff.
  1. Select the .lkpx file.
  2. For each R-ratio found, enter Smax, W, and T.
  3. Choose an output .dkin filename.
  4. Load the result via File > Load dkeff Input File, then select a dataset.
"""


class HelpWindow(tk.Toplevel):
    """A separate window for displaying help content with incremental search."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("FASTRAN GUI - Help")
        self.geometry("800x650")

        self.last_search_query = ""
        self.last_match_end = "1.0"

        search_frame = ttk.Frame(self, padding="5")
        search_frame.pack(fill='x', side='bottom')

        ttk.Label(search_frame, text="Search:").pack(side='left', padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side='left', fill='x', expand=True)
        ttk.Button(search_frame, text="Find Next", command=self.find_next).pack(side='left', padx=5)
        ttk.Button(search_frame, text="Reset", command=self.reset_search).pack(side='left', padx=5)

        text_container = ttk.Frame(self)
        text_container.pack(fill='both', expand=True)
        self.text_widget = tk.Text(text_container, wrap='word', undo=False, font=("tahoma", 9))
        scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)

        self.text_widget.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)

        self.text_widget.insert('1.0', HELP_CONTENT)
        self.text_widget.config(state='disabled')

        self.text_widget.tag_configure("highlight", background="yellow", foreground="black")

        self.bind('<Control-f>', self.focus_search)
        self.bind('<Command-f>', self.focus_search)
        self.search_entry.bind('<Return>', self.find_next)

        self.focus_set()

    def focus_search(self, event=None):
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)
        return "break"

    def reset_search(self, event=None):
        self.text_widget.tag_remove("highlight", '1.0', tk.END)
        self.search_var.set("")
        self.last_search_query = ""
        self.last_match_end = "1.0"

    def find_next(self, event=None):
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
    """Modal indeterminate-progress dialog used during long-running operations."""

    def __init__(self, parent, title="Processing...", message="Please wait..."):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x100")
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        ttk.Label(self, text=message, padding=(20, 10)).pack()
        self.progress = ttk.Progressbar(self, mode='indeterminate', length=260)
        self.progress.pack(pady=10)

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def start(self):
        self.progress.start(10)

    def stop(self):
        self.progress.stop()
        self.destroy()
