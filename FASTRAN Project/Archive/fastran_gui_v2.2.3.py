import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import xml.etree.ElementTree as ET
import threading
import subprocess
import queue
import csv
import copy
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- SIMPLIFIED Help File Content ---
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
  - For all other loading options, you can use a dummy filename (e.g., dummy.txt).

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

[ Constraint Factors ]

  Tensile Constraint (ALP)
  - A factor that defines the state of stress at the crack tip.
  - Common values: 1.0 for plane stress, 3.0 for plane strain.

  Compressive Constraint (BETAT / BETAW)
  - Factors for compressive yielding. BETAT is for the material ahead of the crack tip, and BETAW is for the material in the crack wake.

[ Material Options ]

  Constraint Opt (NALP)
  - Defines how the constraint factor (ALP) is treated.
  - 0: Constant -> Uses the user-input ALP value throughout the analysis.
  - 1: Variable -> The program calculates a variable ALP based on crack growth rates.

  Plasticity Opt (NEP)
  - Defines the plasticity correction method for the stress intensity factor.
  - 0: Elastic -> No plasticity correction.
  - 1: Plasticity-Corrected -> Modifies the crack length by adding a portion of the *cyclic* plastic zone. (RECOMMENDED)
  - 2: Closure Corrected -> Modifies the crack length by adding a portion of the *monotonic* plastic zone. (Use with caution)

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
  - Enables the transition from small-crack to large-crack behavior (only used when IRATE=4).
  - NGC=1 enables the transition.
  - CRKNGC is the crack size at which the transition occurs.

[ Growth Rate Equation & Properties ]

  C1-C7, KF, m
  - These are the coefficients, powers, and toughness parameters for the selected crack growth equation (FASTRAN or NASGRO).
  - C5 is the cyclic fracture toughness.

  Equation (NEQN)
  - Selects the crack growth law to be used.
  - 0: FASTRAN Equation
  - 1: NASGRO Equation

[ Crack Growth Table (NTAB > 0) ]

  Num. Points (NTAB)
  - If greater than 1, the program will use a table of (dK_eff, da/dN) data instead of the equation. NTAB is the number of points in the table.

  NDKTH
  - Defines how the table data is interpreted and applied.
  - 0: Direct table lookup.
  - 1: FASTRAN tabular form, which modifies the table data with threshold and fracture properties.
  - 2: NASGRO tabular form, similar to option 1 but uses a different formulation.

[ Transition Parameters (NALP = 1 only) ]

  RATE1, ALP1, RATE2, ALP2, etc.
  - These parameters define the crack growth rates (RATE1, RATE2) at which the transition from flat-to-slant crack growth occurs, and the corresponding constraint factors (ALP1, ALP2).

-----------------------------------------------------------------------------
  Tab 3: Geometry & Loading
-----------------------------------------------------------------------------

[ Specimen & Crack Geometry ]

  Specimen Type (NTYP)
  - Defines the geometry of the cracked component (e.g., Center Crack, Surface Crack, Crack at Hole).

  W, T, CI, AI, CF, RAD
  - W: Width (or half-width)
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
  - The constant-amplitude max and min stress levels used to grow the crack from the initial notch (CN) to the initial crack size (CI).
  - These inputs are required but are only used if CN is different from CI.

  Primary Loading (MAXSEQ, SPEAK, SMEAN, etc.)
  - These fields control the application of the primary fatigue loading defined by NFOPT.
  - SPEAK: The highest stress in a spectrum, used to scale the spectrum data.
  - SMEAN: The mean stress for certain spectra like TWIST.
  - MAXSEQ: Total number of blocks or flights in a sequence.

[ Output & Advanced Options ]

  NIPT / NPRT / LSTEP / DCPR
  - These options control how frequently and in what detail the analysis results are printed to the output files.

  LFAST
  - Selects the crack-closure model. Option 0 is the standard, most common choice.

  Threshold Test (KTH)
  - Enables a load-reduction threshold test instead of a standard fatigue analysis.
  - This is a special-purpose test, and should typically be left at 0 for normal analyses.
"""

# --- Help Window Class ---
class HelpWindow(tk.Toplevel):
    """
    A separate window for displaying help content.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title("FASTRAN GUI - Help")
        self.geometry("800x650")

        # --- State variables for searching ---
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
        
        # Insert the embedded help content
        self.text_widget.insert('1.0', HELP_CONTENT)
        self.text_widget.config(state='disabled') # Make text read-only

        # Configure a tag for highlighting search results
        self.text_widget.tag_configure("highlight", background="yellow", foreground="black")

        # Bind shortcuts
        self.bind('<Control-f>', self.focus_search)
        self.bind('<Command-f>', self.focus_search) # For macOS
        self.search_entry.bind('<Return>', self.find_next)

        self.focus_set() # Bring this window to the front

    def focus_search(self, event=None):
        """Callback to focus the search entry widget."""
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)
        return "break" # Prevents the default text widget search from running

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

        # If the search term is new, reset the position to the start
        if query != self.last_search_query:
            self.last_search_query = query
            self.last_match_end = "1.0"

        # Remove the previous highlight
        self.text_widget.tag_remove("highlight", "1.0", tk.END)

        # Find the next occurrence
        pos = self.text_widget.search(query, self.last_match_end, stopindex=tk.END, nocase=True)

        # If no match is found from the current position to the end
        if not pos:
            # Ask the user if they want to wrap the search
            if messagebox.askyesno("Find", "End of document reached.\nContinue search from beginning?", parent=self):
                self.last_match_end = "1.0" # Reset to top
                pos = self.text_widget.search(query, self.last_match_end, stopindex=tk.END, nocase=True)
            else:
                # User chose not to wrap, so reset for the next new search
                self.last_search_query = ""
                self.last_match_end = "1.0"
                self.text_widget.config(state='disabled')
                return

        # If a match was found (either immediately or after wrapping)
        if pos:
            end_pos = f"{pos}+{len(query)}c"
            self.text_widget.tag_add("highlight", pos, end_pos)
            self.text_widget.see(pos) # Scroll to the highlighted text
            self.last_match_end = end_pos # Set the starting point for the *next* search
            self.search_entry.focus_set()
        else:
            # This case is reached if the text isn't in the document at all
            messagebox.showinfo("Find", f"Text '{query}' not found.", parent=self)
            self.last_search_query = "" # Reset
            self.last_match_end = "1.0"

        self.text_widget.config(state='disabled')

# --- FASTRAN Parsing/Generation Functions ---
def parse_material_xml(filepath):
    try:
        tree = ET.parse(filepath); root = tree.getroot()
        name = root.findtext('.//Material/Name', 'Unknown Material')
        table_rows = []
        tlookup_table = root.find('.//PropertyData[@property="tlookup"]/DataTable/Data')
        if tlookup_table is not None:
            for row in tlookup_table.findall('row'):
                rate_el = row.find("./FieldData[@pos='1']"); dk_el = row.find("./FieldData[@pos='2']")
                if dk_el is not None and rate_el is not None: table_rows.append([dk_el.text, rate_el.text])
        if not table_rows: messagebox.showwarning("Warning", "Could not find a da/dN table in the material file.")
        properties = {}
        properties['SYIELD'] = root.findtext('.//PropertyData[@property="yld"]/Data', '0.0')
        properties['SULT']   = root.findtext('.//PropertyData[@property="ult_strength"]/Data', '0.0')
        properties['E']      = root.findtext('.//PropertyData[@property="e"]/Data', '0.0')
        properties['ETA']    = root.findtext('.//PropertyData[@property="poisson"]/Data', '0.0')
        return name, table_rows, properties
    except Exception as e:
        messagebox.showerror("Material File Error", f"Failed to load material file: {e}")
        return None, None, None

def parse_fastran_file(filepath):
    try:
        with open(filepath, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        if not lines:
            messagebox.showerror("Error", "The selected file is empty.")
            return None, None
            
        data = {}; line_idx = 0
        def get_vals(line_index):
            return lines[line_index].split()

        line_idx += 1 
        data['SPECTRA'] = lines[line_idx]; line_idx += 1
        data['MAT'] = lines[line_idx].strip(); line_idx += 1
        keys = ['SYIELD', 'SULT', 'E', 'ETA', 'ALP', 'BETAT', 'BETAW', 'NALP', 'NEP']
        vals = get_vals(line_idx); data.update(zip(keys, vals)); line_idx += 1
        keys = ['IRATE', 'NGC', 'CRKNGC']; vals = get_vals(line_idx); data.update(zip(keys, vals)); line_idx += 1
        keys = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'KF', 'M', 'NEQN']; vals = get_vals(line_idx); data.update(zip(keys, vals)); line_idx += 1
        
        vals = get_vals(line_idx); ntab = int(vals[0])
        data['NTAB'] = str(ntab)
        data['NDKTH'] = vals[1] if len(vals) > 1 else '0'
        line_idx += 1
        
        table_data = []
        if ntab > 0:
            for _ in range(ntab):
                vals = get_vals(line_idx)
                table_data.append(vals[0:2])
                line_idx += 1
        
        if data.get('NALP') == '1' and "E" in lines[line_idx].upper():
            keys = ['RATE1', 'ALP1', 'BETAT1', 'BETAW1', 'RATE2', 'ALP2', 'BETAT2', 'BETAW2']
            vals = get_vals(line_idx); data.update(zip(keys, vals)); line_idx += 1
        
        keys = ['NIPT', 'NPRT', 'LSTEP', 'NDKE', 'DCPR']; vals = get_vals(line_idx); data.update(zip(keys, vals)); line_idx += 1
        keys = ['NTYP', 'LTYP', 'LFAST', 'NS', 'NFOPT', 'INVERT', 'KCONST', 'NTCMAX']; vals = get_vals(line_idx); data.update(zip(keys, vals)); line_idx += 1
        keys = ['W', 'T', 'CI', 'AI', 'CN', 'AN', 'HN', 'RAD', 'RADF']; vals = get_vals(line_idx); data.update(zip(keys, vals)); line_idx += 1
        data['CF'] = lines[line_idx].split()[0]; line_idx += 1
        ntyp_code = data.get('NTYP')
        ltyp_code = data.get('LTYP')

        # Check for optional Section 14 parameters before reading Section 15
        if ntyp_code == '5':
            data['RADIUS'] = get_vals(line_idx)[0]; line_idx += 1
        elif ntyp_code in ['-12', '-13']:
            keys = ['RIVETS', 'RLF1', 'RLF2', 'NODKL', 'GAMMA', 'DELTA']
            vals = get_vals(line_idx); data.update(zip(keys, vals)); line_idx += 1
        elif (ntyp_code in ['0', '7'] and ltyp_code == '2') or ntyp_code == '-10':
            data['GAMMA'] = get_vals(line_idx)[0]; line_idx += 1

        keys = ['SMAX', 'SMIN']; vals = get_vals(line_idx); data.update(zip(keys, vals)); line_idx += 1
        keys = ['NRC', 'DVALUE', 'NCYCLE1', 'NCYCLE2']; vals = get_vals(line_idx); data.update(zip(keys, vals)); line_idx += 1
        
        nfopt_val = int(data.get('NFOPT', '0'))
        if nfopt_val in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] and line_idx < len(lines) and "HALT" not in lines[line_idx].upper():
            vals = get_vals(line_idx)
            keys = ['MAXSEQ', 'MAXBLK', 'LPRINT', 'MAXLPR']
            data.update(zip(keys, vals))
            if nfopt_val == 8:
                if len(vals) > 4: data['NREP'] = vals[4]
                if len(vals) > 5: data['MARKER'] = vals[5]
            line_idx += 1
            
            if line_idx < len(lines) and "HALT" not in lines[line_idx].upper():
                if nfopt_val in [2,3]: data['SMEAN'] = lines[line_idx].split()[0]; line_idx+=1
                elif nfopt_val == 6: vals = get_vals(line_idx); data['SPEAK'], data['SMEAN'] = vals; line_idx+=1
                elif nfopt_val in [4,5,7,8,9,10]: data['SPEAK'] = lines[line_idx].split()[0]; line_idx+=1

        if line_idx < len(lines) and "HALT" not in lines[line_idx].upper():
            keys = ['KTH', 'SMAXTH', 'RTH', 'CONST', 'PRT']
            vals = get_vals(line_idx)
            data.update(zip(keys, vals))

        messagebox.showinfo("Success", "Successfully loaded the input file.")
        return data, table_data
    except Exception as e:
        messagebox.showerror("Parsing Error", f"Failed to load the input file.\n{e}")
        return None, None

def generate_fastran_file(values, table_data, save_path, maps):
    try:
        # Convert all descriptive combobox values to their required integer codes
        values['NALP'] = maps['nalp_map'][values['NALP_DESC']]
        values['NEP'] = maps['nep_map'][values['NEP_DESC']]
        values['NEQN'] = maps['neqn_map'][values['NEQN_DESC']]
        values['NTYP'] = maps['ntyp_map'][values['NTYP_DESC']]
        values['LTYP'] = maps['ltyp_map'][values['LTYP_DESC']]
        values['NFOPT'] = maps['nfopt_map'][values['NFOPT_DESC']]
        values['IRATE'] = maps['irate_map'][values['IRATE_DESC']]
        values['NGC'] = maps['ngc_map'][values['NGC_DESC']]
        values['NDKTH'] = maps['ndkth_map'][values['NDKTH_DESC']]
        values['NDKE'] = maps['ndke_map'][values['NDKE_DESC']]
        values['LFAST'] = maps['lfast_map'][values['LFAST_DESC']]
        values['KCONST'] = maps['kconst_map'][values['KCONST_DESC']]
        values['NTCMAX'] = maps['ntcmax_map'][values['NTCMAX_DESC']]
        values['KTH'] = maps['kth_map'][values['KTH_DESC']]
        
        problem_title = os.path.basename(save_path)
        
        output_lines = [
            f"{problem_title}",
            f"{values['SPECTRA']}",
            f" {values['MAT']}",
            f"  {float(values['SYIELD']):.1f}  {float(values['SULT']):.1f}  {float(values['E']):.1f}   {float(values['ETA'])}  {float(values['ALP'])}  {float(values['BETAT'])}  {float(values['BETAW'])}  {int(values['NALP'])}  {int(values['NEP'])}",
            f"    {int(values['IRATE'])}    {int(values['NGC'])}    {float(values['CRKNGC']):.1f}",
            f" {float(values['C1']):.2E} {float(values['C2']):.2E}  {float(values['C3'])}  {float(values['C4'])}  {float(values['C5']):.4E}  {float(values['C6'])}  {float(values['C7'])}  {float(values['KF'])}  {float(values['M'])}  {int(values['NEQN'])}",
        ]

        ntab = int(values['NTAB'])
        output_lines.append(f"    {ntab}    {int(values['NDKTH'])}")
        if ntab > 0:
            for i in range(ntab):
                dk_val, rate_val = float(table_data[i][0]), float(table_data[i][1])
                output_lines.append(f"  {dk_val:<5.2f}   {rate_val:g}")

        if values.get('NALP') == '1':
            output_lines.append(f"{float(values['RATE1']):.1E}  {float(values['ALP1']):.2f}  {float(values['BETAT1'])}  {float(values['BETAW1'])}  {float(values['RATE2']):.1E}  {float(values['ALP2']):.2f}  {float(values['BETAT2'])}  {float(values['BETAW2'])}")

        output_lines.extend([
            f"   {int(values['NIPT'])}   {int(values['NPRT'])}    {int(values['LSTEP'])}    {int(values['NDKE'])}   {float(values['DCPR']):.5f}",
            f"   {int(values['NTYP'])}    {int(values['LTYP'])}    {int(values['LFAST'])}    {int(values['NS'])}     {int(values['NFOPT'])}    {int(values['INVERT'])}    {int(values['KCONST'])}    {int(values['NTCMAX'])}",
            f" {float(values['W'])}  {float(values['T'])}  {float(values['CI'])}  {float(values['AI'])}  {float(values['CN'])}  {float(values['AN'])}  {float(values['HN'])}   {float(values['RAD'])}   {float(values['RADF'])}",
            f" {float(values['CF'])}",
        ])

        ntyp_code = values['NTYP']
        ltyp_code = values['LTYP']
        if ntyp_code == '5':
            output_lines.append(f" {float(values['RADIUS'])}")
        elif ntyp_code in ['-12', '-13']:
            lap_joint_line = f" {float(values['RIVETS'])} {float(values['RLF1'])} {float(values['RLF2'])} {int(values['NODKL'])} {float(values['GAMMA'])} {float(values['DELTA'])}"
            output_lines.append(lap_joint_line)
        elif (ntyp_code in ['0', '7'] and ltyp_code == '2') or ntyp_code == '-10':
            output_lines.append(f" {float(values['GAMMA'])}")

        output_lines.extend([
            f"   {float(values['SMAX']):.1f}       {float(values['SMIN']):.1f}",
            f" {int(values['NRC'])}   {float(values['DVALUE'])}    {int(values['NCYCLE1'])}    {int(values['NCYCLE2'])}"
        ])

        nfopt_val = int(values.get('NFOPT', '0'))
        if 0 <= nfopt_val <= 10:
            loading_line = f"  {int(values['MAXSEQ'])}  {int(values['MAXBLK'])}  {int(values['LPRINT'])}  {int(values['MAXLPR'])}"
            if nfopt_val == 8:
                loading_line += f"  {int(values['NREP'])}  {int(values['MARKER'])}"
            output_lines.append(loading_line)

            if nfopt_val == 6: output_lines.append(f"    {float(values['SPEAK']):.1f}  {float(values['SMEAN']):.1f}")
            elif nfopt_val in [2, 3]: output_lines.append(f"    {float(values['SMEAN']):.1f}")
            elif nfopt_val in [4, 5, 7, 8, 9, 10]: output_lines.append(f"    {float(values['SPEAK']):.1f}")
        
        output_lines.append(f" {int(values['KTH'])}   {int(float(values['SMAXTH']))}   {int(float(values['RTH']))}   {int(float(values['CONST']))}   {int(float(values['PRT']))}")
        output_lines.append("HALT\nHALT")

        with open(save_path, 'w') as f:
            f.write('\n'.join(output_lines))
        return True
    except Exception as e:
        messagebox.showerror("Generation Error", f"An error occurred during file generation: {e}")
        return False

# --- ToolTip Helper Class ---
class ToolTip:
    """
    Create a tooltip for a given widget.
    """
    def __init__(self, widget, text):
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
        self.id = self.widget.after(500, self.showtip)

    def unschedule(self):
        id = getattr(self, 'id', None)
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
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
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()

# --- Spectrum Creator/Editor Window Class ---
class SpectrumCreatorWindow(tk.Toplevel):
    def __init__(self, parent, callback, load_from_file=None):
        super().__init__(parent)
        self.title("Spectrum Editor")
        self.geometry("750x650")
        self.callback = callback
        self.output_filepath = None
        
        self.levels_data = [] 
        self.level_widgets = []
        self.num_levels_var = tk.IntVar(value=0)
        self.smf_var = tk.StringVar(value="1.0")

        self.undo_stack = []
        self.redo_stack = []

        self._create_widgets()
        
        if load_from_file and os.path.exists(load_from_file):
            self._load_spectrum_file(load_from_file)
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
        # --- Top Control Frame ---
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill='x', padx=10, pady=5)
        top_frame.columnconfigure(6, weight=1)

        ttk.Label(top_frame, text="Spectrum Title:").grid(row=0, column=0, sticky='w', pady=2)
        self.title_entry = ttk.Entry(top_frame)
        self.title_entry.insert(0, "Custom Spectrum")
        self.title_entry.grid(row=0, column=1, columnspan=5, sticky='ew', padx=5)
        
        ttk.Label(top_frame, text="INVERT:").grid(row=1, column=0, sticky='w', pady=(5,2))
        self.invert_entry = ttk.Entry(top_frame, width=10)
        self.invert_entry.insert(0, "0")
        self.invert_entry.grid(row=1, column=1, sticky='w', padx=5)
        ToolTip(self.invert_entry, "0 for Smax,Smin pairs. 1 for Smin,Smax pairs.")

        ttk.Label(top_frame, text="ICLIP:").grid(row=1, column=2, sticky='w', padx=5, pady=(5,2))
        self.iclip_entry = ttk.Entry(top_frame, width=10)
        self.iclip_entry.insert(0, "3")
        self.iclip_entry.grid(row=1, column=3, sticky='w', padx=5)
        ToolTip(self.iclip_entry, "ICLIP value for spectrum header.\nAlso used to determine body format (e.g., 3 for 10I8).")

        smf_lbl = ttk.Label(top_frame, text="SMF:")
        smf_lbl.grid(row=1, column=4, sticky='w', padx=5, pady=(5,2))
        smf_entry = ttk.Entry(top_frame, textvariable=self.smf_var, width=10)
        smf_entry.grid(row=1, column=5, sticky='w')
        ToolTip(smf_lbl, "Stress Multiplication Factor.\nApplied to all stress levels during file generation.")
        ToolTip(smf_entry, "Stress Multiplication Factor.\nApplied to all stress levels during file generation.")
        
        ttk.Button(top_frame, text="Save & Close", command=self._generate_spectrum).grid(row=0, column=6, sticky='ne', padx=5)

        ttk.Button(top_frame, text="Set Save Location...", command=self._set_output_file).grid(row=2, column=0, pady=(10,0))
        self.output_label = ttk.Label(top_frame, text="Spectrum File: Not Set", relief='sunken', anchor='w')
        self.output_label.grid(row=2, column=1, columnspan=6, sticky='ew', padx=5, pady=(10,0))

        # --- Paned Window for Table and Plot ---
        paned_window = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned_window.pack(fill='both', expand=True, padx=10, pady=5)

        # --- Top Pane: Table ---
        table_container = ttk.LabelFrame(paned_window, text="Stress Levels", padding="10")
        paned_window.add(table_container, weight=1)
        
        level_ctrl_frame = ttk.Frame(table_container)
        level_ctrl_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(level_ctrl_frame, text="Number of Levels:").pack(side='left')
        ttk.Spinbox(
            level_ctrl_frame, from_=0, to=500, textvariable=self.num_levels_var,
            width=6, command=self._update_levels_from_spinbox
        ).pack(side='left', padx=5)
        
        ttk.Button(level_ctrl_frame, text="Import...", command=self._import_spectrum).pack(side='left', padx=(10, 0))
        ttk.Button(level_ctrl_frame, text="Update Plot", command=self._update_plot).pack(side='left', padx=10)

        # Undo/Redo Buttons
        self.undo_button = ttk.Button(level_ctrl_frame, text="Undo", command=self._undo, state="disabled")
        self.undo_button.pack(side='left', padx=(20, 0))
        self.redo_button = ttk.Button(level_ctrl_frame, text="Redo", command=self._redo, state="disabled")
        self.redo_button.pack(side='left', padx=5)
        
        canvas = tk.Canvas(table_container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=canvas.yview)
        self.table_frame = ttk.Frame(canvas, padding="5")
        self.table_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- Bottom Pane: Plot ---
        plot_container = ttk.LabelFrame(paned_window, text="Spectrum Plot", padding="10")
        paned_window.add(plot_container, weight=1)

        fig = Figure(dpi=100)
        fig.set_tight_layout(True)
        self.ax = fig.add_subplot(111)
        self.plot_canvas = FigureCanvasTkAgg(fig, master=plot_container)
        self.plot_canvas.get_tk_widget().pack(fill='both', expand=True)
        plot_container.bind("<Configure>", lambda event: self.plot_canvas.draw_idle())
        self._update_plot()
    
    # --- New Undo/Redo and Supporting Methods ---
    def _save_state_for_undo(self, clear_redo=True):
        """Saves a deep copy of the current data state for undo purposes."""
        self.undo_stack.append(copy.deepcopy(self.levels_data))
        if clear_redo:
            self.redo_stack.clear()
        self._update_undo_redo_buttons()

    def _undo(self, event=None):
        if not self.undo_stack or len(self.undo_stack) <= 1: return
        self._sync_data_from_widgets()
        self.redo_stack.append(copy.deepcopy(self.levels_data))
        self.levels_data = self.undo_stack.pop()
        self._redraw_levels_table()
        self._update_plot()
        self._update_undo_redo_buttons()

    def _redo(self, event=None):
        if not self.redo_stack: return
        self._sync_data_from_widgets()
        self.undo_stack.append(copy.deepcopy(self.levels_data))
        self.levels_data = self.redo_stack.pop()
        self._redraw_levels_table()
        self._update_plot()
        self._update_undo_redo_buttons()

    def _update_undo_redo_buttons(self):
        self.undo_button.config(state="normal" if len(self.undo_stack) > 1 else "disabled")
        self.redo_button.config(state="normal" if self.redo_stack else "disabled")

    def _sync_data_from_widgets(self):
        """Saves the current values from the entry widgets back to the data list."""
        for i, row_widgets in enumerate(self.level_widgets):
            if i < len(self.levels_data):
                self.levels_data[i] = [row_widgets[0].get(), row_widgets[1].get(), row_widgets[2].get()]

    def _delete_level(self, index):
        self._save_state_for_undo()
        self._sync_data_from_widgets()
        if 0 <= index < len(self.levels_data):
            self.levels_data.pop(index)
            self._redraw_levels_table()

    def _move_level_up(self, index):
        if index > 0:
            self._save_state_for_undo()
            self._sync_data_from_widgets()
            self.levels_data[index], self.levels_data[index - 1] = self.levels_data[index - 1], self.levels_data[index]
            self._redraw_levels_table()

    def _move_level_down(self, index):
        if index < len(self.levels_data) - 1:
            self._save_state_for_undo()
            self._sync_data_from_widgets()
            self.levels_data[index], self.levels_data[index + 1] = self.levels_data[index + 1], self.levels_data[index]
            self._redraw_levels_table()

    def _import_spectrum(self):
        filepath = filedialog.askopenfilename(
            title="Import Spectrum File", parent=self,
            filetypes=(("Spectrum Files", "*.spx *.sub *.txt"), ("All Files", "*.*"))
        )
        if filepath:
            self._load_spectrum_file(filepath, from_import=True)
    
    def _load_spectrum_file(self, filepath, from_import=False):
        """Unified function to load spectrum files of different types."""
        _, extension = os.path.splitext(filepath)
        new_levels_data = None
        parser_used = ""

        try:
            if extension.lower() == '.spx':
                new_levels_data = self._parse_spx(filepath)
                parser_used = ".spx"
            elif extension.lower() in ['.sub', '.txt']:
                # Try parsing as simple SUB format first
                new_levels_data = self._parse_sub(filepath)
                parser_used = ".sub"
                # If SUB parsing fails or returns no data, try parsing as FASTRAN format
                if not new_levels_data:
                    new_levels_data = self._parse_fastran_txt(filepath)
                    parser_used = "FASTRAN .txt"

            if new_levels_data is not None:
                if from_import: self._save_state_for_undo()
                self.levels_data = new_levels_data
                self._redraw_levels_table()
                self._update_plot()
                if from_import:
                    messagebox.showinfo("Import Success", f"Successfully imported {len(new_levels_data)} stress levels using {parser_used} parser.", parent=self)
            else:
                raise ValueError("Could not parse file with any available parser.")

        except Exception as e:
             messagebox.showerror("File Load Error", f"Could not load the spectrum file.\nError: {e}", parent=self)

        # If loading (not importing), also set the output path
        if not from_import:
            self.output_filepath = filepath
            self.output_label.config(text=f"Editing: {os.path.basename(filepath)}")

    def _parse_fastran_txt(self, filepath):
        """Parses a FASTRAN-generated text spectrum file with robust spacing."""
        with open(filepath, 'r') as f:
            lines = f.readlines()
        if len(lines) < 2: return None
        
        self.title_entry.delete(0, tk.END); self.title_entry.insert(0, lines[0].strip())
        header_parts = lines[1].strip().split()
        self.invert_entry.delete(0, tk.END); self.invert_entry.insert(0, header_parts[3])
        self.iclip_entry.delete(0, tk.END); self.iclip_entry.insert(0, header_parts[4])
        
        # --- NEW ROBUST PARSING LOGIC ---
        all_points_int = []
        for line in lines[2:]:
            parts = line.strip().split()
            for part in parts:
                all_points_int.append(int(part))

        if not all_points_int: return []
        if len(all_points_int) % 2 != 0: all_points_int.pop()
        
        stress_pairs = [[all_points_int[i], all_points_int[i+1]] for i in range(0, len(all_points_int), 2)]
        
        if not stress_pairs: return []
        
        levels = []
        current_pair = stress_pairs[0]
        count = 1
        for i in range(1, len(stress_pairs)):
            if stress_pairs[i] == current_pair:
                count += 1
            else:
                levels.append([str(current_pair[0]), str(current_pair[1]), str(count)])
                current_pair = stress_pairs[i]
                count = 1
        levels.append([str(current_pair[0]), str(current_pair[1]), str(count)])
        return levels
    
    def _parse_spx(self, filepath):
        """Parses an XML-based .spx spectrum file."""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            levels = []
            for sub_spectrum in root.findall('.//SubSpectrum'):
                for level in sub_spectrum.findall('B'):
                    smax = level.get('Mx', '0.0')
                    smin = level.get('Mn', '0.0')
                    cycles = level.get('C', '1')
                    levels.append([smax, smin, cycles])
            return levels
        except Exception as e:
            messagebox.showerror("SPX Parse Error", f"Failed to parse the .spx file: {e}", parent=self)
            return None

    def _parse_sub(self, filepath):
        """Parses a text-based .sub spectrum file."""
        try:
            levels = []
            with open(filepath, 'r') as f:
                # Skip the first line which is metadata
                next(f, None) 
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 3:
                        smax, smin, cycles = parts
                        levels.append([smax, smin, cycles])
            return levels
        except Exception as e:
            messagebox.showerror("SUB/TXT Parse Error", f"Failed to parse the file: {e}", parent=self)
            return None
    
    def _update_levels_from_spinbox(self):
        """Adds or removes rows from the table data based on the spinbox value."""
        self._save_state_for_undo()
        try:
            new_size = self.num_levels_var.get()
            if new_size < 0: return

            # Add new rows if necessary
            while len(self.levels_data) < new_size:
                self.levels_data.append(['0.0', '0.0', '1'])
            
            # Remove rows if necessary
            if len(self.levels_data) > new_size:
                self.levels_data = self.levels_data[:new_size]
            
            self._redraw_levels_table()
        except tk.TclError:
            pass # Handles case where spinbox is empty temporarily 

    def _update_plot(self):
        """Reads data from the table, applies SMF, and redraws the plot."""
        try:
            smf = float(self.smf_var.get())
        except (ValueError, tk.TclError):
            smf = 1.0

        plot_x = [0]
        plot_y = [0]
        cumulative_cycles = 0

        for row_widgets in self.level_widgets:
            try:
                smax = float(row_widgets[0].get()) * smf
                smin = float(row_widgets[1].get()) * smf
                cycles = int(row_widgets[2].get())

                for _ in range(cycles):
                    # Add points to trace one cycle
                    plot_x.append(cumulative_cycles)
                    plot_y.append(smin)
                    plot_x.append(cumulative_cycles + 0.5)
                    plot_y.append(smax)
                    plot_x.append(cumulative_cycles + 1)
                    plot_y.append(smin)
                    cumulative_cycles += 1
            except (ValueError, tk.TclError):
                continue # Skip rows with invalid data

        self.ax.clear()
        self.ax.plot(plot_x, plot_y, marker='o', markersize=2, linestyle='-')
        self.ax.set_title("Spectrum Visualization")
        self.ax.set_xlabel("Cumulative Cycles")
        self.ax.set_ylabel("Stress")
        self.ax.grid(True)
        self.plot_canvas.draw()

    def _redraw_levels_table(self):
        for widget in self.table_frame.winfo_children(): widget.destroy()
        self.level_widgets.clear()
        
        # Table Headers
        ttk.Label(self.table_frame, text="Max Stress", font="-weight bold").grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(self.table_frame, text="Min Stress", font="-weight bold").grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(self.table_frame, text="Cycles", font="-weight bold").grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(self.table_frame, text="Actions", font="-weight bold").grid(row=0, column=3, columnspan=3, pady=5)

        for i, data_row in enumerate(self.levels_data):
            smax, smin, cycles = data_row
            smax_entry = ttk.Entry(self.table_frame, width=15); smax_entry.insert(0, smax); smax_entry.grid(row=i + 1, column=0, padx=5, pady=2)
            smin_entry = ttk.Entry(self.table_frame, width=15); smin_entry.insert(0, smin); smin_entry.grid(row=i + 1, column=1, padx=5, pady=2)
            cycles_entry = ttk.Entry(self.table_frame, width=10); cycles_entry.insert(0, cycles); cycles_entry.grid(row=i + 1, column=2, padx=5, pady=2)
            
            # --- Add new editing buttons for each row ---
            up_button = ttk.Button(self.table_frame, text="↑", width=3, command=lambda i=i: self._move_level_up(i))
            up_button.grid(row=i + 1, column=3, padx=(10, 2))
            
            down_button = ttk.Button(self.table_frame, text="↓", width=3, command=lambda i=i: self._move_level_down(i))
            down_button.grid(row=i + 1, column=4, padx=2)

            delete_button = ttk.Button(self.table_frame, text="Delete", width=8, command=lambda i=i: self._delete_level(i))
            delete_button.grid(row=i + 1, column=5, padx=2)

            # Disable buttons on first/last rows
            if i == 0: up_button.config(state="disabled")
            if i == len(self.levels_data) - 1: down_button.config(state="disabled")
            
            self.level_widgets.append([smax_entry, smin_entry, cycles_entry])
        
        self.num_levels_var.set(len(self.levels_data))  

    def _set_output_file(self):
        filepath = filedialog.asksaveasfilename(
            title="Set Spectrum File Location",
            defaultextension=".txt",
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        if filepath:
            self.output_filepath = filepath
            self.output_label.config(text=f"File: {os.path.basename(filepath)}")

    def _load_data_from_file(self, filepath):
        try:
            if not os.path.exists(filepath) or os.path.basename(filepath) == 'dummy.txt':
                messagebox.showinfo("Info", f"Spectrum file '{os.path.basename(filepath)}' not found or is a dummy file. Opening a new spectrum editor.", parent=self)
                # Ensure we start with one empty row if no file is loaded
                if not self.levels_data:
                    self.levels_data.append(['0.0', '0.0', '1'])
                self._redraw_levels_table()
                return

            with open(filepath, 'r') as f:
                lines = f.readlines()

            if len(lines) < 2:
                messagebox.showwarning("Warning", f"File '{os.path.basename(filepath)}' is not a valid spectrum file.", parent=self)
                return

            title = lines[0].strip()
            header_parts = lines[1].strip().split()
            invert_val = header_parts[3]
            iclip_val = header_parts[4]

            self.title_entry.delete(0, tk.END); self.title_entry.insert(0, title)
            self.invert_entry.delete(0, tk.END); self.invert_entry.insert(0, invert_val)
            self.iclip_entry.delete(0, tk.END); self.iclip_entry.insert(0, iclip_val)

            format_specs = {1: {'width': 4}, 2: {'width': 5}, 3: {'width': 8}}
            col_width = format_specs.get(int(iclip_val), {'width': 8})['width']
            
            body_text = "".join(line.strip('\n\r') for line in lines[2:])
            all_points_int = [int(body_text[i:i+col_width]) for i in range(0, len(body_text), col_width) if body_text[i:i+col_width].strip()]
            
            if len(all_points_int) % 2 != 0:
                all_points_int.pop()
            
            stress_pairs = [[all_points_int[i], all_points_int[i+1]] for i in range(0, len(all_points_int), 2)]

            if not stress_pairs:
                self.levels_data = []
            else:
                self.levels_data = []
                current_pair = stress_pairs[0]
                count = 1
                for i in range(1, len(stress_pairs)):
                    if stress_pairs[i] == current_pair:
                        count += 1
                    else:
                        self.levels_data.append([str(current_pair[0]), str(current_pair[1]), str(count)])
                        current_pair = stress_pairs[i]
                        count = 1
                self.levels_data.append([str(current_pair[0]), str(current_pair[1]), str(count)])

            self._redraw_levels_table()
            self.output_filepath = filepath
            self.output_label.config(text=f"Editing: {os.path.basename(filepath)}")

        except Exception as e:
            messagebox.showerror("Spectrum Parsing Error", f"Could not load the spectrum file.\nError: {e}", parent=self)   

    def _generate_spectrum(self):
        if not self.output_filepath:
            messagebox.showerror("Error", "Please set a save location for the spectrum file first.", parent=self)
            return

        try:
            # Get SMF value, default to 1.0 if invalid
            try:
                smf = float(self.smf_var.get())
            except (ValueError, tk.TclError):
                smf = 1.0

            title = self.title_entry.get()
            invert = int(self.invert_entry.get())
            iclip = int(self.iclip_entry.get())
            
            levels = []
            total_cycles = 0
            overall_smax = -float('inf')
            overall_smin = float('inf')
            
            for row in self.level_widgets:
                # Apply the SMF to the stress values from the table
                smax = float(row[0].get()) * smf
                smin = float(row[1].get()) * smf
                cycles = int(row[2].get())
                
                if cycles < 1: continue
                
                levels.append({'smax': smax, 'smin': smin, 'cycles': cycles})
                total_cycles += cycles
                overall_smax = max(overall_smax, smax)
                overall_smin = min(overall_smin, smin)

            total_points = total_cycles * 2
            
            with open(self.output_filepath, 'w') as f:
                f.write(f"{title}\n")
                smax_header = int(round(overall_smax))
                smin_header = int(round(overall_smin))
                f.write(f" {total_points}    {smax_header}    {smin_header}    {invert}    {iclip}\n")

                format_specs = {1: {'width': 4, 'count': 20}, 2: {'width': 5, 'count': 16}, 3: {'width': 8, 'count': 10}}
                spec = format_specs.get(iclip, {'width': 8, 'count': 10})
                col_width = spec['width']
                cols_per_line = spec['count']

                line_str = ""
                current_col = 0
                for level in levels:
                    for _ in range(level['cycles']):
                        # Round the final, scaled values to integers for the output file
                        smax_int = int(round(level['smax']))
                        smin_int = int(round(level['smin']))
                        
                        # Add points to the line string
                        line_str += f"{smax_int:{col_width}d}"
                        current_col += 1
                        if current_col >= cols_per_line:
                            f.write(line_str + "\n")
                            line_str = ""
                            current_col = 0

                        line_str += f"{smin_int:{col_width}d}"
                        current_col += 1
                        if current_col >= cols_per_line:
                            f.write(line_str + "\n")
                            line_str = ""
                            current_col = 0

                if line_str:
                    f.write(line_str + "\n")

            messagebox.showinfo("Success", "Spectrum file successfully updated/created!", parent=self)
            self.callback(os.path.basename(self.output_filepath))
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Could not generate spectrum file:\n{e}", parent=self)

class FastranGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FASTRAN Input Generator v2.2")
        self.geometry("900x800")
        self.input_filepath = None
        self.help_window = None 
        self.fastran_exe_path = None
        self.config_filename = "fastran_gui.cfg"
        self.log_queue = queue.Queue()
        self.process = None
        
        # New variable to hold the full path to the selected spectrum file
        self.spectrum_full_path = None
        
        # New variables for plotting
        self.plot_x_data = []
        self.plot_y_data = []

        self._setup_maps()
        self._init_vars()
        self._create_widgets()
        self._load_config()
        self._update_all_states()

    def _setup_maps(self):
        # Combobox Maps
        self.nalp_map = {'0: Constant': '0', '1: Variable': '1'}
        self.nep_map = {'0: Elastic': '0', '1: Plasticity-Corrected': '1', '2: Closure Corrected': '2'}
        self.neqn_map = {'0: FASTRAN Equation': '0', '1: NASGRO Equation': '1'}
        self.ntyp_map = {
            'Center Crack Tension': '1', 'Compact C(T)': '2', 'Single-Edge Crack': '3', 
            'Single-Edge Bend': '4', 'Pressurized Cylinder': '5', 'Corner Crack (AGARD)': '6', 
            'Surface Crack': '0', 'Corner Crack': '7', 'Double Edge Crack': '8',
            'Through Crack at Hole': '-3', 'Two Through Cracks at Hole': '-4',
            'One Surface Crack at Hole': '-5', 'Two Surface Cracks at Hole': '-6',
            'Lap-Splice Joint (Through)': '-12', 'Lap-Splice Joint (Corner)': '-13',
            'Custom SIF (no hole)': '99', 'Custom SIF (at hole)': '-99'
        }
        self.ltyp_map = {'0: Tension': '0', '1: Bending': '1', '2: Combined': '2'}
        self.nfopt_map = {
            '0: Constant-Amplitude': '0', '1: Variable/Block Loading': '1', '2: TWIST Spectrum': '2',
            '3: Mini-TWIST Spectrum': '3', '4: FALSTAFF Spectrum': '4', '5: Space Shuttle Spectrum': '5',
            '6: Gaussian Spectrum (Not Recommended)': '6', '7: Helicopter Spectra': '7',
            '8: File - List of Stress Points': '8', '9: File - Flight-by-Flight': '9', '10: File - Flight Schedule': '10'
        }

        self.irate_map = {'1: dc/dN=da/dN': '1', '2: Independent Curves': '2', '4: Small/Large Cracks': '4'}
        self.ngc_map = {'0: Disable Transition': '0', '1: Enable Transition': '1'}
        self.nodkl_map = {'0: No Rivet-Load Decay': '0', '1: Use Rivet-Load Decay': '1'}
        self.ndkth_map = {'0: Direct Lookup': '0', '1: FASTRAN Form': '1', '2: NASGRO Form': '2'}
        self.ndke_map = {'0: Print Elastic SIF': '0', '1: Print Effective SIF': '1'}
        self.lfast_map = {
            '0: Normal Closure': '0', '1: Equivalent S\'o (SOBAR)': '1', '2: Linear Cumulative Dmg': '2',
            '3: Constant S\'o': '3', '4: Manual S\'o Ratio': '4'
        }
        self.kconst_map = {'0: Stress Loading': '0', '1: SIF Loading': '1'}
        self.ntcmax_map = {'0: Input Constraint': '0', '1: Plane-Stress (1st cycle)': '1'}
        self.kth_map = {
            '0: No Test': '0', '1: ASTM (K-gradient)': '1', '2: SIF Gradient': '2',
            '3: Step Loading': '3', '4: Kmax Controlled': '4'
        }

        # Create reverse maps for all for loading files
        for map_name in ['nalp', 'nep', 'neqn', 'ntyp', 'ltyp', 'nfopt', 'irate', 'ngc', 'nodkl', 'ndkth', 'ndke', 'lfast', 'kconst', 'ntcmax', 'kth']:
            if hasattr(self, f"{map_name}_map"):
                original_map = getattr(self, f"{map_name}_map")
                setattr(self, f"{map_name}_rev_map", {v: k for k, v in original_map.items()})

    def _init_vars(self):
        self.vars = {key: tk.StringVar(value=val) for key, val in self.get_default_data().items()}
        
        # Setup StringVars for all descriptive comboboxes
        self.vars['NALP_DESC'] = tk.StringVar(value=list(self.nalp_map.keys())[0])
        self.vars['NEP_DESC'] = tk.StringVar(value=list(self.nep_map.keys())[1]) 
        self.vars['NEQN_DESC'] = tk.StringVar(value=list(self.neqn_map.keys())[0])
        self.vars['NTYP_DESC'] = tk.StringVar(value=list(self.ntyp_map.keys())[0])
        self.vars['LTYP_DESC'] = tk.StringVar(value=list(self.ltyp_map.keys())[0])
        self.vars['NFOPT_DESC'] = tk.StringVar(value=list(self.nfopt_map.keys())[0])
        self.vars['IRATE_DESC'] = tk.StringVar(value=list(self.irate_map.keys())[0])
        self.vars['NGC_DESC'] = tk.StringVar(value=list(self.ngc_map.keys())[0])
        self.vars['NODKL_DESC'] = tk.StringVar(value=list(self.nodkl_map.keys())[0])
        self.vars['NDKTH_DESC'] = tk.StringVar(value=list(self.ndkth_map.keys())[0])
        self.vars['NDKE_DESC'] = tk.StringVar(value=list(self.ndke_map.keys())[0])
        self.vars['LFAST_DESC'] = tk.StringVar(value=list(self.lfast_map.keys())[0])
        self.vars['KCONST_DESC'] = tk.StringVar(value=list(self.kconst_map.keys())[0])
        self.vars['NTCMAX_DESC'] = tk.StringVar(value=list(self.ntcmax_map.keys())[0])
        self.vars['KTH_DESC'] = tk.StringVar(value=list(self.kth_map.keys())[0])

        self.table_data = [['0.0', '0.0']]
        self.sif_table_data = []
        self.sif_table_widgets = []
        
        # Add traces to variables that control the state of other widgets
        for key in ['NALP_DESC', 'NFOPT_DESC', 'NGC_DESC', 'KTH_DESC', 'NTYP_DESC', 'LTYP_DESC', 'IRATE_DESC']:
            self.vars[key].trace_add('write', self._update_all_states)

    def get_default_data(self):
        return {
            'OUTPUT_FILE': 'output.txt', 'SPECTRA': 'spectrum.txt', 'MAT': 'material name',
            'SYIELD': '0.0', 'SULT': '0.0', 'E': '0.0', 'ETA': '0.0',
            'ALP': '1.0', 'BETAT': '1.0', 'BETAW': '1.0', 'CRKNGC': '0.0',
            'C1': '0.0', 'C2': '0.0', 'C3': '0.0', 'C4': '0.0', 'C5': '0.0',
            'C6': '1.0', 'C7': '1.0', 'KF': '0.0', 'M': '0.0',
            'NTAB': '1', 'KTAB': '0',
            'RATE1': '1.E-9', 'ALP1': '3.0', 'BETAT1': '1.0', 'BETAW1': '1.0',
            'RATE2': '1.E-6', 'ALP2': '1.0', 'BETAT2': '1.0', 'BETAW2': '1.0',
            'NIPT': '0', 'NPRT': '0', 'LSTEP': '1', 'DCPR': '0.0',
            'NS': '1', 'INVERT': '0', 'NRC': '0',
            'W': '0.0', 'T': '0.0', 'CI': '0.0', 'AI': '0.0', 'CN': '0.0', 'AN': '0.0',
            'HN': '0.0', 'RAD': '0.0', 'RADF': '0.0', 'CF': '0.0',
            'SMAX': '0.0', 'SMIN': '0.0', 'DVALUE': '0.0',
            'NCYCLE1': '0', 'NCYCLE2': '0',
            'MAXSEQ': '0', 'MAXBLK': '0', 'LPRINT': '0', 'MAXLPR': '0',
            'NREP': '0', 'MARKER': '0', 'SPEAK': '0.0', 'SMEAN': '0.0',
            'SMAXTH': '0', 'RTH': '0', 'CONST': '0', 'PRT': '0',
            'GAMMA': '0.0', 'RADIUS': '0.0', 'RIVETS': '0.0', 'RLF1': '0.5',
            'RLF2': '0.5', 'DELTA': '0.0'
        }

    def _create_widgets(self):
        # --- Menubar ---
        menubar = tk.Menu(self); self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load FASTRAN Input...", command=self._load_file)
        file_menu.add_command(label="Load Material File...", command=self._load_material_file)
        file_menu.add_command(label="Set FASTRAN Path...", command=self._set_fastran_path)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        help_menu = tk.Menu(menubar, tearoff=0); help_menu.add_command(label="Help...", command=self._show_help)
        menubar.add_cascade(label="File", menu=file_menu); menubar.add_cascade(label="Help", menu=help_menu)
        
        # --- Top Action Frame ---
        top_frame = ttk.Frame(self, padding="5"); top_frame.pack(side="top", fill="x", pady=5)
        self.run_button = ttk.Button(top_frame, text="Save & Run FASTRAN", command=self._initiate_run)
        self.run_button.pack(side="right", padx=5)
        
        # --- Notebook for Tabs ---
        notebook = ttk.Notebook(self); notebook.pack(expand=True, fill='both', padx=5, pady=0)
        self.tab1 = ttk.Frame(notebook, padding="10"); self.tab2 = ttk.Frame(notebook, padding="10"); self.tab3 = ttk.Frame(notebook, padding="10")
        notebook.add(self.tab1, text='General & Material'); notebook.add(self.tab2, text='Crack Growth'); notebook.add(self.tab3, text='Geometry & Loading')
        
        self._create_tab1(); self._create_tab2(); self._create_tab3()

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Status: Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w', padding=5)
        status_bar.pack(side="bottom", fill="x")
    
    def _create_entry_row(self, parent, label, var_key, row, col=0, width=15, tooltip_text=None, state=tk.NORMAL):
        lbl = ttk.Label(parent, text=label); lbl.grid(row=row, column=col*2, sticky='w', padx=5, pady=2)
        ent = ttk.Entry(parent, textvariable=self.vars[var_key], width=width, state=state); ent.grid(row=row, column=col*2+1, sticky='ew', padx=5)
        if tooltip_text: ToolTip(ent, text=tooltip_text); ToolTip(lbl, text=tooltip_text)
        return lbl, ent

    def _create_combo_row(self, parent, label, var_key, row, values, col=0, tooltip_text=None, width=15):
        lbl = ttk.Label(parent, text=label); lbl.grid(row=row, column=col*2, sticky='w', padx=5, pady=2)
        combo = ttk.Combobox(parent, textvariable=self.vars[var_key], values=values, state='readonly', width=width); combo.grid(row=row, column=col*2+1, sticky='ew', padx=5)
        if tooltip_text: ToolTip(combo, text=tooltip_text); ToolTip(lbl, text=tooltip_text)
        return lbl, combo
        
    def _create_tab1(self):
        # --- Section 1: Files ---
        lf1 = ttk.LabelFrame(self.tab1, text="Section 1: FASTRAN Files", padding="10"); lf1.pack(fill="x", pady=5); lf1.columnconfigure(1, weight=1)
        # Input File
        self.input_file_label = ttk.Label(lf1, text="Input File: Not Set", relief="sunken", padding=2, anchor='w'); self.input_file_label.grid(row=0, column=0, columnspan=2, sticky='ew', padx=5, pady=2)
        ttk.Button(lf1, text="Set Save Location...", command=self._set_input_file).grid(row=0, column=2, padx=5)
        # Output File
        self._create_entry_row(lf1, "Output File:", 'OUTPUT_FILE', 1, 0, width=40, tooltip_text="Filename for the FASTRAN analysis output.")
        
        # --- Sections 2, 3, 10 ---
        lf23 = ttk.LabelFrame(self.tab1, text="Sections 2, 3, & 10: Loading and Material", padding="10"); lf23.pack(fill="x", pady=5); lf23.columnconfigure(1, weight=1)
        nfopt_frame = ttk.Frame(lf23); nfopt_frame.grid(row=0, column=0, columnspan=4, sticky='ew', pady=(0, 5)); nfopt_frame.columnconfigure(1, weight=1)
        self._create_combo_row(nfopt_frame, "Loading Option (NFOPT):", 'NFOPT_DESC', 0, list(self.nfopt_map.keys()), col=0, tooltip_text="Defines the type of spectrum loading.", width=35)
        
        spec_frame = ttk.Frame(lf23); spec_frame.grid(row=1, column=0, columnspan=4, sticky='ew'); spec_frame.columnconfigure(1, weight=1)
        self.spec_label, self.spec_entry = self._create_entry_row(spec_frame, "Spectrum File:", 'SPECTRA', 0, 0, width=40, tooltip_text="Filename of the spectrum loading file.\nUsed only for NFOPT = 5, 8, 9, 10.")
        
        # --- Reverted to two-button system ---
        ttk.Button(spec_frame, text="Browse...", command=self._browse_for_spectrum_file).grid(row=0, column=2, padx=5)
        self.edit_spec_button = ttk.Button(spec_frame, text="Edit Spectrum", command=self._open_spectrum_editor, state="disabled")
        self.edit_spec_button.grid(row=0, column=3, padx=5)

        mat_frame = ttk.Frame(lf23); mat_frame.grid(row=2, column=0, columnspan=4, sticky='ew'); mat_frame.columnconfigure(1, weight=1)
        self._create_entry_row(mat_frame, "Material Title:", 'MAT', 0, 0, width=40, tooltip_text="Any 60-character description of the material.")
        ttk.Button(mat_frame, text="Load from XML...", command=self._load_material_file).grid(row=0, column=2, padx=5)
        
        # --- Section 4 ---
        lf4 = ttk.LabelFrame(self.tab1, text="Section 4: Material Properties", padding="10"); lf4.pack(fill="x", pady=5)
        self._create_entry_row(lf4, "Yield Stress (SYIELD):", 'SYIELD', 0, 0, tooltip_text="Yield stress (0.2 percent offset).")
        self._create_entry_row(lf4, "Ultimate Strength (SULT):", 'SULT', 0, 1, tooltip_text="Ultimate tensile strength.")
        self._create_entry_row(lf4, "Elastic Modulus (E):", 'E', 1, 0, tooltip_text="Elastic modulus.")
        self._create_entry_row(lf4, "Poisson's Ratio (ETA):", 'ETA', 1, 1, tooltip_text="Poisson's ratio for plane strain.\nSet to 0 for plane stress (normally used).")
        self._create_entry_row(lf4, "Tensile Constraint (ALP):", 'ALP', 2, 0, tooltip_text="Tensile constraint factor.\n1.0 for plane-stress, 3.0 for plane-strain.")
        self._create_entry_row(lf4, "Comp. Constraint (BETAT):", 'BETAT', 2, 1, tooltip_text="Compressive constraint factor for intact material at crack tip.")
        self._create_entry_row(lf4, "Comp. Constraint (BETAW):", 'BETAW', 3, 0, tooltip_text="Compressive constraint factor along crack surface (or wake).")
        self._create_combo_row(lf4, "Constraint Opt (NALP):", 'NALP_DESC', 4, list(self.nalp_map.keys()), col=0, tooltip_text="0: Constraint factor (ALP) is constant as input.\n1: Constraint factor is variable (computed by the program).")
        self._create_combo_row(lf4, "Plasticity Opt (NEP):", 'NEP_DESC', 4, list(self.nep_map.keys()), col=1, tooltip_text="Effective SIF option.\n0: Elastic\n1: Plasticity-corrected (cyclic) - RECOMMENDED\n2: Closure-corrected (monotonic) - Use with caution")

    def _create_tab2(self):
        canvas = tk.Canvas(self.tab2, borderwidth=0, highlightthickness=0); scrollbar = ttk.Scrollbar(self.tab2, orient="vertical", command=canvas.yview)
        content_frame = ttk.Frame(canvas, padding="10"); content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set); canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y"); content_frame.columnconfigure(0, weight=1)
        
        lf56 = ttk.LabelFrame(content_frame, text="Sections 5 & 6: Growth Rate & Fracture Properties", padding="10"); lf56.grid(row=0, column=0, sticky="ew")
        
        self._create_combo_row(lf56, "IRATE:", 'IRATE_DESC', 0, list(self.irate_map.keys()), 0, tooltip_text="Number of crack-growth rate relations (J=1 to IRATE).", width=22)
        self.ngc_lbl, self.ngc_combo = self._create_combo_row(lf56, "NGC:", 'NGC_DESC', 0, list(self.ngc_map.keys()), 1, tooltip_text="Enable (1) or disable (0) the small-to-large crack transition.\nOnly used for IRATE=4.")
        self.crkngc_lbl, self.crkngc_entry = self._create_entry_row(lf56, "CRKNGC:", 'CRKNGC', 0, 2, tooltip_text="The crack length or depth where small-to-large crack transition occurs.")
        
        self._create_entry_row(lf56, "Coefficient (C1):", 'C1', 1, 0, tooltip_text="Crack-growth coefficient C1.")
        self._create_entry_row(lf56, "Power (C2):", 'C2', 1, 1, tooltip_text="Crack-growth power C2.")
        self._create_entry_row(lf56, "Threshold (C3):", 'C3', 2, 0, tooltip_text="Threshold constant C3.")
        self._create_entry_row(lf56, "Threshold (C4):", 'C4', 2, 1, tooltip_text="Threshold constant C4.")
        self._create_entry_row(lf56, "Fracture Tough. (C5):", 'C5', 3, 0, tooltip_text="Cyclic fracture toughness, C5.")
        self._create_entry_row(lf56, "Fracture Power (C6):", 'C6', 3, 1, tooltip_text="Power on fracture term, C6.")
        self._create_entry_row(lf56, "Threshold Power (C7):", 'C7', 4, 0, tooltip_text="Power on threshold term, C7.")
        self._create_entry_row(lf56, "Elastic-Plastic (KF):", 'KF', 4, 1, tooltip_text="Elastic-plastic fracture toughness, KF.")
        self._create_entry_row(lf56, "Toughness Param. (m):", 'M', 5, 0, tooltip_text="Fracture toughness parameter (0 <= m <= 1).")
        self._create_combo_row(lf56, "Equation (NEQN):", 'NEQN_DESC', 5, list(self.neqn_map.keys()), col=1, tooltip_text="Selects the crack-growth rate equation.\n0: FASTRAN equation\n1: NASGRO equation")
        
        self.lf7 = ttk.LabelFrame(content_frame, text="Section 7: Crack Growth Table", padding="10"); self.lf7.grid(row=1, column=0, sticky="ew", pady=5)
        table_ctrl_frame = ttk.Frame(self.lf7); table_ctrl_frame.pack(fill='x', pady=2)
        
        ntab_lbl = ttk.Label(table_ctrl_frame, text="Num. Points (NTAB):"); ntab_lbl.pack(side="left")
        ntab_tip = "If > 1, indicates number of points for tabular input.\nIf 0, program uses the equation from Section 6."
        ntab_spinbox = ttk.Spinbox(table_ctrl_frame, from_=0, to=100, textvariable=self.vars['NTAB'], width=5, command=self._update_table_from_ntab); ntab_spinbox.pack(side="left", padx=5)
        ToolTip(ntab_lbl, ntab_tip); ToolTip(ntab_spinbox, ntab_tip)
        
        self.ndkth_lbl = ttk.Label(table_ctrl_frame, text="NDKTH:")
        self.ndkth_lbl.pack(side="left", padx=(10, 0))
        self.ndkth_combo = ttk.Combobox(table_ctrl_frame, textvariable=self.vars['NDKTH_DESC'], values=list(self.ndkth_map.keys()), state='readonly', width=18)
        self.ndkth_combo.pack(side="left", padx=5)
        ndkth_tip = "Defines how the table is used."
        ToolTip(self.ndkth_lbl, ndkth_tip); ToolTip(self.ndkth_combo, ndkth_tip)
        
        ttk.Button(table_ctrl_frame, text="Paste from Clipboard", command=self._paste_into_table).pack(side='left', padx=(10, 0))

        self.table_frame_container = ttk.Frame(self.lf7, padding="5"); self.table_frame_container.pack(fill="both", expand=True)
        self._redraw_table()
        
        self.lf8 = ttk.LabelFrame(content_frame, text="Section 8: Transition Parameters (NALP=1 only)", padding="10"); self.lf8.grid(row=2, column=0, sticky="ew", pady=5)
        rate1_tip = "Crack-growth rate near the start of transition from flat-to-slant growth."
        rate2_tip = "Crack-growth rate near the end of the transition from flat-to-slant growth."
        self._create_entry_row(self.lf8, "RATE1:", 'RATE1', 0, 0, tooltip_text=rate1_tip); self._create_entry_row(self.lf8, "ALP1:", 'ALP1', 0, 1)
        self._create_entry_row(self.lf8, "BETAT1:", 'BETAT1', 0, 2); self._create_entry_row(self.lf8, "BETAW1:", 'BETAW1', 0, 3)
        self._create_entry_row(self.lf8, "RATE2:", 'RATE2', 1, 0, tooltip_text=rate2_tip); self._create_entry_row(self.lf8, "ALP2:", 'ALP2', 1, 1)
        self._create_entry_row(self.lf8, "BETAT2:", 'BETAT2', 1, 2); self._create_entry_row(self.lf8, "BETAW2:", 'BETAW2', 1, 3)

    def _create_tab3(self):
        canvas = tk.Canvas(self.tab3, borderwidth=0, highlightthickness=0); scrollbar = ttk.Scrollbar(self.tab3, orient="vertical", command=canvas.yview)
        content_frame = ttk.Frame(canvas, padding="10"); content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set); canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        
        # --- Create all frames first ---
        
        lf9 = ttk.LabelFrame(content_frame, text="Section 9: Data Output Options", padding="10")
        lf10 = ttk.LabelFrame(content_frame, text="Section 10: Specimen & Loading", padding="10")
        lf11 = ttk.LabelFrame(content_frame, text="Sections 11 & 13: Dimensions", padding="10")
        lf15 = ttk.LabelFrame(content_frame, text="Section 15: Pre-Crack Loading", padding="10")
        lf16 = ttk.LabelFrame(content_frame, text="Section 16: Special Options", padding="10")
        self.lf17 = ttk.LabelFrame(content_frame, text="Section 17: Primary Loading", padding="10")
        self.lf18 = ttk.LabelFrame(content_frame, text="Section 18: Load-Reduction Threshold Test", padding="10")

        # Container for conditional frames
        self.conditional_frame_container = ttk.Frame(content_frame)

        # Conditional frames have the container as their parent
        self.lf12 = ttk.LabelFrame(self.conditional_frame_container, text="Section 12: Custom Stress-Intensity Factor (NTYP=99/-99)", padding="10")
        self.lf14 = ttk.LabelFrame(self.conditional_frame_container, text="Section 14: Special Parameters", padding="10")
        
        # --- Populate all frames with their widgets ---
        
        # Populate lf9
        self._create_entry_row(lf9, "NIPT:", "NIPT", 0, 0, tooltip_text="If > 0, outputs detailed half-cycle data\nafter 'NIPT' crack-growth increments.")
        self._create_entry_row(lf9, "NPRT:", "NPRT", 0, 1, tooltip_text="Controls frequency of crack-length-vs-cycles output.\n<= 0: Use DCPR increment\n> 0: Print every NPRTth increment")
        self._create_entry_row(lf9, "LSTEP:", "LSTEP", 1, 0, tooltip_text="Number of load steps from min to max during NIPT printout.\nUse > 1 to study how crack surfaces open.")
        self._create_combo_row(lf9, "NDKE:", "NDKE_DESC", 1, list(self.ndke_map.keys()), col=1, tooltip_text="0: Print elastic SIF ranges.\n1: Print effective SIF ranges.")
        self._create_entry_row(lf9, "DCPR:", "DCPR", 2, 0, tooltip_text="Crack-growth increment for printed output\n(used when NPRT <= 0).")
        
        # Populate lf10
        lf10.columnconfigure(1, weight=1); lf10.columnconfigure(3, weight=1)
        self._create_combo_row(lf10, "Specimen Type (NTYP):", 'NTYP_DESC', 0, list(self.ntyp_map.keys()), tooltip_text="Defines the specimen and crack geometry.", width=30)
        self._create_combo_row(lf10, "Loading Type (LTYP):", 'LTYP_DESC', 1, list(self.ltyp_map.keys()), tooltip_text="Defines loading type for NTYP=0 and 7.\n0: Tension, 1: Bending, 2: Combined.")
        self._create_combo_row(lf10, "LFAST:", 'LFAST_DESC', 2, list(self.lfast_map.keys()), tooltip_text="Selects the crack-closure model.", width=25)
        self._create_entry_row(lf10, "Num. Notch Elem. (NS):", 'NS', 3, tooltip_text="Number of elements used to define the starter notch.")
        self.invert_lbl, self.invert_entry = self._create_entry_row(lf10, "INVERT:", "INVERT", 4)
        self.invert_tooltip = ToolTip(self.invert_entry, "")
        ToolTip(self.invert_lbl, "")
        self._create_combo_row(lf10, "KCONST:", "KCONST_DESC", 5, list(self.kconst_map.keys()), tooltip_text="0: Apply stress as external loading.\n1: Apply SIF directly (NTYP=1 or 2 only).")
        self.ntcmax_lbl, self.ntcmax_combo = self._create_combo_row(lf10, "NTCMAX:", "NTCMAX_DESC", 6, list(self.ntcmax_map.keys()), tooltip_text="Applies to negative NTYP only.\n0: Use user-input notch constraint.\n1: Assume plane-stress for first cycle.")

        # Populate lf12 (Conditional)
        sif_ctrl_frame = ttk.Frame(self.lf12); sif_ctrl_frame.pack(fill='x', pady=2)
        ktab_tooltip = "Number of SIF data pairs for user-input table.\nIf 0, a user-defined equation in subroutine SIF99 is assumed.\nMaximum is 50."
        ktab_lbl = ttk.Label(sif_ctrl_frame, text="Num. SIF Pairs (KTAB):"); ktab_lbl.pack(side="left"); ToolTip(ktab_lbl, ktab_tooltip)
        ktab_spinbox = ttk.Spinbox(sif_ctrl_frame, from_=0, to=50, textvariable=self.vars['KTAB'], width=5, command=self._update_sif_table_from_ktab)
        ktab_spinbox.pack(side="left", padx=5)
        ToolTip(ktab_spinbox, ktab_tooltip)
        ttk.Button(sif_ctrl_frame, text="Paste from Clipboard", command=self._paste_into_sif_table).pack(side='left', padx=(10, 0))
        self.sif_table_container = ttk.Frame(self.lf12, padding="5"); self.sif_table_container.pack(fill="both", expand=True)
        self._redraw_sif_table()
        
        # Populate lf14 (Conditional)
        self.gamma_frame = ttk.Frame(self.lf14)
        self._create_entry_row(self.gamma_frame, "GAMMA (Sb/S):", "GAMMA", 0, 0, tooltip_text="Ratio of outer fiber bending stress to remote tensile stress.")
        self.radius_frame = ttk.Frame(self.lf14)
        self._create_entry_row(self.radius_frame, "Cylinder Radius:", "RADIUS", 0, 0, tooltip_text="Radius of the pressurized cylinder.")
        self.lap_joint_frame = ttk.Frame(self.lf14)
        self._create_entry_row(self.lap_joint_frame, "Rivet Pitch:", "RIVETS", 0, 0, tooltip_text="Rivet pitch or linear spacing.")
        self._create_entry_row(self.lap_joint_frame, "Rivet Load Factor (RLF1):", "RLF1", 0, 1, tooltip_text="Rivet load factor (0 to 1). RLF1 + RLF2 must equal 1.")
        self._create_entry_row(self.lap_joint_frame, "By-pass Load Factor (RLF2):", "RLF2", 1, 0, tooltip_text="By-pass load factor (1 to 0).")
        self._create_entry_row(self.lap_joint_frame, "Interference (DELTA):", "DELTA", 1, 1, tooltip_text="Change in rivet radius.")
        self._create_combo_row(self.lap_joint_frame, "Rivet-Load Decay (NODKL):", "NODKL_DESC", 2, list(self.nodkl_map.keys()), col=0, width=25)
        self._create_entry_row(self.lap_joint_frame, "Bending/Tension (GAMMA):", "GAMMA", 3, 0)
        
        # Populate lf11
        self._create_entry_row(lf11, "Width/Half-Width (W):", "W", 0, 0, tooltip_text="One-half width of the specimen (w).")
        self._create_entry_row(lf11, "Thickness (T):", "T", 0, 1, tooltip_text="Specimen thickness (t).")
        self._create_entry_row(lf11, "Initial Crack Len (CI):", "CI", 1, 0, tooltip_text="Initial crack length (ci). For cracks at a hole, this is c_i + r.")
        self._create_entry_row(lf11, "Initial Crack Dep (AI):", "AI", 1, 1, tooltip_text="Initial crack depth (ai) for surface/corner cracks.")
        self._create_entry_row(lf11, "Final Crack Len (CF):", "CF", 2, 0, tooltip_text="Analysis terminates when crack length exceeds this value.")
        self._create_entry_row(lf11, "Hole/Notch Radius (RAD):", "RAD", 2, 1, tooltip_text="Radius (r) of a circular hole or semi-circular edge notch.")
        self._create_entry_row(lf11, "Starter Notch Len (CN):", "CN", 3, 0, tooltip_text="Length of the starter notch (cn). If CN=CI, no pre-cracking.")
        self._create_entry_row(lf11, "Starter Notch Dep (AN):", "AN", 3, 1, tooltip_text="Depth of the starter notch (an).")
        self._create_entry_row(lf11, "Notch Half-Height (HN):", "HN", 4, 0, tooltip_text="Half-height of the starter notch (hn).")
        self._create_entry_row(lf11, "Fastener Radius (RADF):", "RADF", 4, 1, tooltip_text="Radius of fastener (rf). Set to 0 for open hole.\nAccounts for fastener effects on closure.")

        # Populate lf15
        precrack_tip = "Constant-amplitude loading to grow crack from\nstarter notch (CN) to initial crack length (CI).\nRequired inputs, but only used if CN < CI."
        self._create_entry_row(lf15, "Max Stress (SMAX):", "SMAX", 0, 0, tooltip_text=precrack_tip)
        self._create_entry_row(lf15, "Min Stress (SMIN):", "SMIN", 0, 1, tooltip_text=precrack_tip)

        # Populate lf16
        self._create_entry_row(lf16, "NRC:", "NRC", 0, 0, tooltip_text="0: Normal\n-1: Used with LFAST=4 for manual S'o/Smax input.")
        self._create_entry_row(lf16, "DVALUE:", "DVALUE", 0, 1, tooltip_text="Value for NRC option.\nIf NRC=-1, this is the S'o/Smax ratio for LFAST=4.")
        self._create_entry_row(lf16, "NCYCLE1:", "NCYCLE1", 1, 0, tooltip_text="Start cycle for stress history output.")
        self._create_entry_row(lf16, "NCYCLE2:", "NCYCLE2", 1, 1, tooltip_text="End cycle for stress history output.")
        
        # Populate lf17
        self._create_entry_row(self.lf17, "MAXSEQ:", "MAXSEQ", 0, 0, tooltip_text="Total number of blocks or flights in the sequence to be repeated."); self._create_entry_row(self.lf17, "MAXBLK:", "MAXBLK", 0, 1, tooltip_text="Number of different kinds of blocks or flights.")
        self._create_entry_row(self.lf17, "LPRINT:", "LPRINT", 1, 0, tooltip_text="Print option for spectrum information."); self._create_entry_row(self.lf17, "MAXLPR:", "MAXLPR", 1, 1, tooltip_text="Number of flights/blocks to be printed out.")
        self.speak_lbl, self.speak_entry_main = self._create_entry_row(self.lf17, "SPEAK:", "SPEAK", 2, 0, tooltip_text="Highest stress in the spectrum, used for scaling."); self.smean_lbl, self.smean_entry = self._create_entry_row(self.lf17, "SMEAN:", "SMEAN", 2, 1, tooltip_text="Mean stress for TWIST, Mini-TWIST, or Gaussian spectra.")
        self.nrep_lbl, self.nrep_ent = self._create_entry_row(self.lf17, "NREP:", "NREP", 3, 0, tooltip_text="Number of spectrum repetitions (for NFOPT=8 only)."); self.marker_lbl, self.marker_ent = self._create_entry_row(self.lf17, "MARKER:", "MARKER", 3, 1, tooltip_text="Starting point marker in spectrum (for NFOPT=8 only).")

        # Populate lf18
        self._create_combo_row(self.lf18, "Test Type (KTH):", "KTH_DESC", 0, list(self.kth_map.keys()), tooltip_text="Selects the type of load-reduction threshold test.", width=25)
        self.smaxth_lbl, self.smaxth_entry = self._create_entry_row(self.lf18, "Start SMAX (SMAXTH):", "SMAXTH", 1, 0, tooltip_text="Maximum stress level at the start of the load-reduction test.")
        self.rth_lbl, self.rth_entry = self._create_entry_row(self.lf18, "Stress Ratio (RTH):", "RTH", 1, 1, tooltip_text="Stress ratio (R) for the threshold test.")
        self.const_lbl, self.const_entry = self._create_entry_row(self.lf18, "Constant (CONST):", "CONST", 2, 0, tooltip_text="Constant related to how load is reduced during the test.")
        self.prt_lbl, self.prt_entry = self._create_entry_row(self.lf18, "Percent (PRT):", "PRT", 2, 1, tooltip_text="Percent load increase/decrease at each step.\nUsed only for KTH=3.")

        # --- Pack all frames in the desired order ---
        lf9.pack(fill="x", pady=5, anchor="n")
        lf10.pack(fill="x", pady=5, anchor="n")
        self.conditional_frame_container.pack(fill="x", anchor="n")
        lf11.pack(fill="x", pady=5, anchor="n")
        lf15.pack(fill="x", pady=5, anchor="n")
        lf16.pack(fill="x", pady=5, anchor="n")
        self.lf17.pack(fill="x", pady=5, anchor="n")
        self.lf18.pack(fill="x", pady=5, anchor="n")

        content_frame.update_idletasks(); canvas.config(scrollregion=canvas.bbox("all"))

    def _browse_for_spectrum_file(self):
        """Opens a file dialog and stores the full path to the selected spectrum file."""
        filepath = filedialog.askopenfilename(
            title="Select Spectrum File",
            filetypes=(("Spectrum Files", "*.txt *.spx *.sub"), ("All Files", "*.*"))
        )
        if filepath:
            self.vars['SPECTRA'].set(os.path.basename(filepath))
            self.spectrum_full_path = filepath
            self.edit_spec_button.config(state="normal") # Enable the edit button

    def _open_spectrum_editor(self):
        """Opens the spectrum editor with the currently selected file."""
        if self.spectrum_full_path and os.path.exists(self.spectrum_full_path):
            SpectrumCreatorWindow(self, self._on_spectrum_created, load_from_file=self.spectrum_full_path)
        else:
            messagebox.showwarning("File Not Found", "Please select a valid spectrum file using the 'Browse...' button first.", parent=self)

    def _parse_lkpx_file(self, filepath):
        """Parses an XML-based material file to extract key properties."""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Define a namespace dictionary to handle potential namespaces in the XML
            ns = {'ns': root.tag.split('}')[0][1:] if '}' in root.tag else ''}
            path = './/ns:Material/ns:BulkDetails/' if ns['ns'] else './/Material/BulkDetails/'
            
            properties = {}
            properties['MAT'] = root.findtext('.//ns:Material/ns:Name', default='', namespaces=ns).strip()
            properties['SYIELD'] = root.findtext(path + 'ns:PropertyData[@property="yld"]/ns:Data', default='0.0', namespaces=ns)
            properties['SULT'] = root.findtext(path + 'ns:PropertyData[@property="ult_strength"]/ns:Data', default='0.0', namespaces=ns)
            properties['E'] = root.findtext(path + 'ns:PropertyData[@property="e"]/ns:Data', default='0.0', namespaces=ns)
            properties['ETA'] = root.findtext(path + 'ns:PropertyData[@property="poisson"]/ns:Data', default='0.0', namespaces=ns)

            return properties
        except ET.ParseError as e:
            messagebox.showerror("XML Parse Error", f"Failed to parse the material file: {e}")
            return None
        except Exception as e:
            messagebox.showerror("Material File Error", f"An unexpected error occurred while reading the material file: {e}")
            return None

    def _load_material_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Material File",
            filetypes=(
                ("LK Pro-X Material File", "*.lkpx"),
                ("XML Files", "*.xml"),
                ("Text Files", "*.txt"), 
                ("All Files", "*.*")
            )
        )
        if not filepath:
            return

        properties = self._parse_lkpx_file(filepath)
        
        if properties:
            for key, value in properties.items():
                if key in self.vars and value is not None:
                    self.vars[key].set(value)
            messagebox.showinfo("Success", f"Successfully loaded material: {properties.get('MAT')}")

    def _update_all_states(self, *args):
        # Update NALP-dependent widgets
        if self.vars['NALP_DESC'].get() == self.nalp_rev_map.get('1'): self.lf8.grid()
        else: self.lf8.grid_remove()
        
        # Update IRATE-dependent widgets
        is_irate4 = (self.irate_map.get(self.vars['IRATE_DESC'].get()) == '4')
        ngc_state = tk.NORMAL if is_irate4 else tk.DISABLED
        self.ngc_lbl.config(state=ngc_state); self.ngc_combo.config(state=ngc_state)
        self.crkngc_lbl.config(state=ngc_state); self.crkngc_entry.config(state=ngc_state)
        if not is_irate4: self.vars['NGC_DESC'].set(self.ngc_rev_map['0'])

        # Update NGC-dependent widgets
        ngc_is_enabled = (self.ngc_map.get(self.vars['NGC_DESC'].get()) == '1')
        self.crkngc_entry.config(state=tk.NORMAL if (is_irate4 and ngc_is_enabled) else tk.DISABLED)

        nfopt_code = self.nfopt_map.get(self.vars['NFOPT_DESC'].get(), '0')

        # Logic for INVERT parameter's state and dynamic tooltip
        invert_tooltips = {
            '2': "TWIST spectrum clipping option.\n0-1: Normal\n2: Clip above Level II\n3: Clip above Level III, etc.",
            '3': "Mini-TWIST spectrum clipping option.\n0-1: Normal\n2: Clip above Level II\n3: Clip above Level III, etc.",
            '4': "FALSTAFF spectrum option.\n0: Normal sequence\n1: Inverted sequence (mirror image)",
            '5': "Space Shuttle spectrum option.\n0: Full spectrum from 'stsn' file\n1: Short spectrum from 'stsn' file",
            '7': "Helicopter spectrum option.\n1: Felix-28 flight-load sequence\n2: Helix-32 flight-load sequence",
            '8': "Order of stress points in the spectrum file.\n0: max, min, max, min...\n1: min, max, min, max...",
            '9': "Order of stress points in the spectrum file.\n0: max, min, max, min...\n1: min, max, min, max..."
        }

        if nfopt_code in invert_tooltips: 
            self.invert_entry.config(state=tk.NORMAL)
            self.invert_lbl.config(state=tk.NORMAL)
            self.invert_tooltip.text = invert_tooltips[nfopt_code]
            ToolTip(self.invert_lbl, invert_tooltips[nfopt_code])
        else: 
            self.invert_entry.config(state=tk.DISABLED)
            self.invert_lbl.config(state=tk.DISABLED)
            tip_text = "Not used for this NFOPT selection."
            self.invert_tooltip.text = tip_text
            ToolTip(self.invert_lbl, tip_text)
        
        for widget in [self.nrep_lbl, self.nrep_ent, self.marker_lbl, self.marker_ent]: 
            widget.grid() if nfopt_code == '8' else widget.grid_remove()
        
        self.smean_entry.config(state=tk.NORMAL if nfopt_code in ['2', '3', '6'] else tk.DISABLED)
        self.speak_entry_main.config(state=tk.NORMAL if nfopt_code not in ['0', '1', '2', '3'] else tk.DISABLED)

        spec_file_needed = (nfopt_code in ['5', '8', '9', '10'])
        spec_state = tk.NORMAL if spec_file_needed else tk.DISABLED
        for widget in [self.spec_entry, self.spec_label]: widget.config(state=spec_state)
        if not spec_file_needed and self.vars['SPECTRA'].get() != "dummy.txt": self.vars['SPECTRA'].set("dummy.txt")

        ntyp_code = self.ntyp_map.get(self.vars['NTYP_DESC'].get())
        ltyp_code = self.ltyp_map.get(self.vars['LTYP_DESC'].get())
        
        # --- Logic for Conditional Frames (lf12 and lf14) ---
        self.lf12.pack_forget()
        self.lf14.pack_forget()
        self.gamma_frame.pack_forget()
        self.radius_frame.pack_forget()
        self.lap_joint_frame.pack_forget()

        # Check and pack lf12 (Custom SIF)
        if ntyp_code in ['99', '-99']:
            self.lf12.pack(fill="x", pady=5, anchor="n")
        else:
            if self.vars['KTAB'].get() != '0':
                self.vars['KTAB'].set('0'); self.sif_table_data.clear(); self._redraw_sif_table()
        
        # Check and pack lf14 (Special Params)
        show_lf14 = False
        if ntyp_code == '5': # Pressurized Cylinder
            self.radius_frame.pack(fill='x', expand=True, padx=5, pady=2)
            show_lf14 = True
        elif ntyp_code in ['-12', '-13']: # Lap-Splice Joint
            self.lap_joint_frame.pack(fill='x', expand=True, padx=5, pady=2)
            show_lf14 = True
        elif (ntyp_code in ['0', '7'] and ltyp_code == '2'): # Surface/Corner Crack with Combined Loading
            self.gamma_frame.pack(fill='x', expand=True, padx=5, pady=2)
            show_lf14 = True
        
        if show_lf14:
            self.lf14.pack(fill="x", pady=5, anchor="n")

        # Update KTH-dependent widgets
        kth_code = self.kth_map.get(self.vars['KTH_DESC'].get(), '0')
        is_kth_active = (kth_code != '0')
        kth_state = tk.NORMAL if is_kth_active else tk.DISABLED
        for widget in [self.smaxth_lbl, self.smaxth_entry, self.rth_lbl, self.rth_entry, self.const_lbl, self.const_entry]:
            widget.config(state=kth_state)
        
        prt_state = tk.NORMAL if kth_code == '3' else tk.DISABLED
        self.prt_lbl.config(state=prt_state); self.prt_entry.config(state=prt_state)

    def _set_fastran_path(self):
        """Opens a dialog to select the FASTRAN.exe and saves the path."""
        filepath = filedialog.askopenfilename(
            title="Select FASTRAN Executable",
            filetypes=(("Executable Files", "*.exe"), ("All Files", "*.*"))
        )
        if filepath:
            self.fastran_exe_path = filepath
            self._save_config()
            self.status_var.set(f"FASTRAN path set to: {self.fastran_exe_path}")

    def _load_config(self):
        """Loads the saved FASTRAN executable path from the config file."""
        try:
            if os.path.exists(self.config_filename):
                with open(self.config_filename, 'r') as f:
                    self.fastran_exe_path = f.readline().strip()
                if self.fastran_exe_path:
                    self.status_var.set("FASTRAN path loaded from config.")
                else:
                    self.status_var.set("Status: FASTRAN path not set. Please set it in File -> Set FASTRAN Path...")
        except Exception as e:
            messagebox.showerror("Config Error", f"Failed to load configuration file.\n{e}")

    def _save_config(self):
        """Saves the FASTRAN executable path to the config file."""
        try:
            with open(self.config_filename, 'w') as f:
                f.write(self.fastran_exe_path)
        except Exception as e:
            messagebox.showerror("Config Error", f"Failed to save configuration file.\n{e}")
            
    def _save_input_file(self):
        """Saves the current GUI state to the specified input file."""
        if not self.input_filepath:
            self._set_input_file()
        if not self.input_filepath:
            return False
            
        if not self._run_validation_checks():
            return False

        current_values = {key: var.get() for key, var in self.vars.items()}
        current_table_data = [[row[0].get(), row[1].get()] for row in self.table_widgets]
        
        maps_to_pass = {f"{name}_map": getattr(self, f"{name}_map") for name in 
                        ['nalp', 'nep', 'neqn', 'ntyp', 'ltyp', 'nfopt', 'irate', 'ngc', 
                         'nodkl', 'ndkth', 'ndke', 'lfast', 'kconst', 'ntcmax', 'kth']}
        
        success = generate_fastran_file(current_values, current_table_data, self.input_filepath, maps_to_pass)
        if success:
            self.status_var.set(f"Successfully saved input file: {os.path.basename(self.input_filepath)}")
        return success

    def _initiate_run(self):
        """Handler for the 'Save & Run' button. Saves the file and executes FASTRAN."""
        if not self.fastran_exe_path or not os.path.exists(self.fastran_exe_path):
            messagebox.showwarning("Setup Required", "The path to FASTRAN.exe has not been set or is invalid.\nPlease set it via the 'File -> Set FASTRAN Path...' menu.")
            return

        output_filename = self.vars['OUTPUT_FILE'].get().strip()
        if not output_filename.lower().endswith('.txt'):
            output_filename += '.txt'
            self.vars['OUTPUT_FILE'].set(output_filename)

        if not self._save_input_file():
            self.status_var.set("Status: Save failed. Aborting run.")
            return
            
        self.run_button.config(state="disabled")
        self.status_var.set("Status: Running FASTRAN...")
        
        # Clear previous plot data
        self.plot_x_data.clear()
        self.plot_y_data.clear()

        thread = threading.Thread(target=self._fastran_worker, daemon=True)
        thread.start()

        self._create_log_window()
        self.after(100, self._process_log_queue)

    def _fastran_worker(self):
        """Runs the FASTRAN executable in a separate thread."""
        try:
            input_filename = os.path.basename(self.input_filepath)
            output_filename = self.vars['OUTPUT_FILE'].get()
            
            # Prepare the input that FASTRAN.exe expects
            fastran_input = f"{input_filename}\n{output_filename}\n"

            # Use Popen to start the process
            self.process = subprocess.Popen(
                [self.fastran_exe_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Redirect stderr to stdout
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=os.path.dirname(self.input_filepath) # Run in the same directory as the input file
            )

            # Write the filenames to FASTRAN's stdin
            self.process.stdin.write(fastran_input)
            self.process.stdin.flush()

            # Read the output line by line and put it in the queue
            for line in iter(self.process.stdout.readline, ''):
                self.log_queue.put(line)
            
        except Exception as e:
            self.log_queue.put(f"\n--- THREAD ERROR ---\n{e}\n")
        finally:
            if self.process:
                self.process.stdout.close()
                self.process.stdin.close()
                return_code = self.process.wait()
                self.log_queue.put(f"\n--- PROCESS FINISHED (Exit Code: {return_code}) ---\n")
            self.log_queue.put(None) # Sentinel value to indicate completion

    def _create_log_window(self):
        """Creates a Toplevel window with tabs for log output and a real-time plot."""
        self.log_window = tk.Toplevel(self)
        self.log_window.title("FASTRAN Console Output")
        self.log_window.geometry("800x500")
        
        # --- Top Button Frame ---
        button_frame = ttk.Frame(self.log_window, padding=5)
        button_frame.pack(side=tk.TOP, fill=tk.X)
        self.save_results_button = ttk.Button(button_frame, text="Save Full Results As...", command=self._save_parsed_results, state="disabled")
        self.save_results_button.pack(side=tk.RIGHT)

        # --- Create a Notebook (tab container) ---
        log_notebook = ttk.Notebook(self.log_window)
        log_notebook.pack(fill=tk.BOTH, expand=True)

        # --- Tab 1: Console Log ---
        log_frame = ttk.Frame(log_notebook)
        log_notebook.add(log_frame, text="Console Log")
        
        log_text = tk.Text(log_frame, wrap='word', height=20, width=100, font=("Courier", 9))
        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill="y")
        log_text['yscrollcommand'] = log_scrollbar.set
        self.log_text_widget = log_text

        # --- Tab 2: Crack Growth Plot ---
        plot_frame = ttk.Frame(log_notebook)
        log_notebook.add(plot_frame, text="Crack Growth Plot")

        fig = Figure(figsize=(7, 5), dpi=100)
        self.ax = fig.add_subplot(111)
        self.ax.set_xlabel("Cycles")
        self.ax.set_ylabel("c* - Rad (crack length)")
        self.ax.set_title("Real-time Crack Growth")
        self.ax.grid(True)
        
        self.plot_canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        self.plot_canvas.draw()
        self.plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _process_log_queue(self):
        """Checks the queue for new log messages, displays them, and updates the plot."""
        try:
            while True:
                line = self.log_queue.get_nowait()
                if line is None: # Sentinel found
                    self.status_var.set("Status: Run Complete.")
                    self.run_button.config(state="normal")
                    self.save_results_button.config(state="normal")
                    # Final plot redraw to ensure all points are shown
                    self._update_plot()
                    return
                else:
                    self.log_text_widget.insert(tk.END, line)
                    self.log_text_widget.see(tk.END)
                    self._parse_and_plot_line(line)
        except queue.Empty:
            self.after(100, self._process_log_queue)

    def _parse_and_plot_line(self, line):
        """Parses a line of console output and adds data to the plot if it matches the format."""
        if "C*- RAD =" in line and "CYCLES =" in line:
            try:
                parts = line.split()
                c_minus_rad = float(parts[parts.index("C*-") + 3])
                cycles = float(parts[parts.index("CYCLES") + 2])
                
                self.plot_x_data.append(cycles)
                self.plot_y_data.append(c_minus_rad)
                
                # Update plot periodically to avoid being too slow
                if len(self.plot_x_data) % 5 == 0:
                    self._update_plot()
            except (ValueError, IndexError):
                pass # Ignore lines that look like data but parse incorrectly
                
    def _update_plot(self):
        """Clears and redraws the matplotlib plot with current data."""
        if not self.plot_x_data: return
        self.ax.clear()
        self.ax.plot(self.plot_x_data, self.plot_y_data, marker='.', linestyle='-')
        self.ax.set_xlabel("Cycles")
        self.ax.set_ylabel("c* - Rad (crack length)")
        self.ax.set_title("Real-time Crack Growth")
        self.ax.grid(True)
        self.plot_canvas.draw()

    def _parse_output_file(self):
        """Reads a completed FASTRAN output file and extracts the tabular data."""
        output_filepath = os.path.join(os.path.dirname(self.input_filepath), self.vars['OUTPUT_FILE'].get())
        if not os.path.exists(output_filepath):
            messagebox.showerror("File Not Found", f"The output file could not be found:\n{output_filepath}", parent=self.log_window)
            return None, None

        header = []
        data_table = []
        in_data_section = False

        try:
            with open(output_filepath, 'r') as f:
                for line in f:
                    stripped_line = line.strip()
                    if not stripped_line:
                        continue

                    # Look for the header line to start capturing data
                    if "BLOCK" in stripped_line and "C_crack" in stripped_line:
                        header = stripped_line.split()
                        in_data_section = True
                        continue
                    
                    if in_data_section:
                        # Stop if we hit the failure message
                        if "SPECIMEN FAILED" in stripped_line:
                            break
                        # Assuming data lines start with a digit (the block number)
                        if stripped_line.split()[0].isdigit():
                            data_table.append(stripped_line.split())
            
            if not data_table:
                return None, None # No data found in file

            return header, data_table

        except Exception as e:
            messagebox.showerror("Parsing Error", f"An error occurred while parsing the output file.\n{e}", parent=self.log_window)
            return None, None

    def _save_parsed_results(self):
        """Parses the output file and saves the data to a user-specified file (e.g., CSV)."""
        header, data = self._parse_output_file()

        if not data:
            messagebox.showwarning("No Data", "No tabular result data could be parsed from the output file.", parent=self.log_window)
            return

        save_path = filedialog.asksaveasfilename(
            title="Save Results As",
            parent=self.log_window,
            defaultextension=".csv",
            filetypes=(("CSV File", "*.csv"), ("All Files", "*.*"))
        )

        if not save_path:
            return # User cancelled

        try:
            with open(save_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(data)
            messagebox.showinfo("Success", f"Successfully saved results to:\n{os.path.basename(save_path)}", parent=self.log_window)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save the file.\n{e}", parent=self.log_window)
    
    def _set_input_file(self):
        filepath = filedialog.asksaveasfilename(title="Set FASTRAN Input File", defaultextension=".txt", filetypes=(("Text Files", "*.txt"),))
        if filepath:
            self._set_input_path(filepath)
            # Set default output filename based on input
            base_name = os.path.basename(filepath)
            self.vars['OUTPUT_FILE'].set(f"o_{base_name}")

    def _update_table_from_ntab(self):
        try:
            new_size = int(self.vars['NTAB'].get())
            if new_size < 0: raise ValueError
            current_data = [[row[0].get(), row[1].get()] for row in self.table_widgets]
            while len(current_data) < new_size: current_data.append(['0.0', '0.0'])
            self.table_data = current_data[:new_size]
            self._redraw_table()
        except ValueError:
            messagebox.showerror("Error", "NTAB must be a non-negative integer.")

    def _redraw_table(self):
        for widget in self.table_frame_container.winfo_children(): widget.destroy()
        self.table_widgets = []
        if not self.table_data: return
        
        ttk.Label(self.table_frame_container, text="dK_eff", font="-weight bold").grid(row=0, column=0, padx=5, pady=2)
        ttk.Label(self.table_frame_container, text="da/dN", font="-weight bold").grid(row=0, column=1, padx=5, pady=2)
        
        for i, (dk, rate) in enumerate(self.table_data):
            e_dk = ttk.Entry(self.table_frame_container, width=15); e_dk.insert(0, dk); e_dk.grid(row=i + 1, column=0, padx=5, pady=2)
            e_rate = ttk.Entry(self.table_frame_container, width=15); e_rate.insert(0, rate); e_rate.grid(row=i + 1, column=1, padx=5, pady=2)
            self.table_widgets.append([e_dk, e_rate])

    def _paste_into_table(self):
        """Parses tab- or space-delimited data from the clipboard and populates the crack growth table."""
        try:
            clipboard_content = self.clipboard_get()
            lines = clipboard_content.strip().split('\n')
            
            new_table_data = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) < 2:
                    parts = line.split()
                
                if len(parts) >= 2:
                    dk = float(parts[0])
                    rate = float(parts[1])
                    new_table_data.append([str(dk), str(rate)])
                else:
                    raise ValueError("Each line must contain at least two columns.")

            if not new_table_data:
                messagebox.showwarning("Paste Warning", "No valid data was found on the clipboard.", parent=self)
                return

            self.table_data = new_table_data
            self.vars['NTAB'].set(str(len(self.table_data)))
            self._redraw_table()
            messagebox.showinfo("Paste Success", f"Successfully pasted {len(new_table_data)} data points.", parent=self)

        except (tk.TclError, ValueError) as e:
            messagebox.showerror(
                "Paste Error",
                "Could not paste data from clipboard.\n"
                "Please ensure you have copied two columns of numeric data.\n\n"
                f"Details: {e}",
                parent=self
            )

    def _paste_into_sif_table(self):
            """Parses tab- or space-delimited data from the clipboard and populates the SIF table."""
            try:
                clipboard_content = self.clipboard_get()
                lines = clipboard_content.strip().split('\n')
                
                new_sif_data = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) < 2:
                        parts = line.split()
                    
                    if len(parts) >= 2:
                        cw = float(parts[0])
                        fc = float(parts[1])
                        new_sif_data.append([str(cw), str(fc)])
                    else:
                        raise ValueError("Each line must contain at least two columns.")
    
                if not new_sif_data:
                    messagebox.showwarning("Paste Warning", "No valid data was found on the clipboard.", parent=self)
                    return
    
                # Check if pasted data exceeds the max allowed size
                if len(new_sif_data) > 50:
                    messagebox.showwarning("Paste Warning", "Pasted data exceeds the maximum of 50 rows.\nOnly the first 50 rows will be used.", parent=self)
                    new_sif_data = new_sif_data[:50]
    
                self.sif_table_data = new_sif_data
                self.vars['KTAB'].set(str(len(self.sif_table_data)))
                self._redraw_sif_table()
                messagebox.showinfo("Paste Success", f"Successfully pasted {len(self.sif_table_data)} data points.", parent=self)
    
            except (tk.TclError, ValueError) as e:
                messagebox.showerror(
                    "Paste Error",
                    "Could not paste data from clipboard.\n"
                    "Please ensure you have copied two columns of numeric data.\n\n"
                    f"Details: {e}",
                    parent=self
                )

    def _redraw_sif_table(self):
        """Clears and redraws the SIF table widgets based on self.sif_table_data."""
        for widget in self.sif_table_container.winfo_children():
            widget.destroy()
        self.sif_table_widgets.clear()
        if not self.sif_table_data: return
        
        ttk.Label(self.sif_table_container, text="Norm. Crack (c/w)", font="-weight bold").grid(row=0, column=0, padx=5, pady=2)
        ttk.Label(self.sif_table_container, text="Norm. SIF (Fc)", font="-weight bold").grid(row=0, column=1, padx=5, pady=2)
        
        for i, (cw, fc) in enumerate(self.sif_table_data):
            e_cw = ttk.Entry(self.sif_table_container, width=15); e_cw.insert(0, str(cw)); e_cw.grid(row=i + 1, column=0, padx=5, pady=2)
            e_fc = ttk.Entry(self.sif_table_container, width=15); e_fc.insert(0, str(fc)); e_fc.grid(row=i + 1, column=1, padx=5, pady=2)
            self.sif_table_widgets.append([e_cw, e_fc])

    def _update_sif_table_from_ktab(self):
        """Updates the SIF table based on the value in the KTAB entry widget."""
        try:
            new_size = int(self.vars['KTAB'].get())
            if new_size < 0: raise ValueError
            current_data = [[row[0].get(), row[1].get()] for row in self.sif_table_widgets]
            while len(current_data) < new_size: current_data.append(['0.0', '0.0'])
            self.sif_table_data = current_data[:new_size]
            self._redraw_sif_table()
        except ValueError:
            messagebox.showerror("Error", "KTAB must be a non-negative integer.")

    def _load_file(self):
        filepath = filedialog.askopenfilename(title="Select FASTRAN Input File", filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")))
        if not filepath: return
            
        self._set_input_path(filepath)
        parsed_data, table_data = parse_fastran_file(filepath)
        
        if parsed_data:
            # Load simple variables first
            for key, value in parsed_data.items():
                if key in self.vars: self.vars[key].set(value)
            
            # Set descriptive variables for comboboxes using reverse maps
            for map_name in ['nalp', 'nep', 'neqn', 'ntyp', 'ltyp', 'nfopt', 'irate', 'ngc', 'nodkl', 'ndkth', 'ndke', 'lfast', 'kconst', 'ntcmax', 'kth']:
                code_key = map_name.upper()
                if map_name == 'nodkl': code_key = 'NODKL' # Handle specific capitalization
                
                desc_key = f"{code_key}_DESC"
                
                if code_key in parsed_data and hasattr(self, f"{map_name}_rev_map"):
                    rev_map = getattr(self, f"{map_name}_rev_map")
                    desc_val = rev_map.get(parsed_data[code_key], '')
                    if desc_key in self.vars:
                        self.vars[desc_key].set(desc_val)

            self.table_data = table_data if table_data else [['0.0', '0.0']]
            self.vars['NTAB'].set(str(len(self.table_data)))
            self._redraw_table()
            self._update_all_states()

    def _load_material_file(self):
        filepath = filedialog.askopenfilename(title="Select Material File", filetypes=(("XML/Text Files", "*.xml *.lkxp *.txt"), ("All Files", "*.*")))
        if not filepath: return
        name, table, properties = parse_material_xml(filepath)
        if name: self.vars['MAT'].set(name)
        if table: self.vars['NTAB'].set(str(len(table))); self.table_data = table; self._redraw_table()
        if properties:
            for key, value in properties.items():
                if key in self.vars: self.vars[key].set(value)

    def _set_input_path(self, filepath):
        self.input_filepath = filepath
        self.input_file_label.config(text=f"Input File: {os.path.basename(filepath)}")

    def _run_validation_checks(self):
        try:
            syield = float(self.vars['SYIELD'].get()); sult = float(self.vars['SULT'].get())
            if syield > sult:
                if not messagebox.askokcancel("Validation Warning", "Yield Stress (SYIELD) is greater than Ultimate Strength (SULT). This is unusual. Do you want to proceed?"):
                    return False
            
            ci = float(self.vars['CI'].get()); cf = float(self.vars['CF'].get())
            cn = float(self.vars['CN'].get()); rad = float(self.vars['RAD'].get())
            ntyp_str = self.vars['NTYP_DESC'].get(); ntyp = int(self.ntyp_map[ntyp_str])

            if cf <= ci: messagebox.showerror("Validation Error", "Final crack length (CF) must be greater than initial crack length (CI)."); return False
            if cn > ci: messagebox.showerror("Validation Error", "Notch length (CN) cannot be greater than initial crack length (CI)."); return False
            if ntyp < 0 and rad > 0 and ci <= rad: messagebox.showerror("Validation Error", "For cracks at a hole (NTYP < 0), initial crack length (CI) must be greater than the hole radius (RAD)."); return False

        except (ValueError, KeyError) as e:
            messagebox.showerror("Validation Error", f"Invalid numeric value or selection in input fields: {e}")
            return False
            
        return True

    def _save_and_generate(self):
        if not self.input_filepath: self._set_input_file()
        if not self.input_filepath: return 
        if not self._run_validation_checks(): return

        current_values = {key: var.get() for key, var in self.vars.items()}
        current_table_data = [[row[0].get(), row[1].get()] for row in self.table_widgets]
        
        # Pass all maps to the generation function
        maps_to_pass = {f"{name}_map": getattr(self, f"{name}_map") for name in 
                        ['nalp', 'nep', 'neqn', 'ntyp', 'ltyp', 'nfopt', 'irate', 'ngc', 
                         'nodkl', 'ndkth', 'ndke', 'lfast', 'kconst', 'ntcmax', 'kth']}
        
        success = generate_fastran_file(current_values, current_table_data, self.input_filepath, maps_to_pass)
        if success:
            messagebox.showinfo("Success", "FASTRAN file successfully created!")
            self.destroy()

    def _on_spectrum_created(self, filename):
        if filename:
            nfopt_code = self.nfopt_map.get(self.vars['NFOPT_DESC'].get(), '0')
            if nfopt_code in ['5', '8', '9', '10']:
                 self.vars['SPECTRA'].set(filename)

    def _show_help(self):
        if self.help_window is None or not self.help_window.winfo_exists():
            self.help_window = HelpWindow(self)
        else:
            self.help_window.focus()

if __name__ == "__main__":
    app = FastranGui()
    app.mainloop()