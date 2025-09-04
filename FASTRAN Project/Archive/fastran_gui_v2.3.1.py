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
  - For all other loading options, you can use a cstamp filename (e.g., cstamp.txt).

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

  Output Options
  These parameters control how frequently the results are printed to the output file. There are two main methods: printing by analysis step (NPRT) or printing by a physical crack increment (DCPR).

  NPRT (Print by Step Interval)
  - If NPRT > 0: The program will print a line of results every NPRT-th analysis increment.
  - If NPRT = 0: The program switches to printing based on the crack length, using the DCPR value below. This is the recommended mode for smooth real-time plotting.

  DCPR (Print by Crack Increment)
  - Defines the specific crack length increment (e.g., 0.01) at which results are printed.
  - This is only active when NPRT is set to 0.

  Detailed Internal Log (For Debugging)
  These parameters control an optional, highly detailed log for advanced analysis and debugging. For most runs, these can be ignored.

  NIPT (Internal Log Activation)
  - If NIPT > 0: Enables the detailed log, which prints internal data like plastic zone size and contact stresses.
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

class ProgressWindow(tk.Toplevel):
    """A simple loading screen with an indeterminate progress bar."""
    def __init__(self, parent, title="Processing...", message="Please wait..."):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x100")
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None) # Prevent user from closing

        ttk.Label(self, text=message, padding=(20, 10)).pack()
        self.progress = ttk.Progressbar(self, mode='indeterminate', length=260)
        self.progress.pack(pady=10)
        
        self.update_idletasks()
        # Center the window
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def start(self):
        self.progress.start(10)

    def stop(self):
        self.progress.stop()
        self.destroy()

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
            return None, None, None

        data = {}; line_idx = 0
        table_data = []
        block_data = [] 

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
        if 0 <= nfopt_val <= 10 and line_idx < len(lines) and "HALT" not in lines[line_idx].upper():
            vals = get_vals(line_idx)
            keys = ['MAXSEQ', 'MAXBLK', 'LPRINT', 'MAXLPR']
            data.update(zip(keys, vals))
            if nfopt_val == 8:
                if len(vals) > 4: data['NREP'] = vals[4]
                if len(vals) > 5: data['MARKER'] = vals[5]
            line_idx += 1
            
            if nfopt_val == 0:
                # Correctly parse SCALE for constant-amplitude loading
                if line_idx < len(lines):
                    data['SCALE'] = get_vals(line_idx)[0]
                    line_idx += 1

                line_idx += 1 # Skip over the "1 1 1" line for block header
                
                if line_idx < len(lines):
                    keys = ['SMAXP', 'SMINP', 'NCYCP']
                    vals = get_vals(line_idx)
                    data.update(zip(keys, vals))
                    line_idx += 1
            
            elif nfopt_val == 1:
                # This logic remains the same
                if line_idx < len(lines):
                    data['SCALE'] = get_vals(line_idx)[0]
                    line_idx += 1 

                while line_idx < len(lines) and "HALT" not in lines[line_idx].upper():
                    try:
                        header_vals = get_vals(line_idx)
                        if len(header_vals) < 2: break 

                        if len(header_vals) >= 3:
                            data['NBLK'] = header_vals[0]
                            nsl = int(header_vals[1])
                            nsq = int(header_vals[2])
                        else: 
                            nsl = int(header_vals[0])
                            nsq = int(header_vals[1])
                    except (ValueError, IndexError):
                        break 
                    
                    line_idx += 1 

                    current_block_levels = []
                    for _ in range(nsl):
                        if line_idx >= len(lines) or "HALT" in lines[line_idx].upper(): break
                        level_vals = get_vals(line_idx)
                        current_block_levels.append(level_vals)
                        line_idx += 1 
                    
                    if current_block_levels:
                        block_data.append({'nsq': str(nsq), 'levels': current_block_levels})
                    
                    if len(header_vals) >= 3:
                        break

            elif nfopt_val in [2,3]: 
                if line_idx < len(lines): data['SMEAN'] = get_vals(line_idx)[0]; line_idx+=1
            elif nfopt_val == 6: 
                if line_idx < len(lines): vals = get_vals(line_idx); data['SPEAK'], data['SMEAN'] = vals; line_idx+=1
            elif nfopt_val in [4,5,7,8,9,10]: 
                if line_idx < len(lines): data['SPEAK'] = get_vals(line_idx)[0]; line_idx+=1

        if line_idx < len(lines) and "HALT" not in lines[line_idx].upper():
            keys = ['KTH', 'SMAXTH', 'RTH', 'CONST', 'PRT']
            vals = get_vals(line_idx)
            data.update(zip(keys, vals))

        messagebox.showinfo("Success", "Successfully loaded the input file.")
        return data, table_data, block_data
    except Exception as e:
        messagebox.showerror("Parsing Error", f"Failed to load the input file.\n{e}")
        return None, None, None

def generate_fastran_file(values, table_data, block_data, save_path, maps):
    try:
        # This entire first section converting descriptions to codes remains the same
        values['NALP'] = maps['nalp_map'][values['NALP_DESC']]
        values['NEP'] = maps['nep_map'][values['NEP_DESC']]
        values['NEQN'] = maps['neqn_map'][values['NEQN_DESC']]
        values['NTYP'] = maps['ntyp_map'][values['NTYP_DESC']]
        values['LTYP'] = maps['ltyp_map'][values['LTYP_DESC']]
        values['NFOPT'] = maps['nfopt_map'][values['NFOPT_DESC']]
        values['IRATE'] = maps['irate_map'][values['IRATE_DESC']]
        values['NGC'] = maps['ngc_map'][values['NGC_DESC']]
        values['NODKL'] = maps['nodkl_map'][values['NODKL_DESC']]
        values['NDKTH'] = maps['ndkth_map'][values['NDKTH_DESC']]
        values['NDKE'] = maps['ndke_map'][values['NDKE_DESC']]
        values['LFAST'] = maps['lfast_map'][values['LFAST_DESC']]
        values['KCONST'] = maps['kconst_map'][values['KCONST_DESC']]
        values['NTCMAX'] = maps['ntcmax_map'][values['NTCMAX_DESC']]
        values['KTH'] = maps['kth_map'][values['KTH_DESC']]     
        
        problem_title = os.path.basename(save_path)
        
        output_lines = [
            f"{problem_title}", f"{values['SPECTRA']}", f" {values['MAT']}",
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
            f"   {int(values['NIPT']):>3d}   {int(values['NPRT']):>3d}    {int(values['LSTEP']):>3d}    {int(values['NDKE']):>3d}   {float(values['DCPR']):.5f}",
            f"   {int(values['NTYP']):>3d}    {int(values['LTYP']):>3d}    {int(values['LFAST']):>3d}    {int(values['NS']):>3d}     {int(values['NFOPT']):>3d}    {int(values['INVERT']):>3d}    {int(values['KCONST']):>3d}    {int(values['NTCMAX']):>3d}",
            f" {float(values['W']):.4f}  {float(values['T']):.4f}  {float(values['CI']):.4f}  {float(values['AI']):.4f}  {float(values['CN']):.4f}  {float(values['AN']):.4f}  {float(values['HN']):.4f}   {float(values['RAD']):.4f}   {float(values['RADF']):.4f}",
            f" {float(values['CF']):.4f}",
        ])
        ntyp_code = values['NTYP']; ltyp_code = values['LTYP']
        if ntyp_code == '5': output_lines.append(f" {float(values['RADIUS'])}")
        elif ntyp_code in ['-12', '-13']:
            lap_joint_line = f" {float(values['RIVETS'])} {float(values['RLF1'])} {float(values['RLF2'])} {int(values['NODKL'])} {float(values['GAMMA'])} {float(values['DELTA'])}"
            output_lines.append(lap_joint_line)
        elif (ntyp_code in ['0', '7'] and ltyp_code == '2') or ntyp_code == '-10':
            output_lines.append(f" {float(values['GAMMA'])}")
        output_lines.extend([
            f"   {float(values['SMAX']):.1f}       {float(values['SMIN']):.1f}",
            f" {int(values['NRC'])}   {float(values['DVALUE'])}    {int(values['NCYCLE1'])}    {int(values['NCYCLE2'])}"
        ])
        
        # --- START OF FORMATTING CORRECTION ---
        nfopt_val = int(values.get('NFOPT', '0'))
        if 0 <= nfopt_val <= 10:
            maxseq = int(values.get('MAXSEQ', '0'))
            maxblk = int(values.get('MAXBLK', '0'))
            lprint = int(values.get('LPRINT', '0'))
            maxlpr = int(values.get('MAXLPR', '0'))

            loading_line = f" {maxseq:1d}   {maxblk:1d}   {lprint:1d}   {maxlpr:1d}"

            if nfopt_val == 8:
                nrep = int(values.get('NREP', '0'))
                marker = int(values.get('MARKER', '0'))
                loading_line += f"   {nrep:3d}   {marker:3d}"
            output_lines.append(loading_line)

            
            if nfopt_val == 0:
                output_lines.append(f"{float(values.get('SCALE', '1.0')):.1f}")
                if not block_data:
                    output_lines.append(" 1   1   1") 
                    output_lines.append("  0.0    0.00            1") 
                else:
                    # Enumerate through the blocks to get a consecutive index for NBLK
                    for i, block in enumerate(block_data):
                        levels = block.get('levels', [])
                        nsl = len(levels)
                        nsq = int(block.get('nsq', '1'))
                        
                        # NBLK is the consecutive block number, starting from 1.
                        nblk = i + 1
                        
                        # Write the header using the correct, consecutive NBLK value.
                        output_lines.append(f" {nblk:1d}   {nsl:1d}   {nsq:1d}")

                        for level in levels:
                            smax_val = float(level[0])
                            smin_val = float(level[1])
                            ncyc_val = int(level[2])
                            output_lines.append(f" {smax_val:4.1f}   {smin_val:4.2f} {ncyc_val:14d}")

            elif nfopt_val == 1:
                output_lines.append(f"{float(values.get('SCALE', '1.0')):.1f}")
                if not block_data:
                    output_lines.append(" 1   1   1") 
                    output_lines.append("  0.0    0.00            1") 
                else:
                    # Enumerate through the blocks to get a consecutive index for NBLK
                    for i, block in enumerate(block_data):
                        levels = block.get('levels', [])
                        nsl = len(levels)
                        nsq = int(block.get('nsq', '1'))
                        
                        # NBLK is the consecutive block number, starting from 1.
                        nblk = i + 1
                        
                        # Write the header using the correct, consecutive NBLK value.
                        output_lines.append(f" {nblk:1d}   {nsl:1d}   {nsq:1d}")

                        for level in levels:
                            smax_val = float(level[0])
                            smin_val = float(level[1])
                            ncyc_val = int(level[2])
                            output_lines.append(f" {smax_val:4.1f}   {smin_val:4.2f} {ncyc_val:14d}")

            # Fallback for other NFOPT options
            elif nfopt_val == 6: 
                output_lines.append(f"    {float(values['SPEAK']):.1f}  {float(values['SMEAN']):.1f}")
            elif nfopt_val in [2,3]: 
                output_lines.append(f"    {float(values['SMEAN']):.1f}")
            elif nfopt_val in [4,5,7,8,9,10]: 
                output_lines.append(f"    {float(values['SPEAK']):.1f}")
        
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
    def __init__(self, parent, callback, load_from_file=None, default_dir=None):
        super().__init__(parent)
        self.title("Spectrum Editor")
        self.geometry("750x650")
        self.callback = callback
        self.output_filepath = None
        self.default_dir = default_dir # Store the default directory path
        
        self.levels_data = [] 
        self.level_widgets = []
        self.num_levels_var = tk.IntVar(value=0)
        self.speak_var = tk.StringVar(value="1.0")
        self.invert_var = tk.StringVar(value="0")

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
        # --- Menubar ---
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        edit_menu = tk.Menu(menubar, tearoff=0)

        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        file_menu.add_command(label="Import...", command=self._import_spectrum)
        file_menu.add_command(label="Save", command=self._save_file)
        file_menu.add_command(label="Save & Close", command=self._generate_and_close)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.destroy)

        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self._undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self._redo)

        # --- Top Control Frame ---
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill='x', padx=10, pady=5)
        top_frame.columnconfigure(4, weight=1)
        
        # --- Top Control Frame ---
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill='x', padx=10, pady=5)
        top_frame.columnconfigure(4, weight=1)

        ttk.Label(top_frame, text="Spectrum Title:").grid(row=0, column=0, sticky='w', pady=2)
        self.title_entry = ttk.Entry(top_frame)
        self.title_entry.insert(0, "Custom Spectrum")
        self.title_entry.grid(row=0, column=1, columnspan=5, sticky='ew', padx=5)
        
        ttk.Label(top_frame, text="INVERT:").grid(row=1, column=0, sticky='w', pady=(5,2))
        self.invert_entry = ttk.Entry(top_frame, width=10, textvariable=self.invert_var)
        self.invert_entry.grid(row=1, column=1, sticky='w', padx=5)
        ToolTip(self.invert_entry, "0 for Smax,Smin pairs. 1 for Smin,Smax pairs.")

        speak_lbl = ttk.Label(top_frame, text="SPEAK:")
        speak_lbl.grid(row=1, column=2, sticky='w', padx=5, pady=(5,2))
        speak_entry = ttk.Entry(top_frame, textvariable=self.speak_var, width=10)
        speak_entry.grid(row=1, column=3, sticky='w', padx=5)
        ToolTip(speak_lbl, "Peak Stress (SPEAK).\nThis value is written to the file header and\ncan be used as a multiplier for normalized stress levels.")
        ToolTip(speak_entry, "Peak Stress (SPEAK).\nThis value is written to the file header and\ncan be used as a multiplier for normalized stress levels.")
        
        ttk.Button(top_frame, text="Save & Close", command=self._generate_and_close).grid(row=0, column=6, sticky='ne', padx=5)

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
        ttk.Button(level_ctrl_frame, text="Normalize", command=self._normalize_spectrum).pack(side='left', padx=5)
        ttk.Button(level_ctrl_frame, text="Update Plot", command=self._update_plot).pack(side='left', padx=5)
        self.undo_button = ttk.Button(level_ctrl_frame, text="Undo", command=self._undo, state="disabled")
        self.undo_button.pack(side='left', padx=(10, 0))
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
        plot_container = ttk.LabelFrame(paned_window, text="Spectrum Plot", padding="10")
        paned_window.add(plot_container, weight=1)
        fig = Figure(dpi=100)
        fig.set_tight_layout(True)
        self.ax = fig.add_subplot(111)
        self.plot_canvas = FigureCanvasTkAgg(fig, master=plot_container)
        self.plot_canvas.get_tk_widget().pack(fill='both', expand=True)
        plot_container.bind("<Configure>", lambda event: self.plot_canvas.draw_idle())
        self._update_plot()

    def _save_file(self):
        """Saves the spectrum file but keeps the editor open."""
        if not self.output_filepath:
            messagebox.showerror("Error", "Please set a save location for the spectrum file first.", parent=self)
            return False

        try:
            # The generation logic is the same as before
            try: speak = float(self.speak_var.get())
            except (ValueError, tk.TclError): speak = 1.0
            title = self.title_entry.get()
            invert = int(self.invert_var.get())
            levels = []
            total_cycles = 0
            overall_smax = -float('inf')
            overall_smin = float('inf')
            self._sync_data_from_widgets()
            for level_data in self.levels_data:
                smax = float(level_data[0]) * speak
                smin = float(level_data[1]) * speak
                cycles = int(level_data[2])
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
                
                # The 5th parameter is hard-coded to 3 in order to get it to run.
                f.write(f" {total_points}    {smax_header}    {smin_header}    {invert}    3\n")

                col_width = 8
                cols_per_line = 10
                line_str = ""
                current_col = 0
                for level in levels:
                    for _ in range(level['cycles']):
                        smax_int = int(round(level['smax']))
                        smin_int = int(round(level['smin']))
                        line_str += f"{smax_int:{col_width}d}"
                        current_col += 1
                        if current_col >= cols_per_line:
                            f.write(line_str + "\n"); line_str = ""; current_col = 0
                        line_str += f"{smin_int:{col_width}d}"
                        current_col += 1
                        if current_col >= cols_per_line:
                            f.write(line_str + "\n"); line_str = ""; current_col = 0
                if line_str: f.write(line_str + "\n")

            messagebox.showinfo("Success", "Spectrum file successfully saved!", parent=self)
            self.callback(os.path.basename(self.output_filepath))
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Could not generate spectrum file:\n{e}", parent=self)
            return False
        
    def _generate_and_close(self):
        """Saves the file and then closes the editor window."""
        if self._save_file():
            self.destroy()

    def _normalize_spectrum(self):
        """Normalizes all stress levels by the maximum absolute stress."""
        self._save_state_for_undo()
        self._sync_data_from_widgets()
        
        max_abs_stress = 0.0
        for level_data in self.levels_data:
            try:
                smax = float(level_data[0])
                smin = float(level_data[1])
                max_abs_stress = max(max_abs_stress, abs(smax), abs(smin))
            except ValueError:
                continue # Skip non-numeric values
        
        if max_abs_stress == 0:
            messagebox.showinfo("Normalize", "Cannot normalize, maximum stress is zero.", parent=self)
            return

        for i, level_data in enumerate(self.levels_data):
            try:
                smax = float(level_data[0])
                smin = float(level_data[1])
                self.levels_data[i][0] = f"{smax / max_abs_stress:.4g}"
                self.levels_data[i][1] = f"{smin / max_abs_stress:.4g}"
            except ValueError:
                continue
        
        self.speak_var.set(f"{max_abs_stress:.4g}")
        self._redraw_levels_table()
        self._update_plot()

    def _update_levels_from_spinbox(self):
        """Adds or removes rows from the table data based on the spinbox value."""
        self._save_state_for_undo()
        try:
            new_size = self.num_levels_var.get()
            if new_size < 0: return

            # Get current values before changing size
            self._sync_data_from_widgets()
            
            # Add new rows if necessary
            while len(self.levels_data) < new_size:
                self.levels_data.append(['0.0', '0.0', '1'])
            
            # Remove rows if necessary
            if len(self.levels_data) > new_size:
                self.levels_data = self.levels_data[:new_size]
            
            self._redraw_levels_table()
        except tk.TclError:
            # Handles case where spinbox is empty temporarily
            pass

    def _update_plot(self):
        """Reads data from the table, applies the multiplier, and redraws the plot."""
        try:
            multiplier = float(self.speak_var.get())
        except (ValueError, tk.TclError):
            multiplier = 1.0

        plot_x = [0]
        plot_y = [0]
        cumulative_cycles = 0

        self._sync_data_from_widgets() # Make sure we're plotting the latest data

        for level_data in self.levels_data:
            try:
                smax = float(level_data[0]) * multiplier
                smin = float(level_data[1]) * multiplier
                cycles = int(level_data[2])

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
            
            # --- Add editing buttons for each row ---
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

    def _sync_data_from_widgets(self):
        for i, row_widgets in enumerate(self.level_widgets):
            if i < len(self.levels_data):
                self.levels_data[i] = [row_widgets[0].get(), row_widgets[1].get(), row_widgets[2].get()]

    def _save_state_for_undo(self, clear_redo=True):
        self._sync_data_from_widgets()
        self.undo_stack.append(copy.deepcopy(self.levels_data))
        if clear_redo:
            self.redo_stack.clear()
        self._update_undo_redo_buttons()

    def _undo(self, event=None):
        if not self.undo_stack or len(self.undo_stack) <= 1: return
        self.redo_stack.append(copy.deepcopy(self.levels_data))
        self.levels_data = self.undo_stack.pop()
        self._redraw_levels_table()
        self._update_plot()
        self._update_undo_redo_buttons()

    def _redo(self, event=None):
        if not self.redo_stack: return
        self.undo_stack.append(copy.deepcopy(self.levels_data))
        self.levels_data = self.redo_stack.pop()
        self._redraw_levels_table()
        self._update_plot()
        self._update_undo_redo_buttons()

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
        filepath = filedialog.askopenfilename(
            title="Import Spectrum File", parent=self,
            filetypes=(("Spectrum Files", "*.spx *.sub *.txt"), ("All Files", "*.*"))
        )
        if filepath:
            self._load_spectrum_file(filepath, from_import=True)

    def _load_spectrum_file(self, filepath, from_import=False):
        _, extension = os.path.splitext(filepath)
        new_levels_data = None
        parser_used = ""
        try:
            if extension.lower() == '.spx':
                new_levels_data = self._parse_spx(filepath)
                parser_used = ".spx"
            elif extension.lower() in ['.sub', '.txt']:
                with open(filepath, 'r') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                if not lines: raise ValueError("File is empty")

                # --- CORRECTED DISPATCH LOGIC ---
                # First, specifically check for a standard FASTRAN (NFOPT=8) txt file.
                # Its signature is a header on line 2 with 5 numeric values.
                is_standard_fastran_txt = False
                if len(lines) > 1:
                    header_parts = lines[1].split()
                    if len(header_parts) == 5:
                        try:
                            # Confirm all 5 parts are numbers
                            for part in header_parts: float(part)
                            is_standard_fastran_txt = True
                        except ValueError:
                            is_standard_fastran_txt = False # It had 5 columns, but not all were numeric.

                if is_standard_fastran_txt:
                    new_levels_data = self._parse_spectrum_txt(filepath)
                    parser_used = "Standard FASTRAN .txt"
                else:
                    # If not a standard FASTRAN file, check for other text formats like .sub or reversal.
                    if len(lines) <= 1: # File has a title but no data
                        raise ValueError("File contains only a title line or is empty.")
                    
                    num_cols_first_data_line = len(lines[1].split())

                    if num_cols_first_data_line >= 3:
                        new_levels_data = self._parse_sub(filepath)
                        parser_used = ".sub (3-Column Text)"
                    elif num_cols_first_data_line == 1:
                        # This case was in your original code but the function was missing.
                        # I have provided an implementation for it in the next step.
                        new_levels_data = self._parse_reversal_txt(filepath)
                        parser_used = "Reversal .txt (1-Column)"
                    else:
                        # Fallback for any other format, like a simple 2-column Smax/Smin list
                        messagebox.showwarning("Parsing Warning", "Unrecognized text format. Attempting to parse as a raw list of stress pairs.", parent=self)
                        new_levels_data = self._parse_spectrum_txt(filepath)
                        parser_used = "Paired .txt"

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
        
        if not from_import:
            root, ext = os.path.splitext(filepath)
            if ext.lower() == '.txt':
                target_filename = os.path.basename(filepath)
            else:
                target_filename = os.path.basename(root) + '.txt'

            if self.default_dir:
                self.output_filepath = os.path.join(self.default_dir, target_filename)
                self.output_label.config(text=f"Default Save: {target_filename} (in input file directory)")
            else: 
                self.output_filepath = os.path.join(os.path.dirname(filepath), target_filename)
                self.output_label.config(text=f"Default Save: {target_filename}")
            
    def _set_output_file(self):
        filepath = filedialog.asksaveasfilename(
            title="Set Spectrum File Location",
            initialdir=self.default_dir, # This makes the dialog open in the correct directory
            defaultextension=".txt",
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        if filepath:
            self.output_filepath = filepath
            self.output_label.config(text=f"File: {os.path.basename(filepath)}")

    def _parse_reversal_txt(self, filepath):
        """Parses a 1-column reversal-point text file."""
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        self.title_entry.delete(0, tk.END); self.title_entry.insert(0, lines[0].strip())
        self.speak_var.set("1.0")
        self.invert_var.set("0")

        # Read all numbers from the file into a single list
        points = [float(p) for line in lines[1:] for p in line.split()]
        
        if len(points) < 2:
            return []

        # Create pairs from the reversal points (e.g., S1-S2, S2-S3, S3-S4...)
        stress_pairs = []
        for i in range(len(points) - 1):
            s1 = points[i]
            s2 = points[i+1]
            # Conventionally store as (max, min)
            stress_pairs.append([max(s1, s2), min(s1, s2)])

        if not stress_pairs:
            return []

        # Count occurrences of each unique pair
        levels = []
        pair_counts = {}
        for pair in stress_pairs:
            pair_tuple = tuple(pair)
            pair_counts[pair_tuple] = pair_counts.get(pair_tuple, 0) + 1
        
        for pair, count in pair_counts.items():
            levels.append([f"{pair[0]:.4g}", f"{pair[1]:.4g}", str(count)])
            
        return levels

    def _parse_spectrum_txt(self, filepath):
        """
        Parses a standard FASTRAN (NFOPT=8) paired-point .txt file,
        preserving the order of consecutive cycle blocks.
        """
        with open(filepath, 'r') as f:
            lines = f.readlines()
        if len(lines) < 2: return None

        self.title_entry.delete(0, tk.END); self.title_entry.insert(0, lines[0].strip())
        header_parts = lines[1].strip().split()
        if len(header_parts) >= 5:
            self.invert_var.set(header_parts[3])
            self.speak_var.set("1.0")

        all_points_float = []
        body_text = "".join(line.strip('\n\r') for line in lines[2:])
        try:
            # Try parsing as fixed-width first (common 10I8 format)
            all_points_float = [float(body_text[i:i+8]) for i in range(0, len(body_text), 8) if body_text[i:i+8].strip()]
        except (ValueError, IndexError):
            # Fallback to space-delimited parsing if fixed-width fails
            all_points_float = [float(p) for p in body_text.split()]

        if not all_points_float: return []
        if len(all_points_float) % 2 != 0: all_points_float.pop()

        stress_pairs = [[all_points_float[i], all_points_float[i+1]] for i in range(0, len(all_points_float), 2)]
        
        # --- GROUP ONLY CONSECUTIVE CYCLES ---
        levels = []
        if not stress_pairs:
            return []

        # Start with the first pair to initialize the first block
        current_smax = stress_pairs[0][0]
        current_smin = stress_pairs[0][1]
        current_count = 1

        # Iterate from the second pair to the end of the sequence
        for i in range(1, len(stress_pairs)):
            next_smax, next_smin = stress_pairs[i]

            # Check if the next pair is identical to the current block's pair
            # NOTE: Using a small tolerance for floating point comparison is robust
            if abs(next_smax - current_smax) < 1e-9 and abs(next_smin - current_smin) < 1e-9:
                # If it's the same, just increment the cycle count for the current block
                current_count += 1
            else:
                # If the pair is different, the consecutive block has ended.
                # Finalize the current block and add it to the list of levels.
                levels.append([f"{current_smax:.4g}", f"{current_smin:.4g}", str(current_count)])
                
                # Start a new block using the new pair's data
                current_smax = next_smax
                current_smin = next_smin
                current_count = 1
        
        # The loop finishes on the last block, so we need to add it to the list
        levels.append([f"{current_smax:.4g}", f"{current_smin:.4g}", str(current_count)])

        return levels
    
    def _parse_spx(self, filepath):
        """Parses an XML-based .spx spectrum file."""
        tree = ET.parse(filepath)
        root = tree.getroot()
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, root.findtext('Title', ''))
        
        # In .spx, SMAX/SMIN are not normalized by SPEAK, so SPEAK is set to 1.0
        self.speak_var.set("1.0") 
        self.invert_var.set("0") # .spx files are max/min format

        levels = []
        # Find the first SubSpectrum and extract its levels
        subspectrum = root.find('.//SubSpectrum')
        if subspectrum is not None:
            for level in subspectrum.findall('B'):
                smax = level.get('Mx', '0.0')
                smin = level.get('Mn', '0.0')
                cycles = level.get('C', '1')
                levels.append([smax, smin, cycles])
        return levels

    def _parse_sub(self, filepath):
        """Parses a text-based .sub file (SMAX, SMIN, Cycles)."""
        with open(filepath, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        self.title_entry.delete(0, tk.END); self.title_entry.insert(0, lines[0].strip())
        self.speak_var.set("1.0")
        self.invert_var.set("0")

        # Data starts on the second line
        stress_lines = lines[1:]
        
        levels = []
        for line in stress_lines:
            parts = line.split()
            if len(parts) >= 3:
                smax, smin, cycles = parts[0], parts[1], parts[2]
                levels.append([smax, smin, cycles])
        return levels
    
    def _generate_spectrum(self):
        if not self.output_filepath:
            messagebox.showerror("Error", "Please set a save location for the spectrum file first.", parent=self)
            return

        try:
            try:
                speak = float(self.speak_var.get())
            except (ValueError, tk.TclError):
                speak = 1.0

            title = self.title_entry.get()
            invert = int(self.invert_var.get())

            levels = []
            total_cycles = 0
            overall_smax = -float('inf')
            overall_smin = float('inf')
            
            self._sync_data_from_widgets()

            for level_data in self.levels_data:
                # Apply the SPEAK multiplier to the stress values from the table
                smax = float(level_data[0]) * speak
                smin = float(level_data[1]) * speak
                cycles = int(level_data[2])
                
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
                # The 5th value in the header is now the SPEAK value
                speak_header = int(round(speak))
                f.write(f" {total_points}    {smax_header}    {smin_header}    {invert}    {speak_header}\n")

                # The format is now (10I8 format)
                col_width = 8
                cols_per_line = 10

                line_str = ""
                current_col = 0
                for level in levels:
                    for _ in range(level['cycles']):
                        smax_int = int(round(level['smax']))
                        smin_int = int(round(level['smin']))
                        
                        line_str += f"{smax_int:{col_width}d}"
                        current_col += 1
                        if current_col >= cols_per_line:
                            f.write(line_str + "\n"); line_str = ""; current_col = 0

                        line_str += f"{smin_int:{col_width}d}"
                        current_col += 1
                        if current_col >= cols_per_line:
                            f.write(line_str + "\n"); line_str = ""; current_col = 0

                if line_str:
                    f.write(line_str + "\n")

            messagebox.showinfo("Success", "Spectrum file successfully updated/created!", parent=self)
            self.callback(os.path.basename(self.output_filepath))
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Could not generate spectrum file:\n{e}", parent=self)

class PostProcessingWindow(tk.Toplevel):
    """A dedicated window for plotting and exporting results from an output file."""
    def __init__(self, parent, header, data):
        super().__init__(parent)
        self.title("FASTRAN Post-Processor")
        self.geometry("800x550")

        self.header = header
        self.data = data
        
        # Plotting control variables
        self.x_axis_var = tk.StringVar()
        self.y_axis_var = tk.StringVar()
        self.log_x_var = tk.BooleanVar(value=False)
        self.log_y_var = tk.BooleanVar(value=False)

        self._create_widgets()
        self._populate_controls()

        self.transient(parent)
        self.grab_set()

    def _create_widgets(self):
        # --- Menu ---
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Results As CSV...", command=self._save_parsed_results)
        file_menu.add_command(label="Export Plot...", command=self._export_plot)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.destroy)

        # --- Plot Controls ---
        plot_ctrl_frame = ttk.Frame(self, padding=5)
        plot_ctrl_frame.pack(fill='x', pady=5)
        
        ttk.Label(plot_ctrl_frame, text="Y-Axis:").pack(side='left', padx=(0,5))
        self.y_axis_combo = ttk.Combobox(plot_ctrl_frame, textvariable=self.y_axis_var, state='readonly', width=15)
        self.y_axis_combo.pack(side='left')
        self.y_axis_combo.bind("<<ComboboxSelected>>", self._draw_custom_plot)
        ttk.Checkbutton(plot_ctrl_frame, text="log", variable=self.log_y_var, command=self._draw_custom_plot).pack(side='left', padx=5)
        
        ttk.Label(plot_ctrl_frame, text="X-Axis:").pack(side='left', padx=(20,5))
        self.x_axis_combo = ttk.Combobox(plot_ctrl_frame, textvariable=self.x_axis_var, state='readonly', width=15)
        self.x_axis_combo.pack(side='left')
        self.x_axis_combo.bind("<<ComboboxSelected>>", self._draw_custom_plot)
        ttk.Checkbutton(plot_ctrl_frame, text="log", variable=self.log_x_var, command=self._draw_custom_plot).pack(side='left', padx=5)

        # --- Plot Canvas ---
        plot_frame = ttk.Frame(self)
        plot_frame.pack(fill='both', expand=True, padx=5, pady=5)
        fig = Figure(dpi=100); fig.set_tight_layout(True)
        self.ax = fig.add_subplot(111)
        self.plot_canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        self.plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _populate_controls(self):
        """Populates the comboboxes with headers and draws the initial plot."""
        self.x_axis_combo.config(values=self.header)
        self.y_axis_combo.config(values=self.header)
        if 'CYCLES' in self.header: self.x_axis_var.set('CYCLES')
        if 'C_crack' in self.header: self.y_axis_var.set('C_crack')
        self._draw_custom_plot()

    def _draw_custom_plot(self, event=None):
        x_var = self.x_axis_var.get(); y_var = self.y_axis_var.get()
        if not x_var or not y_var: return

        try:
            x_index = self.header.index(x_var)
            y_index = self.header.index(y_var)
            x_data = [float(row[x_index]) for row in self.data]
            y_data = [float(row[y_index]) for row in self.data]
            self.ax.clear()
            
            plot_style = {'marker': '.', 'linestyle': ''} if 'DKEC' in x_var or 'DKEA' in x_var else {'marker': '.', 'markersize': 4, 'linestyle': '-'}
            title = f"{y_var} vs. {x_var}"
            
            self.ax.plot(x_data, y_data, **plot_style)
            self.ax.set_xlabel(x_var); self.ax.set_ylabel(y_var)
            self.ax.set_title(title); self.ax.grid(True)
            self.ax.set_xscale('log' if self.log_x_var.get() else 'linear')
            self.ax.set_yscale('log' if self.log_y_var.get() else 'linear')
            self.plot_canvas.draw()
        except (ValueError, IndexError) as e:
            messagebox.showerror("Plotting Error", f"Could not create plot.\nDetails: {e}", parent=self)

    def _export_plot(self):
        filepath = filedialog.asksaveasfilename(
            title="Export Plot As", parent=self,
            filetypes=(("PNG Image", "*.png"),("SVG Vector Image", "*.svg"),("PDF Document", "*.pdf"),("All Files", "*.*")),
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
            defaultextension=".csv", filetypes=(("CSV File", "*.csv"), ("All Files", "*.*"))
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
    
# --- Block Loading Editor Window Class ---
class BlockEditorWindow(tk.Toplevel):
    def __init__(self, parent, callback, initial_data, initial_params):
        super().__init__(parent)
        self.title("Block Loading Editor (NFOPT=1)")
        self.geometry("850x650")
        self.callback = callback
        
        self.blocks = copy.deepcopy(initial_data) if initial_data else [{'nsq': '1', 'levels': [['0.0', '0.0', '1']]}]
        self.current_block_index = 0

        self.param_vars = {
            'MAXSEQ': tk.StringVar(value=initial_params.get('MAXSEQ', str(len(self.blocks)))),
            'MAXBLK': tk.StringVar(value=initial_params.get('MAXBLK', '0')),
            'LPRINT': tk.StringVar(value=initial_params.get('LPRINT', '0')),
            'MAXLPR': tk.StringVar(value=initial_params.get('MAXLPR', '0')),
            'SCALE': tk.StringVar(value=initial_params.get('SCALE', '1.0'))
        }
        self.param_vars['MAXSEQ'].set(str(len(self.blocks)))

        self._create_widgets()
        self._populate_block_listbox()

        self.transient(parent)
        self.grab_set()

    def _create_widgets(self):
        bottom_frame = ttk.Frame(self, padding=10)
        bottom_frame.pack(side="bottom", fill="x")
        ttk.Button(bottom_frame, text="Save & Close", command=self._save_and_close).pack(side="right")
        
        params_lf = ttk.LabelFrame(self, text="Global Loading Parameters (Section 17)", padding=10)
        params_lf.pack(side="top", fill="x", padx=10, pady=5)

        ttk.Label(params_lf, text="MAXSEQ:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        maxseq_entry = ttk.Entry(params_lf, textvariable=self.param_vars['MAXSEQ'], width=10, state='disabled')
        maxseq_entry.grid(row=0, column=1, sticky='w', padx=5)
        ToolTip(maxseq_entry, "Total number of blocks defined below (automatically updated).")

        ttk.Label(params_lf, text="MAXBLK:").grid(row=0, column=2, sticky='w', padx=(20, 5), pady=2)
        maxblk_entry = ttk.Entry(params_lf, textvariable=self.param_vars['MAXBLK'], width=10)
        maxblk_entry.grid(row=0, column=3, sticky='w', padx=5)
        ToolTip(maxblk_entry, "Maximum number of total blocks (or flights) to be run.")
        
        ttk.Label(params_lf, text="SCALE:").grid(row=0, column=4, sticky='w', padx=(20, 5), pady=2)
        scale_entry = ttk.Entry(params_lf, textvariable=self.param_vars['SCALE'], width=10)
        scale_entry.grid(row=0, column=5, sticky='w', padx=5)
        ToolTip(scale_entry, "A scale factor applied to all Smax and Smin values in this sequence.")

        ttk.Label(params_lf, text="LPRINT:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        lprint_entry = ttk.Entry(params_lf, textvariable=self.param_vars['LPRINT'], width=10)
        lprint_entry.grid(row=1, column=1, sticky='w', padx=5)
        ToolTip(lprint_entry, "Print option for variable-amplitude load history (0=no print).")
        
        ttk.Label(params_lf, text="MAXLPR:").grid(row=1, column=2, sticky='w', padx=(20, 5), pady=2)
        maxlpr_entry = ttk.Entry(params_lf, textvariable=self.param_vars['MAXLPR'], width=10)
        maxlpr_entry.grid(row=1, column=3, sticky='w', padx=5)
        ToolTip(maxlpr_entry, "Maximum number of variable-amplitude load levels to be printed.")
        
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(fill='both', expand=True, padx=10, pady=(10,0))

        left_pane = ttk.Frame(paned_window, padding=5)
        paned_window.add(left_pane, weight=1)
        list_frame = ttk.LabelFrame(left_pane, text="Block Sequence")
        list_frame.pack(fill='both', expand=True)
        self.block_listbox = tk.Listbox(list_frame, exportselection=False)
        self.block_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        self.block_listbox.bind('<<ListboxSelect>>', self._on_block_select)
        list_ctrl_frame = ttk.Frame(left_pane)
        list_ctrl_frame.pack(fill='x', pady=5)
        ttk.Button(list_ctrl_frame, text="Add Block", command=self._add_block).pack(side='left', expand=True, fill='x')
        ttk.Button(list_ctrl_frame, text="Delete Block", command=self._delete_block).pack(side='left', expand=True, fill='x', padx=5)
        ttk.Button(list_ctrl_frame, text="Move Up ↑", command=self._move_block_up).pack(side='left', expand=True, fill='x')
        ttk.Button(list_ctrl_frame, text="Move Down ↓", command=self._move_block_down).pack(side='left', expand=True, fill='x', padx=5)

        self.right_pane = ttk.Frame(paned_window, padding=10)
        paned_window.add(self.right_pane, weight=3)

    def _populate_block_listbox(self):
        current_selection_index = self.block_listbox.curselection()[0] if self.block_listbox.curselection() else self.current_block_index
        
        self.block_listbox.delete(0, tk.END)
        for i, block in enumerate(self.blocks):
            nsq = block.get('nsq', 1)
            nsl = len(block.get('levels', []))
            self.block_listbox.insert(tk.END, f"Block {i+1} (NSL={nsl}, Reps={nsq})")
        
        new_index = min(current_selection_index, len(self.blocks) - 1)
        if new_index >= 0:
            self.block_listbox.selection_set(new_index)
            self.block_listbox.activate(new_index)
            self.block_listbox.see(new_index)
        
        self.param_vars['MAXSEQ'].set(str(len(self.blocks)))
        self._on_block_select()

    def _on_block_select(self, event=None):
        if not self.block_listbox.curselection():
             if not self.blocks:
                for widget in self.right_pane.winfo_children(): widget.destroy()
                ttk.Label(self.right_pane, text="No Block Selected").pack()
                return
             else:
                self.block_listbox.selection_set(0)

        new_index = self.block_listbox.curselection()[0]
        self._sync_data_from_widgets()
        self.current_block_index = new_index
        
        for widget in self.right_pane.winfo_children(): widget.destroy()
        
        props_frame = ttk.LabelFrame(self.right_pane, text=f"Block {self.current_block_index + 1} Properties", padding=5)
        props_frame.pack(fill='x', expand=False)
        
        block_data = self.blocks[self.current_block_index]
        self.nsq_var = tk.StringVar(value=block_data.get('nsq', '1'))
        
        ttk.Label(props_frame, text="Block Repetitions (NSQ):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        nsq_entry = ttk.Entry(props_frame, textvariable=self.nsq_var, width=10)
        nsq_entry.grid(row=0, column=1, sticky='w', padx=5)
        ToolTip(nsq_entry, "Number of times this entire block of stress levels is repeated.")
        
        self.nsl_label = ttk.Label(props_frame, text="")
        self.nsl_label.grid(row=0, column=2, sticky='w', padx=20)
        
        levels_frame = ttk.LabelFrame(self.right_pane, text="Stress Levels in Block", padding=5)
        levels_frame.pack(fill='both', expand=True, pady=5)
        
        level_ctrl_frame = ttk.Frame(levels_frame)
        level_ctrl_frame.pack(fill='x', pady=(0, 5))
        ttk.Button(level_ctrl_frame, text="Add Level", command=self._add_block_level).pack(side='left')
        
        canvas = tk.Canvas(levels_frame, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(levels_frame, orient="vertical", command=canvas.yview)
        self.table_frame = ttk.Frame(canvas, padding="5")
        self.table_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self._redraw_block_levels_table()

    def _update_nsl_display(self):
        """Updates the NSL label with the current number of levels."""
        if hasattr(self, 'nsl_label') and self.blocks:
            nsl_count = len(self.blocks[self.current_block_index]['levels'])
            self.nsl_label.config(text=f"Number of Levels (NSL): {nsl_count}")

    def _redraw_block_levels_table(self):
        for widget in self.table_frame.winfo_children(): widget.destroy()
        self.level_widgets = []
        
        if not self.blocks: return
        block_levels = self.blocks[self.current_block_index]['levels']
        
        ttk.Label(self.table_frame, text="Max Stress", font="-weight bold").grid(row=0, column=0, padx=5, pady=2)
        ttk.Label(self.table_frame, text="Min Stress", font="-weight bold").grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(self.table_frame, text="Cycles", font="-weight bold").grid(row=0, column=2, padx=5, pady=2)
        ttk.Label(self.table_frame, text="Actions", font="-weight bold").grid(row=0, column=3, columnspan=3, padx=5, pady=2)

        for i, data_row in enumerate(block_levels):
            smax, smin, cycles = data_row
            smax_entry = ttk.Entry(self.table_frame, width=15); smax_entry.insert(0, smax); smax_entry.grid(row=i + 1, column=0, padx=5, pady=2)
            smin_entry = ttk.Entry(self.table_frame, width=15); smin_entry.insert(0, smin); smin_entry.grid(row=i + 1, column=1, padx=5, pady=2)
            cycles_entry = ttk.Entry(self.table_frame, width=10); cycles_entry.insert(0, cycles); cycles_entry.grid(row=i + 1, column=2, padx=5, pady=2)
            
            up_btn = ttk.Button(self.table_frame, text="↑", width=3, command=lambda i=i: self._move_block_level(i, -1))
            up_btn.grid(row=i + 1, column=3, padx=(10, 2))
            down_btn = ttk.Button(self.table_frame, text="↓", width=3, command=lambda i=i: self._move_block_level(i, 1))
            down_btn.grid(row=i + 1, column=4, padx=2)
            del_btn = ttk.Button(self.table_frame, text="Delete", width=8, command=lambda i=i: self._delete_block_level(i))
            del_btn.grid(row=i + 1, column=5, padx=2)
            
            if i == 0: up_btn.config(state="disabled")
            if i == len(block_levels) - 1: down_btn.config(state="disabled")

            self.level_widgets.append([smax_entry, smin_entry, cycles_entry])
        
        self._update_nsl_display()

    def _sync_data_from_widgets(self):
        if not hasattr(self, 'nsq_var') or not self.blocks: return
        block_data = self.blocks[self.current_block_index]
        block_data['nsq'] = self.nsq_var.get()
        new_levels = []
        for row_widgets in self.level_widgets:
            new_levels.append([w.get() for w in row_widgets])
        block_data['levels'] = new_levels
        
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
        new_index = index + direction
        if not (0 <= new_index < len(levels)): return
        levels[index], levels[new_index] = levels[new_index], levels[index]
        self._redraw_block_levels_table()

    def _add_block(self):
        self._sync_data_from_widgets()
        self.blocks.append({'nsq': '1', 'levels': [['0.0', '0.0', '1']]})
        self._populate_block_listbox()
        self.block_listbox.selection_set(tk.END)

    def _delete_block(self):
        if not self.block_listbox.curselection() or not self.blocks: return
        if len(self.blocks) <= 1:
            messagebox.showwarning("Warning", "Must have at least one block.", parent=self)
            return
        index = self.block_listbox.curselection()[0]
        self.blocks.pop(index)
        self.current_block_index = 0
        self._populate_block_listbox()

    def _move_block_up(self):
        if not self.block_listbox.curselection(): return
        index = self.block_listbox.curselection()[0]
        if index == 0: return
        self._sync_data_from_widgets()
        self.blocks[index], self.blocks[index-1] = self.blocks[index-1], self.blocks[index]
        self._populate_block_listbox()
        self.block_listbox.selection_set(index - 1)

    def _move_block_down(self):
        if not self.block_listbox.curselection(): return
        index = self.block_listbox.curselection()[0]
        if index >= len(self.blocks) - 1: return
        self._sync_data_from_widgets()
        self.blocks[index], self.blocks[index+1] = self.blocks[index+1], self.blocks[index]
        self._populate_block_listbox()
        self.block_listbox.selection_set(index + 1)

    def _save_and_close(self):
        self._sync_data_from_widgets()
        if self.callback:
            final_data = {
                'params': {key: var.get() for key, var in self.param_vars.items()},
                'blocks': self.blocks
            }
            self.callback(final_data)
        self.destroy()
        
class DkeffWindow(tk.Toplevel):
    """
    A Toplevel window for generating dKeff data by running dkeff13.exe.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Material Data Generator (dkeff13)")
        self.geometry("850x700")

        self.parent = parent
        self.dkeff_input_path = None
        self.processed_data = []
        self.dkeff_queue = queue.Queue()
        self.parsed_tlookup_table = None
        self.r_ratio_options = {}

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
        self.nsop_var = tk.StringVar(value="Input c (NSOP=1)")
        self.nsop_var.trace_add('write', self._update_nsop_widgets)

        self.test_type_map = {"Constant R test": '0', "Kmax test": '1'}
        self.test_type_rev_map = {v: k for k, v in self.test_type_map.items()}
        self.test_type_var = tk.StringVar(value="Kmax test")
        self.test_type_var.trace_add('write', self._update_test_type_widgets)
        self.output_filename_var = tk.StringVar(value="dkeff_output.txt")
        self.r_var = tk.StringVar(value="0.1")
        self.smax_var = tk.StringVar(value="7.5")
        
        self._create_widgets()
        self._update_test_type_widgets() # Call once to set initial state
        
        self.transient(parent)
        self.grab_set()

    def _create_widgets(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load .lkpx Material File...", command=self._load_lkpx_file)
        file_menu.add_command(label="Load dkeff13 Input File...", command=self._load_dkeff_input_file)
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
        self.ntyp_combo = ttk.Combobox(analysis_lf, state='readonly', values=list(self.ntyp_map.keys()))
        self.ntyp_combo.current(1)
        self.ntyp_combo.grid(row=0, column=1, sticky='ew', padx=5)

        ttk.Label(analysis_lf, text="Test Type:").grid(row=1, column=0, sticky='w', pady=2)
        self.test_type_combo = ttk.Combobox(analysis_lf, textvariable=self.test_type_var, state='readonly', values=list(self.test_type_map.keys()))
        self.test_type_combo.grid(row=1, column=1, sticky='ew', padx=5)

        ttk.Label(analysis_lf, text="Analysis Mode (NSOP):").grid(row=2, column=0, sticky='w', pady=2)
        self.nsop_combo = ttk.Combobox(analysis_lf, textvariable=self.nsop_var, state='readonly', values=list(self.nsop_map.keys()))
        self.nsop_combo.grid(row=2, column=1, sticky='ew', padx=5)

        # The grid rows for the other widgets need to be shifted down
        self.kmax_lbl = ttk.Label(analysis_lf, text="Kmax:")
        self.kmax_lbl.grid(row=3, column=0, sticky='w', pady=2)
        self.kmax_entry = ttk.Entry(analysis_lf)
        self.kmax_entry.grid(row=3, column=1, sticky='ew', padx=5)

        self.r_lbl = ttk.Label(analysis_lf, text="Stress Ratio (R):")
        self.r_lbl.grid(row=4, column=0, sticky='w', pady=2)
        self.r_entry = ttk.Entry(analysis_lf, textvariable=self.r_var)
        self.r_entry.grid(row=4, column=1, sticky='ew', padx=5)

        self.smax_lbl = ttk.Label(analysis_lf, text="Smax:")
        self.smax_lbl.grid(row=5, column=0, sticky='w', pady=2)
        self.smax_entry = ttk.Entry(analysis_lf, textvariable=self.smax_var)
        self.smax_entry.grid(row=5, column=1, sticky='ew', padx=5)

        ttk.Label(analysis_lf, text="Specimen Width (W):").grid(row=6, column=0, sticky='w', pady=2)
        self.w_entry = ttk.Entry(analysis_lf)
        self.w_entry.grid(row=6, column=1, sticky='ew', padx=5)

        ttk.Label(analysis_lf, text="Specimen Thickness (T):").grid(row=7, column=0, sticky='w', pady=2)
        self.t_entry = ttk.Entry(analysis_lf)
        self.t_entry.grid(row=7, column=1, sticky='ew', padx=5)

        ttk.Label(analysis_lf, text="Constraint Factor (ALP):").grid(row=8, column=0, sticky='w', pady=2)
        self.alp_entry = ttk.Entry(analysis_lf)
        self.alp_entry.grid(row=8, column=1, sticky='ew', padx=5)
        
        ttk.Label(analysis_lf, text="Unit Conversion (LUNIT):").grid(row=9, column=0, sticky='w', pady=2)
        self.lunit_combo = ttk.Combobox(analysis_lf, state='readonly', values=list(self.lunit_map.keys()))
        self.lunit_combo.current(0)
        self.lunit_combo.grid(row=9, column=1, sticky='ew', padx=5)
        
        self.r_ratio_frame = ttk.LabelFrame(params_frame, text="R-Ratio Selection (from .lkpx)", padding="10")
        ttk.Label(self.r_ratio_frame, text="Available R-Ratios:").grid(row=0, column=0, sticky='w', pady=2)
        self.r_ratio_combo = ttk.Combobox(self.r_ratio_frame, state='readonly')
        self.r_ratio_combo.grid(row=0, column=1, sticky='ew', padx=5)
        ttk.Button(self.r_ratio_frame, text="Load Selected R-Ratio", command=self._load_selected_r_ratio_data).grid(row=0, column=2, padx=5)

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

        # --- Use an inner frame for better button/entry layout ---
        control_frame = ttk.Frame(bottom_frame)
        control_frame.pack(side='top', fill='x')

        ttk.Label(control_frame, text="Output Filename:").pack(side='left', padx=(0,5))
        ttk.Entry(control_frame, textvariable=self.output_filename_var).pack(side='left', fill='x', expand=True)

        self.generate_button = ttk.Button(control_frame, text="Generate dKeff Data", command=self._run_dkeff, state='normal')
        self.generate_button.pack(side='left', padx=5)
        self.apply_button = ttk.Button(control_frame, text="Apply to Main Window", command=self._apply_to_main, state='disabled')
        self.apply_button.pack(side='left', padx=5)
        ttk.Button(control_frame, text="Close", command=self.destroy).pack(side='right')

    def _update_test_type_widgets(self, *args):
        test_type = self.test_type_var.get()
        is_kmax_test = (test_type == "Kmax test")

        # Toggle visibility of Kmax widgets
        for widget in [self.kmax_lbl, self.kmax_entry]:
            if is_kmax_test:
                widget.grid()
            else:
                widget.grid_remove()

        # Toggle visibility of R and Smax widgets
        for widget in [self.r_lbl, self.r_entry, self.smax_lbl, self.smax_entry]:
            if not is_kmax_test:
                widget.grid()
            else:
                widget.grid_remove()

    def _redraw_grid(self, data):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.grid_widgets = []
        
        nsop_mode = self.nsop_map.get(self.nsop_var.get())
        
        # --- Dynamically set the third column header ---
        header3_text = "Crack Length (c)"
        if nsop_mode == '2':
            header3_text = "So/Smax"
        
        headers = ['ΔK', 'da/dN', header3_text]
        for col, header_text in enumerate(headers):
            # Don't create the third header if nsop is 0
            if nsop_mode == '0' and col == 2:
                continue
            ttk.Label(self.grid_frame, text=header_text, font="-weight bold").grid(row=0, column=col, padx=5, pady=2)

        for row_idx, row_data in enumerate(data):
            row_of_widgets = []
            for col_idx, cell_data in enumerate(row_data):
                # Don't create the third column of entry widgets if nsop is 0
                if nsop_mode == '0' and col_idx == 2:
                    continue
                entry = ttk.Entry(self.grid_frame, width=15)
                entry.insert(0, str(cell_data))
                entry.grid(row=row_idx + 1, column=col_idx, padx=5, pady=1)
                row_of_widgets.append(entry)
            self.grid_widgets.append(row_of_widgets)

    def _update_nsop_widgets(self, *args):
        """
        Updates the data grid header and column visibility based on the NSOP selection.
        """
        # Call redraw_grid to apply the changes. The redraw logic itself will
        # read the current nsop_var to determine how to draw the grid.
        self._redraw_grid([[w.get() for w in row_widgets] for row_widgets in self.grid_widgets])

    def _load_lkpx_file(self):
        """
        Parses an XML-based material file, identifies available R-Ratios,
        and prompts the user to select one via a dropdown menu.
        """
        filepath = filedialog.askopenfilename(
            title="Select Material File (.lkpx, .txt)",
            filetypes=(("Material Files", "*.lkpx *.txt"), ("All Files", "*.*")),
            parent=self
        )
        if not filepath:
            return

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            # --- 1. Parse Material Properties ---
            def get_prop(prop_name):
                node = root.find(f".//PropertyData[@property='{prop_name}']/Data")
                return node.text if node is not None else '0.0'

            self.syield_entry.delete(0, tk.END)
            self.syield_entry.insert(0, get_prop('yld'))
            self.sult_entry.delete(0, tk.END)
            self.sult_entry.insert(0, get_prop('ult_strength'))
            self.e_entry.delete(0, tk.END)
            self.e_entry.insert(0, get_prop('e'))

            # --- 2. Find Available R-Ratios and store data ---
            self.parsed_tlookup_table = root.find(".//PropertyData[@property='tlookup']/DataTable")
            if self.parsed_tlookup_table is None:
                messagebox.showerror("Parsing Error", "Could not find the 'tlookup' data table in the file.", parent=self)
                return

            fields = self.parsed_tlookup_table.findall(".//Fields/Field")
            self.r_ratio_options.clear()
            for field in fields:
                prop_name = field.get('property')
                if prop_name and prop_name.startswith('r_'):
                    r_value_str = prop_name.split('_')[1]
                    self.r_ratio_options[f"R = {r_value_str}"] = field.get('pos')
            
            if not self.r_ratio_options:
                messagebox.showerror("Parsing Error", "No R-ratio data columns (e.g., 'r_0.1') found.", parent=self)
                return

            # --- 3. Update the GUI to show the R-Ratio selector ---
            self.r_ratio_combo['values'] = list(self.r_ratio_options.keys())
            self.r_ratio_combo.current(0)
            self.r_ratio_frame.pack(fill='x', pady=10, anchor='n') # Show the frame
            
            # Clear any previously loaded data
            self._redraw_grid([]) 
            
            self.status_label.config(text=f"Loaded {os.path.basename(filepath)}. Please select an R-Ratio to load.")
            self.apply_button.config(state='disabled') # Disable apply until data is loaded

        except ET.ParseError as e:
            messagebox.showerror("XML Parse Error", f"Failed to parse the file. It may not be valid XML.\n\nError: {e}", parent=self)
        except Exception as e:
            messagebox.showerror("File Load Error", f"An unexpected error occurred while loading the file:\n{e}", parent=self)

    def _load_selected_r_ratio_data(self):
        """
        Populates the data grid based on the R-Ratio selected in the combobox.
        """
        if self.parsed_tlookup_table is None or not self.r_ratio_options:
            messagebox.showerror("Error", "No material file data has been loaded yet.", parent=self)
            return

        selected_key = self.r_ratio_combo.get()
        if not selected_key:
            messagebox.showerror("Error", "Please select an R-Ratio from the dropdown.", parent=self)
            return
            
        selected_pos = self.r_ratio_options.get(selected_key)
        
        loaded_data = []
        data_rows = self.parsed_tlookup_table.findall(".//Data/row")
        for row_node in data_rows:
            dadn_node = row_node.find(f"./FieldData[@pos='1']")
            dk_node = row_node.find(f"./FieldData[@pos='{selected_pos}']")

            if dk_node is not None and dadn_node is not None:
                loaded_data.append([dk_node.text, dadn_node.text, ""])

        self._redraw_grid(loaded_data)
        self.status_label.config(text=f"Displaying {len(loaded_data)} data points for {selected_key}.")
    
    def _load_dkeff_input_file(self):
        filepath = filedialog.askopenfilename(
            title="Select dkeff13 Input File",
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")),
            parent=self
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]

            def set_entry_value(entry_widget, value):
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, value)

            if len(lines) > 1:
                self.parent.vars['MAT'].set(lines[1].strip())
            
            # --- Line 4: SYIELD, SULT, E, NEP, NALP, ALP, NSOP ---
            # The format in dkeff21f.for is extended. We parse what we can.
            parts_l4 = lines[3].split()
            set_entry_value(self.syield_entry, parts_l4[0])
            set_entry_value(self.sult_entry, parts_l4[1])
            set_entry_value(self.e_entry, parts_l4[2])
            set_entry_value(self.alp_entry, parts_l4[5])
            nsop_code = parts_l4[6]
            self.nsop_var.set(self.nsop_rev_map.get(nsop_code, "Input c (NSOP=1)"))
            
            # --- Line 5: Depends on KTEST, which we must infer ---
            parts_l5 = lines[4].split()
            # If there are 5 values, it's a Constant R test file
            if len(parts_l5) == 5:
                self.test_type_var.set("Constant R test")
                mtab, r_val, smax_val, w_val, t_val = parts_l5
                self.r_var.set(r_val)
                self.smax_var.set(smax_val)
            # If there are 4 values, it's a Kmax test file
            elif len(parts_l5) == 4:
                self.test_type_var.set("Kmax test")
                mtab, kmax_val, w_val, t_val = parts_l5
                set_entry_value(self.kmax_entry, kmax_val)
            
            mtab = int(mtab)
            set_entry_value(self.w_entry, w_val)
            set_entry_value(self.t_entry, t_val)
            
            # Subsequent lines: Data grid
            loaded_data = []
            data_lines = lines[5:5 + mtab]
            for line in data_lines:
                parts = line.split()
                dk, dadn = parts[1], parts[2]
                # Conditionally read the third data column
                col3 = parts[3] if len(parts) > 3 else ""
                loaded_data.append([dk, dadn, col3])
            
            self._redraw_grid(loaded_data)
            self.status_label.config(text=f"Successfully loaded dkeff13 input file: {os.path.basename(filepath)}")
            self.apply_button.config(state='disabled')

        except Exception as e:
            messagebox.showerror("File Load Error", f"An unexpected error occurred while loading the file:\n{e}", parent=self)
    
    def _save_dkeff_input_file(self, filepath):
        try:
            mat_name = self.parent.vars['MAT'].get()
            ntyp_code = self.ntyp_map[self.ntyp_combo.get()]
            lunit_code = self.lunit_map[self.lunit_combo.get()]
            nsop_code = self.nsop_map[self.nsop_var.get()]
            
            syield, sult, e_mod, alp = self.syield_entry.get(), self.sult_entry.get(), self.e_entry.get(), self.alp_entry.get()
            w_val, t_val = self.w_entry.get(), self.t_entry.get()
            grid_data = [[widget.get() for widget in row] for row in self.grid_widgets]
            mtab = len(grid_data)

            lines = [
                f"dkeff13 input from {os.path.basename(filepath)}",
                f" {mat_name}",
                f"{ntyp_code} {lunit_code}",
                # The dkeff21f.for code expects 7 values on this line. We hard-code NEP=0 and NALP=0.
                f" {syield}  {sult}  {e_mod}  0  0  {alp}  {nsop_code}"
            ]
            
            if self.test_type_var.get() == "Kmax test":
                kmax = self.kmax_entry.get()
                lines.append(f" {mtab}  {kmax}  {w_val}  {t_val}")
            else: # Constant R test
                r_val, smax_val = self.r_var.get(), self.smax_var.get()
                lines.append(f" {mtab}  {r_val}  {smax_val}  {w_val}  {t_val}")

            for i, row in enumerate(grid_data):
                dk, dadn = row[0], row[1]
                if nsop_code == '0':
                    lines.append(f"  {i+1} {dk} {dadn}")
                else:
                    col3 = row[2]
                    lines.append(f"  {i+1} {dk} {dadn} {col3}")
            
            with open(filepath, 'w') as f:
                f.write('\n'.join(lines))
            
            self.dkeff_input_path = filepath
            self.input_file_label.config(text=f"Input File: {os.path.basename(filepath)}")
            self.status_label.config(text="Saved input file. Ready to generate data.")
            return True

        except (ValueError, KeyError):
            messagebox.showerror("Value Error", "Could not save file. Ensure all numeric fields contain valid numbers and all dropdowns are selected.", parent=self)
            return False
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save dkeff13 input file:\n{e}", parent=self)
            return False

    def _save_dkeff_file_as(self):
        filepath = filedialog.asksaveasfilename(
            title="Save dkeff13 Input File",
            defaultextension=".txt", 
            filetypes=(("dkeff13 Input", "*.txt"), ("All Files", "*.*")),
            parent=self
        )
        if filepath:
            return self._save_dkeff_input_file(filepath)
        else:
            return False # User cancelled

    def _run_dkeff(self):
        if not self.dkeff_input_path:
            if not self._save_dkeff_file_as():
                self.status_label.config(text="Status: Save cancelled. Run aborted.")
                return
        
        if not self.parent.dkeff_exe_path:
            messagebox.showerror("dkeff13 Path Not Set", "Set the path to dkeff13.exe in the main window's File menu.", parent=self)
            return

        self.generate_button.config(state="disabled")
        self.status_label.config(text="Status: Running dkeff13...")

        # Use the user-specified output filename
        output_filename = self.output_filename_var.get()
        output_path = os.path.join(os.path.dirname(self.dkeff_input_path), output_filename)
        self.dkeff_output_path = output_path # Store the output path

        thread = threading.Thread(target=self._dkeff_worker, args=(self.dkeff_input_path, output_path), daemon=True)
        thread.start()
        self.after(100, self._process_dkeff_queue)

    def _dkeff_worker(self, input_path, output_path):
        try:
            # Delete the output file before running to prevent overwrite error
            if os.path.exists(output_path):
                os.remove(output_path)
        except OSError as e:
            self.dkeff_queue.put(f"ERROR: Could not prepare output file location.\n{e}")
            return

        try:
            process = subprocess.Popen([self.parent.dkeff_exe_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', cwd=os.path.dirname(input_path))
            
            test_type_code = self.test_type_map[self.test_type_var.get()]

            # This is the sequence of inputs dkeff13.exe is expecting
            process.stdin.write("1\n") # 1. DKEFF Analysis
            process.stdin.flush()
            process.stdin.write(f"{test_type_code}\n") # 2. Test Type (0 or 1)
            process.stdin.flush()
            process.stdin.write(f"{os.path.basename(input_path)}\n") # 3. Input filename
            process.stdin.flush()
            process.stdin.write(f"{os.path.basename(output_path)}\n") # 4. Output filename
            process.stdin.flush()
            process.stdin.write("0\n") # 5. For "SHORT FILE? YES=1 NO=0", we choose NO for the full output
            process.stdin.flush()
            process.stdin.write("1\n") # 6. For "DELTA-K(0) DELTA-KEFF(1)...?", we choose 1 to output DKeff
            output, _ = process.communicate()
            
            if os.path.exists(output_path):
                self.dkeff_queue.put("DONE")
            else:
                 error_message = "dkeff13.exe did not create an output file.\n\n"
                 error_message += f"Console Output:\n{output}" if output else "No console output was captured."
                 self.dkeff_queue.put(f"ERROR: {error_message}")
        except Exception as e:
            self.dkeff_queue.put(f"ERROR: {e}")

    def _process_dkeff_queue(self):
        try:
            message = self.dkeff_queue.get_nowait()
            if "ERROR" in message:
                messagebox.showerror("dkeff13 Error", message, parent=self)
                self.status_label.config(text="Status: Error!")
                self.generate_button.config(state="normal")
            elif message == "DONE":
                # --- Parse the output file ---
                self.processed_data = []
                with open(self.dkeff_output_path, 'r') as f:
                    in_data_section = False
                    for line in f:
                        if "DKEFF ELASTIC:" in line: # Header for the results table
                            in_data_section = True
                            continue
                        if in_data_section and line.strip():
                            parts = line.split()
                            if len(parts) >= 2:
                                try:
                                    dkeff = float(parts[0])
                                    rate = float(parts[1])
                                    self.processed_data.append([f"{dkeff:.4f}", f"{rate:.4E}"])
                                except (ValueError, IndexError):
                                    continue # Skip non-data lines
                
                self.status_label.config(text=f"Run complete. {len(self.processed_data)} data points processed.")
                self.generate_button.config(state="normal")
                self.apply_button.config(state="normal") # Enable the apply button
        except queue.Empty:
            self.after(100, self._process_dkeff_queue)

    def _apply_to_main(self):
        if not self.processed_data:
            messagebox.showerror("Error", "No processed data is available to apply.", parent=self)
            return
            
        # Update the main window's data structures
        self.parent.table_data = self.processed_data
        self.parent.vars['NTAB'].set(str(len(self.processed_data)))
        
        # Call the main window's function to redraw its table
        self.parent._redraw_table()
        
        messagebox.showinfo("Success", f"Applied {len(self.processed_data)} data points to the main window's crack growth table.", parent=self)
        self.destroy() # Close the generator window

class FastranGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FASTRAN Input Generator v2.2")
        self.geometry("900x800")
        
        # Core application variables
        self.input_filepath = None
        self.spectrum_full_path = None
        self.block_data = []

        # Helper/utility variables
        self.help_window = None 
        self.fastran_exe_path = None
        self.config_filename = "fastran_gui.cfg"
        self.log_queue = queue.Queue()
        self.process = None
        
        # Variables for plotting
        self.plot_x_data = []
        self.plot_y_data = []
        self.log_x_var = tk.BooleanVar(value=False)
        self.log_y_var = tk.BooleanVar(value=False)
        self.realtime_ax = None
        self.realtime_canvas = None
        self.growth_rate_ax = None
        self.growth_rate_canvas = None
        self.growth_rate_plot_frame = None

        # --- Style and Validation Setup ---
        self.style = ttk.Style(self)
        self.style.configure('Invalid.TEntry', foreground='red')
        self.vcmd_numeric = (self.register(self._validate_numeric_input), '%W', '%P')

        self._setup_maps()
        self._init_vars()
        self._create_widgets()
        self._load_config()
        self._update_all_states()
        self.dkeff_exe_path = None
        
    def _reset_all_fields(self):
        """Resets all GUI variables and data structures to their default state."""
        # Reset all string variables
        default_data = self.get_default_data()
        for key, value in default_data.items():
            if key in self.vars:
                self.vars[key].set(value)

        # Reset dropdowns to their first option
        self.vars['NALP_DESC'].set(list(self.nalp_map.keys())[0])
        self.vars['NEP_DESC'].set(list(self.nep_map.keys())[1]) 
        self.vars['NEQN_DESC'].set(list(self.neqn_map.keys())[0])
        self.vars['NTYP_DESC'].set(list(self.ntyp_map.keys())[0])
        self.vars['LTYP_DESC'].set(list(self.ltyp_map.keys())[0])
        self.vars['NFOPT_DESC'].set(list(self.nfopt_map.keys())[0])
        self.vars['IRATE_DESC'].set(list(self.irate_map.keys())[0])
        self.vars['NGC_DESC'].set(list(self.ngc_map.keys())[0])
        self.vars['NODKL_DESC'].set(list(self.nodkl_map.keys())[0])
        self.vars['NDKTH_DESC'].set(list(self.ndkth_map.keys())[0])
        self.vars['NDKE_DESC'].set(list(self.ndke_map.keys())[0])
        self.vars['LFAST_DESC'].set(list(self.lfast_map.keys())[0])
        self.vars['KCONST_DESC'].set(list(self.kconst_map.keys())[0])
        self.vars['NTCMAX_DESC'].set(list(self.ntcmax_map.keys())[0])
        self.vars['KTH_DESC'].set(list(self.kth_map.keys())[0])

        # Clear data tables
        self.table_data = [['0.0', '0.0']]
        self.vars['NTAB'].set(str(len(self.table_data)))
        self._redraw_table()

        self.block_data = []

    def _validate_numeric_input(self, widget_name, new_value):
        widget = self.nametowidget(widget_name)
        if not new_value:
            widget.config(foreground='black')
            return True
        try:
            float(new_value)
            widget.config(foreground='black')
        except ValueError:
            widget.config(foreground='red')
        return True

    def _setup_maps(self):
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


        for map_name in ['nalp', 'nep', 'neqn', 'ntyp', 'ltyp', 'nfopt', 'irate', 'ngc', 'nodkl', 'ndkth', 'ndke', 'lfast', 'kconst', 'ntcmax', 'kth']:
            if hasattr(self, f"{map_name}_map"):
                original_map = getattr(self, f"{map_name}_map")
                setattr(self, f"{map_name}_rev_map", {v: k for k, v in original_map.items()})
   
    def _init_vars(self):
        self.vars = {key: tk.StringVar(value=val) for key, val in self.get_default_data().items()}
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
        for key in ['NALP_DESC', 'NFOPT_DESC', 'NGC_DESC', 'KTH_DESC', 'NTYP_DESC', 'LTYP_DESC', 'IRATE_DESC', 'SPECTRA']:
            self.vars[key].trace_add('write', self._update_all_states)

    def get_default_data(self):
        return {
            'OUTPUT_FILE': 'output.txt', 'SPECTRA': 'cstamp.txt', 'MAT': 'material name',
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
            'SMAXP': '0.0', 'SMINP': '0.0', 'NCYCP': '1000',
            'SMAXTH': '0', 'RTH': '0', 'CONST': '0', 'PRT': '0',
            'SCALE': '1.0',
            'GAMMA': '0.0', 'RADIUS': '0.0', 'RIVETS': '0.0', 'RLF1': '0.5',
            'RLF2': '0.5', 'DELTA': '0.0'
        }

    def _create_widgets(self):
        menubar = tk.Menu(self); self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu); menubar.add_cascade(label="Help", menu=help_menu)
        file_menu.add_command(label="Load FASTRAN Input...", command=self._load_file)
        # Call the post-processor launcher
        file_menu.add_command(label="Open FASTRAN Output File...", command=self._open_and_process_output)
        file_menu.add_command(label="Material Data Generator...", command=self._open_dkeff_window)
        file_menu.add_separator()
        file_menu.add_command(label="Set FASTRAN Path...", command=self._set_fastran_path)
        file_menu.add_command(label="Set dkeff13 Path...", command=self._set_dkeff_path)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        help_menu.add_command(label="Help...", command=self._show_help)
        top_frame = ttk.Frame(self, padding="5"); top_frame.pack(side="top", fill="x", pady=5)
        self.run_button = ttk.Button(top_frame, text="Save & Run FASTRAN", command=self._initiate_run)
        self.run_button.pack(side="right", padx=5)
        notebook = ttk.Notebook(self); notebook.pack(expand=True, fill='both', padx=5, pady=0)
        self.tab1 = ttk.Frame(notebook, padding="10"); self.tab2 = ttk.Frame(notebook, padding="10"); self.tab3 = ttk.Frame(notebook, padding="10")
        notebook.add(self.tab1, text='General & Material'); notebook.add(self.tab2, text='Crack Growth'); notebook.add(self.tab3, text='Geometry & Loading')
        self._create_tab1(); self._create_tab2(); self._create_tab3()
        self.status_var = tk.StringVar(value="Status: Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w', padding=5)
        status_bar.pack(side="bottom", fill="x")
    
    def _open_dkeff_window(self):
        """Opens the material data generator window, prompting for path if not set."""
        if not self.dkeff_exe_path:
            messagebox.showinfo("Path Required", "Please set the path to the dkeff13.exe executable first.", parent=self)
            self._set_dkeff_path() # Open the file dialog for the user
        
        # Only open the window if the path was successfully set
        if self.dkeff_exe_path:
            DkeffWindow(self)
    
    def _set_dkeff_path(self):
        """Opens a dialog to select the dkeff13.exe and saves the path."""
        filepath = filedialog.askopenfilename(
            title="Select dkeff13 Executable",
            filetypes=(("Executable Files", "*.exe"), ("All Files", "*.*"))
        )
        if filepath:
            self.dkeff_exe_path = filepath
            self._save_config()
            self.status_var.set(f"dkeff13 path set to: {self.dkeff_exe_path}")
    
    def _create_entry_row(self, parent, label, var_key, row, col=0, width=15, tooltip_text=None, state=tk.NORMAL, numeric=False):
        lbl = ttk.Label(parent, text=label); lbl.grid(row=row, column=col*2, sticky='w', padx=5, pady=2)
        entry_options = {'textvariable': self.vars[var_key], 'width': width, 'state': state}
        if numeric:
            entry_options['validate'] = 'focusout'
            entry_options['validatecommand'] = self.vcmd_numeric
        ent = ttk.Entry(parent, **entry_options); ent.grid(row=row, column=col*2+1, sticky='ew', padx=5)
        if tooltip_text: ToolTip(ent, text=tooltip_text); ToolTip(lbl, text=tooltip_text)
        return lbl, ent

    def _create_combo_row(self, parent, label, var_key, row, values, col=0, tooltip_text=None, width=15):
        lbl = ttk.Label(parent, text=label); lbl.grid(row=row, column=col*2, sticky='w', padx=5, pady=2)
        combo = ttk.Combobox(parent, textvariable=self.vars[var_key], values=values, state='readonly', width=width); combo.grid(row=row, column=col*2+1, sticky='ew', padx=5)
        if tooltip_text: ToolTip(combo, text=tooltip_text); ToolTip(lbl, text=tooltip_text)
        return lbl, combo
        
    def _create_tab1(self):
        lf1 = ttk.LabelFrame(self.tab1, text="Section 1: FASTRAN Files", padding="10"); lf1.pack(fill="x", pady=5); lf1.columnconfigure(1, weight=1)
        self.input_file_label = ttk.Label(lf1, text="Input File: Not Set", relief="sunken", padding=2, anchor='w'); self.input_file_label.grid(row=0, column=0, columnspan=2, sticky='ew', padx=5, pady=2)
        ttk.Button(lf1, text="Set Save Location...", command=self._set_input_file).grid(row=0, column=2, padx=5)
        self._create_entry_row(lf1, "Output File:", 'OUTPUT_FILE', 1, 0, width=40, tooltip_text="Filename for the FASTRAN analysis output.")
        lf23 = ttk.LabelFrame(self.tab1, text="Sections 2, 3, & 10: Loading and Material", padding="10"); lf23.pack(fill="x", pady=5); lf23.columnconfigure(1, weight=1)
        nfopt_frame = ttk.Frame(lf23); nfopt_frame.grid(row=0, column=0, columnspan=4, sticky='ew', pady=(0, 5)); nfopt_frame.columnconfigure(1, weight=1)
        self._create_combo_row(nfopt_frame, "Loading Option (NFOPT):", 'NFOPT_DESC', 0, list(self.nfopt_map.keys()), col=0, tooltip_text="Defines the type of spectrum loading.", width=35)
        spec_frame = ttk.Frame(lf23); spec_frame.grid(row=1, column=0, columnspan=4, sticky='ew'); spec_frame.columnconfigure(1, weight=1)
        self.spec_label, self.spec_entry = self._create_entry_row(spec_frame, "Spectrum File:", 'SPECTRA', 0, 0, width=40, tooltip_text="Filename of the spectrum loading file.\nUsed only for NFOPT = 5, 8, 9, 10.")
        self.browse_spec_button = ttk.Button(spec_frame, text="Browse...", command=self._browse_for_spectrum_file)
        self.browse_spec_button.grid(row=0, column=2, padx=5)
        self.edit_spec_button = ttk.Button(spec_frame, text="Edit Spectrum", command=self._open_spectrum_editor, state="disabled")
        self.edit_spec_button.grid(row=0, column=3, padx=5)
        self.edit_blocks_button = ttk.Button(spec_frame, text="Edit Blocks...", command=self._open_block_editor)
        self.edit_blocks_button.grid(row=0, column=2, padx=5)
        mat_frame = ttk.Frame(lf23); mat_frame.grid(row=2, column=0, columnspan=4, sticky='ew'); mat_frame.columnconfigure(1, weight=1)
        self._create_entry_row(mat_frame, "Material Title:", 'MAT', 0, 0, width=40, tooltip_text="Any 60-character description of the material.")
        ttk.Button(mat_frame, text="Open Material Generator...", command=self._open_dkeff_window).grid(row=0, column=2, padx=5)
        lf4 = ttk.LabelFrame(self.tab1, text="Section 4: Material Properties", padding="10"); lf4.pack(fill="x", pady=5)
        self._create_entry_row(lf4, "Yield Stress (SYIELD):", 'SYIELD', 0, 0, tooltip_text="Yield stress (0.2 percent offset).", numeric=True)
        self._create_entry_row(lf4, "Ultimate Strength (SULT):", 'SULT', 0, 1, tooltip_text="Ultimate tensile strength.", numeric=True)
        self._create_entry_row(lf4, "Elastic Modulus (E):", 'E', 1, 0, tooltip_text="Elastic modulus.", numeric=True)
        self._create_entry_row(lf4, "Poisson's Ratio (ETA):", 'ETA', 1, 1, tooltip_text="Poisson's ratio for plane strain.\nSet to 0 for plane stress (normally used).", numeric=True)
        self._create_entry_row(lf4, "Tensile Constraint (ALP):", 'ALP', 2, 0, tooltip_text="Tensile constraint factor.\n1.0 for plane-stress, 3.0 for plane-strain.", numeric=True)
        self._create_entry_row(lf4, "Comp. Constraint (BETAT):", 'BETAT', 2, 1, tooltip_text="Compressive constraint factor for intact material at crack tip.", numeric=True)
        self._create_entry_row(lf4, "Comp. Constraint (BETAW):", 'BETAW', 3, 0, tooltip_text="Compressive constraint factor along crack surface (or wake).", numeric=True)
        self._create_combo_row(lf4, "Constraint Opt (NALP):", 'NALP_DESC', 4, list(self.nalp_map.keys()), col=0, tooltip_text="0: Constraint factor (ALP) is constant as input.\n1: Constraint factor is variable (computed by the program).")
        self._create_combo_row(lf4, "Plasticity Opt (NEP):", 'NEP_DESC', 4, list(self.nep_map.keys()), col=1, tooltip_text="Effective SIF option.\n0: Elastic\n1: Plasticity-corrected (cyclic) - RECOMMENDED\n2: Closure-corrected (monotonic) - Use with caution")
    
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
        self._create_combo_row(lf56, "IRATE:", 'IRATE_DESC', 0, list(self.irate_map.keys()), 0, tooltip_text="Number of crack-growth rate relations (J=1 to IRATE).", width=22)
        self.ngc_lbl, self.ngc_combo = self._create_combo_row(lf56, "NGC:", 'NGC_DESC', 0, list(self.ngc_map.keys()), 1, tooltip_text="Enable (1) or disable (0) the small-to-large crack transition.\nOnly used for IRATE=4.")
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
        self._create_combo_row(lf56, "Equation (NEQN):", 'NEQN_DESC', 5, list(self.neqn_map.keys()), col=1, tooltip_text="Selects the crack-growth rate equation.\n0: FASTRAN equation\n1: NASGRO equation")
        
        self.lf7 = ttk.LabelFrame(content_frame, text="Section 7: Crack Growth Table & Plot", padding="10")
        self.lf7.grid(row=1, column=0, sticky="ew", pady=5)
        self.lf7.columnconfigure(1, weight=1) # Make the plot column expandable

        # --- Left frame for table controls and grid ---
        table_area_frame = ttk.Frame(self.lf7)
        table_area_frame.grid(row=0, column=0, sticky='nsew')

        table_ctrl_frame = ttk.Frame(table_area_frame)
        table_ctrl_frame.pack(fill='x', pady=2)
        ntab_lbl = ttk.Label(table_ctrl_frame, text="Num. Points (NTAB):")
        ntab_lbl.pack(side="left")
        ntab_tip = "If > 1, indicates number of points for tabular input.\nIf 0, program uses the equation from Section 6."
        ntab_spinbox = ttk.Spinbox(table_ctrl_frame, from_=0, to=100, textvariable=self.vars['NTAB'], width=5, command=self._update_table_from_ntab)
        ntab_spinbox.pack(side="left", padx=5)
        ToolTip(ntab_lbl, ntab_tip); ToolTip(ntab_spinbox, ntab_tip)
        self.ndkth_lbl = ttk.Label(table_ctrl_frame, text="NDKTH:")
        self.ndkth_lbl.pack(side="left", padx=(10, 0))
        self.ndkth_combo = ttk.Combobox(table_ctrl_frame, textvariable=self.vars['NDKTH_DESC'], values=list(self.ndkth_map.keys()), state='readonly', width=18)
        self.ndkth_combo.pack(side="left", padx=5)
        ndkth_tip = "Defines how the table is used.\n0: Direct table lookup.\n1: FASTRAN form (modifies table with threshold/fracture props).\n2: NASGRO form."
        ToolTip(self.ndkth_lbl, ndkth_tip); ToolTip(self.ndkth_combo, ndkth_tip)
        
        # --- Frame for table action buttons ---
        table_action_frame = ttk.Frame(table_area_frame)
        table_action_frame.pack(fill='x', pady=5)
        ttk.Button(table_action_frame, text="Paste from Clipboard", command=self._paste_into_table).pack(side='left')
        ttk.Button(table_action_frame, text="Update Plot", command=self._update_growth_rate_plot).pack(side='left', padx=5)

        # --- Create a container with a fixed height for the scrollable table ---
        table_scroll_container = ttk.Frame(table_area_frame)
        table_scroll_container.pack(fill="both", expand=True)
        table_scroll_container.config(height=250) 
        # Prevent the container from shrinking to fit its contents
        table_scroll_container.pack_propagate(False) 

        # --- Create Canvas and Scrollbar inside the new container ---
        table_canvas = tk.Canvas(table_scroll_container, borderwidth=0, highlightthickness=0)
        table_scrollbar = ttk.Scrollbar(table_scroll_container, orient="vertical", command=table_canvas.yview)
        table_canvas.configure(yscrollcommand=table_scrollbar.set)
        
        table_scrollbar.pack(side="right", fill="y")
        table_canvas.pack(side="left", fill="both", expand=True)

        # --- Place the original table container INSIDE the canvas ---
        self.table_frame_container = ttk.Frame(table_canvas, padding="5")
        table_canvas.create_window((0, 0), window=self.table_frame_container, anchor="nw")
        
        self.table_frame_container.bind(
            "<Configure>",
            lambda e: table_canvas.configure(
                scrollregion=table_canvas.bbox("all")
            )
        )

        # --- Right frame for the plot ---
        self.growth_rate_plot_frame = ttk.LabelFrame(self.lf7, text="da/dN vs. dK_eff", padding=5)
        self.growth_rate_plot_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
        
        fig_growth = Figure(figsize=(4, 4), dpi=100)
        fig_growth.set_tight_layout(True)
        self.growth_rate_ax = fig_growth.add_subplot(111)
        self.growth_rate_canvas = FigureCanvasTkAgg(fig_growth, master=self.growth_rate_plot_frame)
        self.growth_rate_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        self._redraw_table() # Redraw the table in its new container
        
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
        canvas = tk.Canvas(self.tab3, borderwidth=0, highlightthickness=0); scrollbar = ttk.Scrollbar(self.tab3, orient="vertical", command=canvas.yview)
        content_frame = ttk.Frame(canvas, padding="10"); content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set); canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        
        lf10 = ttk.LabelFrame(content_frame, text="Section 10: Specimen & Loading", padding="10")
        lf11 = ttk.LabelFrame(content_frame, text="Sections 11 & 13: Dimensions", padding="10")
        lf15 = ttk.LabelFrame(content_frame, text="Section 15: Pre-Crack Loading", padding="10")
        
        lf16 = ttk.LabelFrame(content_frame, text="Section 16: Special Options", padding="10")
        self.lf17 = ttk.LabelFrame(content_frame, text="Section 17: Primary Loading", padding="10")
        self.lf18 = ttk.LabelFrame(content_frame, text="Section 18: Load-Reduction Threshold Test", padding="10")
        self.conditional_frame_container = ttk.Frame(content_frame)
        self.lf12 = ttk.LabelFrame(self.conditional_frame_container, text="Section 12: Custom SIF", padding="10")
        self.lf14 = ttk.LabelFrame(self.conditional_frame_container, text="Section 14: Special Parameters", padding="10")

        # Section 9
        lf9 = ttk.LabelFrame(content_frame, text="Section 9: Data Output Options", padding="10")
        
        nipt_tooltip = "Print interval for detailed internal states (e.g., plastic zone size).\nSet to 0 to disable this extra printout (recommended)."
        nprt_tooltip = "Print interval for the main results table (crack length vs. cycles).\nSet to 0 to use the 'DCPR' crack increment for printing."
        
        self._create_entry_row(lf9, "NIPT:", "NIPT", 0, 0, tooltip_text=nipt_tooltip, numeric=True)
        self._create_entry_row(lf9, "NPRT:", "NPRT", 0, 1, tooltip_text=nprt_tooltip, numeric=True)
        
        self._create_entry_row(lf9, "LSTEP:", "LSTEP", 1, 0, tooltip_text="Cycle counting option for variable-amplitude loading.\n1 = cycle-by-cycle, 2 = block-by-block. Typically 1.", numeric=True)
        self._create_combo_row(lf9, "NDKE:", "NDKE_DESC", 1, list(self.ndke_map.keys()), col=1, tooltip_text="Option for printing effective stress-intensity factors.\n0 = Print elastic dK. 1 = Print effective dK.")
        self._create_entry_row(lf9, "DCPR:", "DCPR", 2, 0, tooltip_text="Crack-length increment for printing results.\nUsed when NPRT is set to 0.", numeric=True)
        
        # Section 10
        lf10.columnconfigure(1, weight=1); lf10.columnconfigure(3, weight=1)
        self._create_combo_row(lf10, "Specimen Type (NTYP):", 'NTYP_DESC', 0, list(self.ntyp_map.keys()), width=30, tooltip_text="Code that defines the geometry of the cracked component.")
        self._create_combo_row(lf10, "Loading Type (LTYP):", 'LTYP_DESC', 1, list(self.ltyp_map.keys()), tooltip_text="Code for loading type.\n0 = tension, 1 = bending, 2 = combined.")
        self._create_combo_row(lf10, "LFAST:", 'LFAST_DESC', 2, list(self.lfast_map.keys()), width=25, tooltip_text="Selects the crack-closure model. Option 0 is the standard model.")
        self._create_entry_row(lf10, "Num. Notch Elem. (NS):", 'NS', 3, tooltip_text="Number of elements used to model the notch-root radius (typically 1).", numeric=True)
        self.invert_lbl, self.invert_entry = self._create_entry_row(lf10, "INVERT:", "INVERT", 4, numeric=True)
        self.invert_tooltip = ToolTip(self.invert_entry, ""); ToolTip(self.invert_lbl, "")
        self._create_combo_row(lf10, "KCONST:", "KCONST_DESC", 5, list(self.kconst_map.keys()), tooltip_text="Loading control option.\n0 = constant stress loading, 1 = constant SIF range loading.")
        self.ntcmax_lbl, self.ntcmax_combo = self._create_combo_row(lf10, "NTCMAX:", "NTCMAX_DESC", 6, list(self.ntcmax_map.keys()))
        
        # Section 12 (Custom SIF)
        sif_ctrl_frame = ttk.Frame(self.lf12); sif_ctrl_frame.pack(fill='x', pady=2)
        ktab_tooltip = "Number of SIF data pairs for user-input table.\nIf 0, a user-defined equation in subroutine SIF99 is assumed.\nMaximum is 50."
        ktab_lbl = ttk.Label(sif_ctrl_frame, text="Num. SIF Pairs (KTAB):"); ktab_lbl.pack(side="left"); ToolTip(ktab_lbl, ktab_tooltip)
        ktab_spinbox = ttk.Spinbox(sif_ctrl_frame, from_=0, to=50, textvariable=self.vars['KTAB'], width=5, command=self._update_sif_table_from_ktab); ktab_spinbox.pack(side="left", padx=5); ToolTip(ktab_spinbox, ktab_tooltip)
        ttk.Button(sif_ctrl_frame, text="Paste from Clipboard", command=self._paste_into_sif_table).pack(side='left', padx=(10, 0))
        self.sif_table_container = ttk.Frame(self.lf12, padding="5"); self.sif_table_container.pack(fill="both", expand=True)
        self._redraw_sif_table()

        # Section 14 (Special Geo Params)
        self.gamma_frame = ttk.Frame(self.lf14); self._create_entry_row(self.gamma_frame, "GAMMA (Sb/S):", "GAMMA", 0, 0, tooltip_text="Ratio of outer fiber bending stress to remote tensile stress.", numeric=True)
        self.radius_frame = ttk.Frame(self.lf14); self._create_entry_row(self.radius_frame, "Cylinder Radius:", "RADIUS", 0, 0, tooltip_text="Radius of the pressurized cylinder.", numeric=True)
        self.lap_joint_frame = ttk.Frame(self.lf14)
        self._create_entry_row(self.lap_joint_frame, "Rivet Pitch:", "RIVETS", 0, 0, tooltip_text="Rivet pitch or linear spacing.", numeric=True)
        self._create_entry_row(self.lap_joint_frame, "Rivet Load Factor (RLF1):", "RLF1", 0, 1, tooltip_text="Rivet load factor (0 to 1). RLF1 + RLF2 must equal 1.", numeric=True)
        self._create_entry_row(self.lap_joint_frame, "By-pass Load Factor (RLF2):", "RLF2", 1, 0, tooltip_text="By-pass load factor (1 to 0).", numeric=True)
        self._create_entry_row(self.lap_joint_frame, "Interference (DELTA):", "DELTA", 1, 1, tooltip_text="Change in rivet radius.", numeric=True)
        self._create_combo_row(self.lap_joint_frame, "Rivet-Load Decay (NODKL):", "NODKL_DESC", 2, list(self.nodkl_map.keys()), col=0, width=25, tooltip_text="Option for rivet-load decay due to crack growth.\n0=no decay, 1=decay used.")
        self._create_entry_row(self.lap_joint_frame, "Bending/Tension (GAMMA):", "GAMMA", 3, 0, tooltip_text="Ratio of bending stress to gross-section tensile stress for the lap-splice joint.", numeric=True)
        
        # Section 11 & 13
        self._create_entry_row(lf11, "Width/Half-Width (W):", "W", 0, 0, tooltip_text="One-half width of the specimen (w).", numeric=True)
        self._create_entry_row(lf11, "Thickness (T):", "T", 0, 1, tooltip_text="Specimen thickness (t).", numeric=True)
        self._create_entry_row(lf11, "Initial Crack Len (CI):", "CI", 1, 0, tooltip_text="Initial crack length (ci). For cracks at a hole, this is c_i + r.", numeric=True)
        self._create_entry_row(lf11, "Initial Crack Dep (AI):", "AI", 1, 1, tooltip_text="Initial crack depth (ai) for surface/corner cracks.", numeric=True)
        self._create_entry_row(lf11, "Final Crack Len (CF):", "CF", 2, 0, tooltip_text="Analysis terminates when crack length exceeds this value.", numeric=True)
        self._create_entry_row(lf11, "Hole/Notch Radius (RAD):", "RAD", 2, 1, tooltip_text="Radius (r) of a circular hole or semi-circular edge notch.", numeric=True)
        self._create_entry_row(lf11, "Starter Notch Len (CN):", "CN", 3, 0, tooltip_text="Length of the starter notch (cn). If CN=CI, no pre-cracking.", numeric=True)
        self._create_entry_row(lf11, "Starter Notch Dep (AN):", "AN", 3, 1, tooltip_text="Depth of the starter notch (an).", numeric=True)
        self._create_entry_row(lf11, "Notch Half-Height (HN):", "HN", 4, 0, tooltip_text="Half-height of the starter notch (hn).", numeric=True)
        self._create_entry_row(lf11, "Fastener Radius (RADF):", "RADF", 4, 1, tooltip_text="Radius of fastener (rf). Set to 0 for open hole.\nAccounts for fastener effects on closure.", numeric=True)
        
        # Section 15
        precrack_tip = "Constant-amplitude loading to grow crack from\nstarter notch (CN) to initial crack length (CI).\nRequired inputs, but only used if CN < CI."
        self._create_entry_row(lf15, "Max Stress (SMAX):", "SMAX", 0, 0, tooltip_text=precrack_tip, numeric=True)
        self._create_entry_row(lf15, "Min Stress (SMIN):", "SMIN", 0, 1, tooltip_text=precrack_tip, numeric=True)
        
        # Section 16
        self._create_entry_row(lf16, "NRC:", "NRC", 0, 0, tooltip_text="0: Normal\n-1: Used with LFAST=4 for manual S'o/Smax input.", numeric=True)
        self._create_entry_row(lf16, "DVALUE:", "DVALUE", 0, 1, tooltip_text="Value for NRC option.\nIf NRC=-1, this is the S'o/Smax ratio for LFAST=4.", numeric=True)
        self._create_entry_row(lf16, "NCYCLE1:", "NCYCLE1", 1, 0, tooltip_text="Start cycle for stress history output.", numeric=True)
        self._create_entry_row(lf16, "NCYCLE2:", "NCYCLE2", 1, 1, tooltip_text="End cycle for stress history output.", numeric=True)

        # Section 17 (Primary Loading)
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
        
        self.va_loading_frame = ttk.Frame(self.lf17)
        ttk.Button(self.va_loading_frame, text="Edit Blocks...", command=self._open_block_editor).pack(pady=10)
        
        self.block_editor_button_frame = ttk.Frame(self.lf17)
        ttk.Button(self.block_editor_button_frame, text="Edit Loading Sequence...", command=self._open_block_editor).pack(pady=10)
        
        # Section 18 (Threshold Test)
        self._create_combo_row(self.lf18, "Test Type (KTH):", "KTH_DESC", 0, list(self.kth_map.keys()), width=25, tooltip_text="Selects the load-reduction threshold test type (0 for normal analysis).")
        self.smaxth_lbl, self.smaxth_entry = self._create_entry_row(self.lf18, "Start SMAX (SMAXTH):", "SMAXTH", 1, 0, tooltip_text="Initial maximum stress for the start of the threshold test.", numeric=True)
        self.rth_lbl, self.rth_entry = self._create_entry_row(self.lf18, "Stress Ratio (RTH):", "RTH", 1, 1, tooltip_text="Stress ratio (Smin/Smax) for the threshold test.", numeric=True)
        self.const_lbl, self.const_entry = self._create_entry_row(self.lf18, "Constant (CONST):", "CONST", 2, 0, tooltip_text="Constant K-gradient (C) for KTH=1, or dK/da for KTH=2.", numeric=True)
        self.prt_lbl, self.prt_entry = self._create_entry_row(self.lf18, "Percent (PRT):", "PRT", 2, 1, tooltip_text="Load-reduction percentage per step for KTH=3.", numeric=True)

        # Pack all frames
        lf9.pack(fill="x", pady=5, anchor="n")
        lf10.pack(fill="x", pady=5, anchor="n")
        self.conditional_frame_container.pack(fill="x", anchor="n")
        lf11.pack(fill="x", pady=5, anchor="n")
        lf15.pack(fill="x", pady=5, anchor="n")
        lf16.pack(fill="x", pady=5, anchor="n")
        self.lf17.pack(fill="x", pady=5, anchor="n")
        self.lf18.pack(fill="x", pady=5, anchor="n")
        content_frame.update_idletasks(); canvas.config(scrollregion=canvas.bbox("all"))
        
    def _open_block_editor(self):
        """Opens the editor for variable-amplitude block loading."""
        # Prepare the global parameters to pass to the editor
        initial_params = {
            'MAXSEQ': self.vars['MAXSEQ'].get(),
            'MAXBLK': self.vars['MAXBLK'].get(),
            'LPRINT': self.vars['LPRINT'].get(),
            'MAXLPR': self.vars['MAXLPR'].get(),
            'SCALE': self.vars.get('SCALE', tk.StringVar(value='1.0')).get() # Handle SCALE potentially not existing yet
        }
        BlockEditorWindow(self, self._on_blocks_saved, self.block_data, initial_params)

    def _on_blocks_saved(self, returned_data):
        """Callback function to receive data from the BlockEditorWindow."""
        params = returned_data.get('params', {})
        self.block_data = returned_data.get('blocks', [])
        
        # Update the main GUI's variables with the values from the editor
        for key, value in params.items():
            if key in self.vars:
                self.vars[key].set(value)
            elif key == 'SCALE': # Special case for SCALE if not in self.vars
                self.vars['SCALE'] = tk.StringVar(value=value)

        self.status_var.set(f"Updated with {len(self.block_data)} loading blocks.")
        
    def _browse_for_spectrum_file(self):
        """
        Opens a file dialog, then automatically converts the selected file
        to the standard FASTRAN .txt format in a background thread.
        """
        if not self.input_filepath:
            messagebox.showwarning("Set Input File", "Please set the main FASTRAN input file save location first. The spectrum file will be saved in the same directory.")
            return

        filepath = filedialog.askopenfilename(
            title="Select Spectrum File",
            filetypes=(("All Spectrum Files", "*.txt *.spx *.sub"),("Text Files", "*.txt"), ("SPX Files", "*.spx"), ("SUB Files", "*.sub"))
        )
        if not filepath:
            return

        # Start the progress window and the conversion thread
        progress = ProgressWindow(self, title="Converting Spectrum")
        progress.start()
        
        output_directory = os.path.dirname(self.input_filepath)

        thread = threading.Thread(
            target=self._conversion_worker,
            args=(filepath, output_directory),
            daemon=True
        )
        thread.start()
        
        # Start checking the queue for the result
        self.after(100, self._process_conversion_queue, progress)
            
    def _conversion_worker(self, input_path, output_dir):
        """
        Worker function to be run in a separate thread for spectrum conversion.
        """
        try:
            new_filename = self._convert_spectrum_to_txt(input_path, output_dir)
            if new_filename:
                self.log_queue.put(('success', new_filename))
            else:
                raise ValueError("Conversion failed to produce a filename.")
        except Exception as e:
            self.log_queue.put(('error', str(e)))

    def _process_conversion_queue(self, progress_window):
        """
        Checks the queue for messages from the conversion worker thread.
        """
        try:
            msg_type, msg_data = self.log_queue.get_nowait()
            progress_window.stop() # Stop and close the progress window

            if msg_type == 'success':
                new_filename = msg_data
                self.vars['SPECTRA'].set(new_filename)
                self.spectrum_full_path = os.path.join(os.path.dirname(self.input_filepath), new_filename)
                messagebox.showinfo("Success", f"Successfully converted and loaded spectrum:\n{new_filename}")
            elif msg_type == 'error':
                messagebox.showerror("Conversion Error", f"Failed to convert spectrum file:\n{msg_data}")

        except queue.Empty:
            self.after(100, self._process_conversion_queue, progress_window)
            
    def _convert_spectrum_to_txt(self, input_path, output_dir):
        """
        Parses a spectrum file (.spx, .sub, etc.) and saves it as a FASTRAN-compatible .txt file.
        Returns the new filename on success, None on failure.
        """
        _, extension = os.path.splitext(input_path)
        levels_data = None
        
        # Determine which parser to use
        if extension.lower() == '.spx':
            levels_data, title = self._parse_spx_for_conversion(input_path)
        elif extension.lower() in ['.sub', '.txt']:
            with open(input_path, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            if not lines: raise ValueError("File is empty")
            
            is_standard_fastran_txt = False
            if len(lines) > 1:
                header_parts = lines[1].split()
                if len(header_parts) == 5 and all(p.replace('.', '', 1).replace('-', '', 1).isdigit() for p in header_parts):
                    is_standard_fastran_txt = True
            
            if is_standard_fastran_txt: # It's already in the right format
                return os.path.basename(input_path)

            num_cols = len(lines[1].split()) if len(lines) > 1 else 0
            if num_cols >= 3:
                levels_data, title = self._parse_sub_for_conversion(input_path)
            elif num_cols == 1:
                levels_data, title = self._parse_reversal_txt_for_conversion(input_path)
            else: # Fallback for 2-column or other text formats
                levels_data, title = self._parse_spectrum_txt_for_conversion(input_path)
        
        if levels_data is None:
            raise ValueError(f"Could not parse file with any available parser: {os.path.basename(input_path)}")
        
        levels = []
        total_cycles, overall_smax, overall_smin = 0, -float('inf'), float('inf')
        for smax_str, smin_str, cycles_str in levels_data:
            smax, smin, cycles = float(smax_str), float(smin_str), int(cycles_str)
            if cycles < 1: continue
            levels.append({'smax': smax, 'smin': smin, 'cycles': cycles})
            total_cycles += cycles
            overall_smax = max(overall_smax, smax)
            overall_smin = min(overall_smin, smin)

        total_points = total_cycles * 2
        
        output_basename = os.path.splitext(os.path.basename(input_path))[0] + '.txt'
        output_path = os.path.join(output_dir, output_basename)
        
        with open(output_path, 'w') as f:
            f.write(f"{title}\n")
            f.write(f" {total_points}    {int(round(overall_smax))}    {int(round(overall_smin))}    0    3\n")
            
            line_str, current_col = "", 0
            for level in levels:
                for _ in range(level['cycles']):
                    line_str += f"{int(round(level['smax'])):8d}"
                    current_col += 1
                    if current_col >= 10: f.write(line_str + "\n"); line_str, current_col = "", 0
                    line_str += f"{int(round(level['smin'])):8d}"
                    current_col += 1
                    if current_col >= 10: f.write(line_str + "\n"); line_str, current_col = "", 0
            if line_str: f.write(line_str + "\n")
            
        return output_basename

    def _open_spectrum_editor(self):
            """Opens the spectrum editor, passing the default directory."""
            input_dir = ""
            # Get the directory of the main input file, if it has been set
            if self.input_filepath:
                input_dir = os.path.dirname(self.input_filepath)

            # Pass the directory to the SpectrumCreatorWindow constructor
            if self.spectrum_full_path and os.path.exists(self.spectrum_full_path):
                SpectrumCreatorWindow(self, self._on_spectrum_created, load_from_file=self.spectrum_full_path, default_dir=input_dir)
            else:
                SpectrumCreatorWindow(self, self._on_spectrum_created, load_from_file=None, default_dir=input_dir)
    
    def _parse_spx_for_conversion(self, filepath):
        tree = ET.parse(filepath)
        root = tree.getroot()
        title = root.findtext('Title', os.path.splitext(os.path.basename(filepath))[0])
        levels = []
        subspectrum = root.find('.//SubSpectrum')
        if subspectrum is not None:
            for level in subspectrum.findall('B'):
                levels.append([level.get('Mx','0'), level.get('Mn','0'), level.get('C','1')])
        return levels, title

    def _parse_sub_for_conversion(self, filepath):
        with open(filepath, 'r') as f: lines = [l.strip() for l in f.readlines() if l.strip()]
        title = lines[0]
        levels = [line.split()[:3] for line in lines[1:] if len(line.split()) >= 3]
        return levels, title

    def _parse_reversal_txt_for_conversion(self, filepath):
        with open(filepath, 'r') as f: lines = f.readlines()
        title = lines[0].strip()
        points = [float(p) for line in lines[1:] for p in line.split()]
        if len(points) < 2: return [], title
        pairs = [tuple(sorted([points[i], points[i+1]], reverse=True)) for i in range(len(points)-1)]
        counts = {p: pairs.count(p) for p in set(pairs)}
        levels = [[f"{p[0]:.4g}", f"{p[1]:.4g}", str(c)] for p, c in counts.items()]
        return levels, title

    def _parse_spectrum_txt_for_conversion(self, filepath):
        # This is a simplified parser for non-standard txt files
        with open(filepath, 'r') as f: lines = f.readlines()
        title = lines[0].strip()
        levels_data = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 2:
                smax, smin = parts[0], parts[1]
                cycles = parts[2] if len(parts) >= 3 else '1'
                levels_data.append([smax, smin, cycles])
        return levels_data, title
    
    def _open_and_process_output(self):
        """Opens a file dialog to select an output file and shows the post-processor."""
        filepath = filedialog.askopenfilename(
            title="Open FASTRAN Output File",
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        if not filepath: return
        
        header, data = self._parse_output_file(filepath)
        if header and data:
            PostProcessingWindow(self, header, data)
        else:
            messagebox.showerror("Error", "Could not parse the selected output file.", parent=self)

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
        """Calls all individual state-updating methods."""
        self._update_nalp_widgets()
        self._update_irate_widgets()
        self._update_ntyp_widgets()
        self._update_kth_widgets()
        self._update_nfopt_widgets() # Run this last as it depends on other states

    def _update_nalp_widgets(self):
        """Updates widgets dependent on the NALP selection."""
        if self.vars['NALP_DESC'].get() == self.nalp_rev_map.get('1'):
            self.lf8.grid()
        else:
            self.lf8.grid_remove()

    def _update_irate_widgets(self):
        """Updates widgets dependent on the IRATE selection."""
        irate_code = self.irate_map.get(self.vars['IRATE_DESC'].get())
        is_irate4 = (irate_code == '4')
        ngc_state = tk.NORMAL if is_irate4 else tk.DISABLED
        
        self.ngc_lbl.config(state=ngc_state)
        self.ngc_combo.config(state=ngc_state)
        self.crkngc_lbl.config(state=ngc_state)
        self.crkngc_entry.config(state=ngc_state)
        
        if not is_irate4:
            self.vars['NGC_DESC'].set(self.ngc_rev_map['0'])

        ngc_is_enabled = (self.ngc_map.get(self.vars['NGC_DESC'].get()) == '1')
        self.crkngc_entry.config(state=tk.NORMAL if (is_irate4 and ngc_is_enabled) else tk.DISABLED)

    def _update_ntyp_widgets(self):
        """Updates widgets dependent on the NTYP and LTYP selections."""
        ntyp_code = self.ntyp_map.get(self.vars['NTYP_DESC'].get())
        ltyp_code = self.ltyp_map.get(self.vars['LTYP_DESC'].get())
        
        # Logic for Section 12 Frame (Custom SIF)
        if ntyp_code in ['99', '-99']:
            self.lf12.pack(fill="x", pady=5, anchor="n")
        else:
            self.lf12.pack_forget()
            if self.vars['KTAB'].get() != '0':
                self.vars['KTAB'].set('0'); self.sif_table_data.clear(); self._redraw_sif_table()
        
        # Logic for Section 14 Frame (Special Parameters)
        self.gamma_frame.pack_forget()
        self.radius_frame.pack_forget()
        self.lap_joint_frame.pack_forget()
        show_lf14 = False

        if ntyp_code == '5':
            self.radius_frame.pack(fill='x', expand=True, padx=5, pady=2)
            show_lf14 = True
        elif ntyp_code in ['-12', '-13']:
            self.lap_joint_frame.pack(fill='x', expand=True, padx=5, pady=2)
            show_lf14 = True
        elif (ntyp_code in ['0', '7'] and ltyp_code == '2'):
            self.gamma_frame.pack(fill='x', expand=True, padx=5, pady=2)
            show_lf14 = True
        
        if show_lf14:
            self.lf14.pack(fill="x", pady=5, anchor="n")
        else:
            self.lf14.pack_forget()

    def _update_kth_widgets(self):
        """Updates widgets dependent on the KTH selection."""
        kth_code = self.kth_map.get(self.vars['KTH_DESC'].get(), '0')

        # Default state for all is disabled unless explicitly enabled
        smaxth_state = tk.DISABLED
        rth_state = tk.DISABLED
        const_state = tk.DISABLED
        prt_state = tk.DISABLED

        if kth_code in ['1', '2', '3', '4']:
            smaxth_state = tk.NORMAL
            rth_state = tk.NORMAL
        
        if kth_code in ['1', '2']:
            const_state = tk.NORMAL
            
        if kth_code == '3':
            prt_state = tk.NORMAL

        # Apply states to widgets
        self.smaxth_lbl.config(state=smaxth_state)
        self.smaxth_entry.config(state=smaxth_state)
        self.rth_lbl.config(state=rth_state)
        self.rth_entry.config(state=rth_state)
        self.const_lbl.config(state=const_state)
        self.const_entry.config(state=const_state)
        self.prt_lbl.config(state=prt_state)
        self.prt_entry.config(state=prt_state)

    def _update_nfopt_widgets(self):
        """Updates widgets dependent on the NFOPT selection."""
        nfopt_code = self.nfopt_map.get(self.vars['NFOPT_DESC'].get(), '0')

        # Logic for INVERT parameter tooltip
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
            self.invert_tooltip.text = "Not used for this NFOPT selection."
            ToolTip(self.invert_lbl, "Not used for this NFOPT selection.")

        # Logic for spectrum file widgets on Tab 1
        is_file_based = nfopt_code in ['5', '8', '9', '10']
        is_block_based = nfopt_code == '1'
        
        spec_state = tk.NORMAL if is_file_based else tk.DISABLED
        self.spec_entry.config(state=spec_state)
        self.spec_label.config(state=spec_state)
        
        self.browse_spec_button.grid() if is_file_based else self.browse_spec_button.grid_remove()
        
        if is_file_based:
            self.edit_spec_button.grid()
            spectrum_text = self.vars['SPECTRA'].get().strip()
            if not spectrum_text or spectrum_text.lower() == 'cstamp.txt':
                self.edit_spec_button.config(text="Create Spectrum", state="normal")
            else:
                self.edit_spec_button.config(text="Edit Spectrum", state="normal")
        else:
            self.edit_spec_button.grid_remove()

        self.edit_blocks_button.grid() if is_block_based else self.edit_blocks_button.grid_remove()

        if not is_file_based and not is_block_based and self.vars['SPECTRA'].get() != "cstamp.txt":
            self.vars['SPECTRA'].set("cstamp.txt")
        
        # --- Logic for Primary Loading Frame (lf17) on Tab 3 ---
        # Hide all loading frames first
        self.ca_loading_frame.pack_forget()
        self.nfopt0_params_frame.pack_forget()
        self.standard_loading_frame.pack_forget()
        self.block_editor_button_frame.pack_forget()
        
        if nfopt_code == '0':
            # For NFOPT=0, show standard parameters, SCALE, and C-A fields
            self.standard_loading_frame.pack(fill='x', pady=5)
            self.nfopt0_params_frame.pack(fill='x', pady=5)
            self.ca_loading_frame.pack(fill='x', pady=5)
            # Hide spectrum-specific fields within the standard frame
            for widget in [self.speak_lbl, self.speak_entry_main, self.smean_lbl, self.smean_entry, self.nrep_lbl, self.nrep_ent, self.marker_lbl, self.marker_ent]:
                widget.grid_remove()

        elif nfopt_code == '1':
            # For NFOPT=1, show the block editor button
            self.block_editor_button_frame.pack(fill='x')

        else: 
            # For all other spectra, show the standard frame and dynamically manage fields
            self.standard_loading_frame.pack(fill='x')
            
            # SPEAK is used for most file/standard spectra
            if nfopt_code in ['4', '5', '6', '7', '8', '9', '10']:
                self.speak_lbl.grid()
                self.speak_entry_main.grid()
            else:
                self.speak_lbl.grid_remove()
                self.speak_entry_main.grid_remove()

            # SMEAN is only for TWIST and GAUSS
            if nfopt_code in ['2', '3', '6']:
                self.smean_lbl.grid()
                self.smean_entry.grid()
            else:
                self.smean_lbl.grid_remove()
                self.smean_entry.grid_remove()
            
            # NREP and MARKER are only for NFOPT=8
            if nfopt_code == '8':
                for widget in [self.nrep_lbl, self.nrep_ent, self.marker_lbl, self.marker_ent]:
                    widget.grid()
            else:
                for widget in [self.nrep_lbl, self.nrep_ent, self.marker_lbl, self.marker_ent]:
                    widget.grid_remove()

    def _update_growth_rate_plot(self, event=None):
        """
        Reads data from the Section 7 table and updates the log-log plot.
        """
        dkeff_data = []
        rate_data = []

        # Extract data from the live entry widgets
        for row_widgets in self.table_widgets:
            try:
                dkeff_val = float(row_widgets[0].get())
                rate_val = float(row_widgets[1].get())
                if dkeff_val > 0 and rate_val > 0: # Log plots cannot have zero or negative values
                    dkeff_data.append(dkeff_val)
                    rate_data.append(rate_val)
            except (ValueError, IndexError):
                continue # Skip rows with non-numeric or invalid data

        # Plot the data
        self.growth_rate_ax.clear()
        if dkeff_data and rate_data:
            self.growth_rate_ax.plot(dkeff_data, rate_data, marker='o', linestyle='-', markersize=4)

        self.growth_rate_ax.set_xscale('log')
        self.growth_rate_ax.set_yscale('log')
        self.growth_rate_ax.set_xlabel("ΔK_eff")
        self.growth_rate_ax.set_ylabel("da/dN")
        self.growth_rate_ax.grid(True, which="both", ls="--", linewidth=0.5)
        self.growth_rate_canvas.draw()

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

    def _save_config(self):
        """Saves the FASTRAN and dkeff13 executable paths to the config file."""
        try:
            with open(self.config_filename, 'w') as f:
                if self.fastran_exe_path:
                    f.write(f"fastran_path={self.fastran_exe_path}\n")
                if self.dkeff_exe_path:
                    f.write(f"dkeff_path={self.dkeff_exe_path}\n")
        except Exception as e:
            messagebox.showerror("Config Error", f"Failed to save configuration file.\n{e}")

    def _load_config(self):
        """Loads the saved executable paths from the config file."""
        try:
            if os.path.exists(self.config_filename):
                with open(self.config_filename, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or '=' not in line:
                            continue
                        key, value = line.split('=', 1)
                        if key == 'fastran_path':
                            self.fastran_exe_path = value
                        elif key == 'dkeff_path':
                            self.dkeff_exe_path = value
                
                status_parts = []
                if self.fastran_exe_path:
                    status_parts.append("FASTRAN path loaded.")
                if self.dkeff_exe_path:
                    status_parts.append("dkeff13 path loaded.")
                
                if status_parts:
                    self.status_var.set(" ".join(status_parts))
                else:
                    self.status_var.set("Status: Paths not set. Please set them in the File menu.")
        except Exception as e:
            messagebox.showerror("Config Error", f"Failed to load configuration file.\n{e}")
            
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
        
        success = generate_fastran_file(current_values, current_table_data, self.block_data, self.input_filepath, maps_to_pass)
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
        
        self.plot_x_data.clear()
        self.plot_y_data.clear()

        # Get the integer values directly from the entry fields.
        nipt_val = int(self.vars['NIPT'].get())
        nprt_val = int(self.vars['NPRT'].get())
        
        # The real-time plot is shown ONLY if NPRT <= 0 AND NIPT == 0.
        show_realtime = (nprt_val <= 0 and nipt_val == 0)

        # Create the log window with the correct tab configuration
        self._create_log_window(show_realtime_features=show_realtime)
        
        if not show_realtime:
            # Output is sparse, so show the progress bar
            self.progress_bar.pack(fill='x', padx=10, pady=10)
            self.progress_bar.start()
        else:
            # Output is frequent, so show the text log
            self.log_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.log_scrollbar.pack(side=tk.RIGHT, fill="y")

        thread = threading.Thread(target=self._fastran_worker, daemon=True)
        thread.start()

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

    def _create_log_window(self, show_realtime_features=True):
        """Creates a Toplevel window with tabs for console output and real-time plotting."""
        self.log_window = tk.Toplevel(self)
        self.log_window.title("FASTRAN Run Log")
        self.log_window.geometry("800x600")

        self.log_notebook = ttk.Notebook(self.log_window)
        self.log_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- Tab 1: Console Log / Status Tab ---
        log_frame = ttk.Frame(self.log_notebook)
        
        # Add the progress bar, but don't display it yet
        self.progress_bar = ttk.Progressbar(log_frame, mode='indeterminate')
        
        log_text = tk.Text(log_frame, wrap='word', font=("Courier", 9))
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
        log_text['yscrollcommand'] = log_scrollbar.set

        # Store widgets to manage their visibility later
        self.log_text_widget = log_text
        self.log_scrollbar = log_scrollbar

        if show_realtime_features:
            self.log_notebook.add(log_frame, text="Console Log")
            # --- Tab 2: Real-time Plot ---
            realtime_plot_tab = ttk.Frame(self.log_notebook, padding=5)
            self.log_notebook.add(realtime_plot_tab, text="Real-time Plot")
            
            fig = Figure(dpi=100)
            fig.set_tight_layout(True)
            self.realtime_ax = fig.add_subplot(111) 
            self.realtime_canvas = FigureCanvasTkAgg(fig, master=realtime_plot_tab)
            self.realtime_canvas.get_tk_widget().pack(fill='both', expand=True)
            self.realtime_ax.set_title("Real-Time Crack Growth")
            self.realtime_ax.set_xlabel("Cycles")
            self.realtime_ax.set_ylabel("Crack Length")
            self.realtime_ax.grid(True)
        else:
            # If NIPT=0, create a single "Running..." tab
            self.log_notebook.add(log_frame, text="Running FASTRAN...")

    def _process_log_queue(self):
        """Checks queue for messages, updates log in batches, and opens post-processor when done."""
        lines_to_process = []
        plot_data_found = False
        run_complete = False

        # Process all available messages in the queue at once
        try:
            while True:
                line = self.log_queue.get_nowait()
                if line is None:
                    run_complete = True
                    break
                else:
                    lines_to_process.append(line)
                    # Check for plot data but don't plot yet
                    if self._parse_and_plot_line(line):
                        plot_data_found = True
        except queue.Empty:
            pass # The queue is empty, continue

        # Update the GUI once with the batch of new lines
        if lines_to_process:
            self.log_text_widget.insert(tk.END, "".join(lines_to_process))
            self.log_text_widget.see(tk.END)
        
        # Update the plot once if new data was found in this batch
        if plot_data_found:
            self._update_realtime_plot()

        # Handle the end of the run
        if run_complete:
            self.status_var.set("Status: Run Complete.")
            self.run_button.config(state="normal")
            
            # Stop and hide the progress bar if it was running
            if self.progress_bar.winfo_ismapped():
                self.progress_bar.stop()
                self.progress_bar.pack_forget()
            
            # Final plot update
            self._update_realtime_plot()
            
            header, data = self._parse_output_file()
            if header and data:
                PostProcessingWindow(self, header, data)
        else:
            # If not complete, schedule the next check
            self.after(100, self._process_log_queue)

    def _parse_and_plot_line(self, line):
        """
        Parses a line of console output for real-time plotting.
        Returns True if plot data was found, False otherwise.
        """
        try:
            c_val = None
            cycles = None
            if "C*- RAD =" in line and "CYCLES =" in line:
                parts = line.split()
                c_val = float(parts[parts.index("C*-") + 3])
                cycles = float(parts[parts.index("CYCLES") + 2])
            elif "C_crack" in line and "CYCLES" in line and "BLOCK" not in line:
                parts = line.split()
                c_val = float(parts[parts.index("C_crack") + 1])
                cycles = float(parts[parts.index("CYCLES") + 1])

            if c_val is not None and cycles is not None:
                self.plot_x_data.append(cycles)
                self.plot_y_data.append(c_val)
                return True # Indicate that data was found

        except (ValueError, IndexError):
            pass 
        return False # No plot data found in this line

    def _update_realtime_plot(self):
        """Clears and redraws the real-time matplotlib plot."""
        # Only proceed if the plot axes have been created
        if not self.realtime_ax:
            return
            
        if not self.plot_x_data: return
        self.realtime_ax.clear()
        self.realtime_ax.plot(self.plot_x_data, self.plot_y_data, marker='.', markersize=3, linestyle='-')
        self.realtime_ax.set_title("Real-Time Crack Growth")
        self.realtime_ax.set_xlabel("Cycles")
        self.realtime_ax.set_ylabel("Crack Length") # Updated Label
        self.realtime_ax.grid(True)
        self.realtime_canvas.draw()

    def _export_plot(self):
        """Opens a save dialog to export the current post-processing plot as an image file."""
        filepath = filedialog.asksaveasfilename(
            title="Export Plot As", parent=self.log_window,
            filetypes=(("PNG Image", "*.png"),("SVG Vector Image", "*.svg"),("PDF Document", "*.pdf"),("All Files", "*.*")),
            defaultextension=".png"
        )
        if not filepath: return
        try:
            fig = self.post_ax.get_figure() # Export the post-processing figure
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Success", f"Plot successfully exported to:\n{os.path.basename(filepath)}", parent=self.log_window)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export plot.\n{e}", parent=self.log_window)
   
    def _draw_custom_plot(self, event=None):
        """Parses the final output file and draws a user-defined plot."""
        header, data = self._parse_output_file()
        if not header or not data: return

        x_var = self.x_axis_var.get()
        y_var = self.y_axis_var.get()

        if not x_var or not y_var: return

        try:
            x_index = header.index(x_var)
            y_index = header.index(y_var)
            
            x_data = [float(row[x_index]) for row in data]
            y_data = [float(row[y_index]) for row in data]

            self.post_ax.clear()
            
            # --- New logic for plot style ---
            # Use a scatter plot for rate data to avoid messy lines
            if 'DKEC' in x_var or 'DKEA' in x_var:
                plot_style = {'marker': '.', 'linestyle': ''}
                title = f"{y_var} vs. {x_var} (Scatter)"
            else: # Use a line plot for history data
                plot_style = {'marker': '.', 'markersize': 4, 'linestyle': '-'}
                title = f"{y_var} vs. {x_var}"

            self.post_ax.plot(x_data, y_data, **plot_style)
            
            self.post_ax.set_xlabel(x_var)
            self.post_ax.set_ylabel(y_var)
            self.post_ax.set_title(title)
            self.post_ax.grid(True)
            
            # Set axis scales
            if self.log_x_var.get(): self.post_ax.set_xscale('log')
            else: self.post_ax.set_xscale('linear')
            
            if self.log_y_var.get(): self.post_ax.set_yscale('log')
            else: self.post_ax.set_yscale('linear')
            
            self.post_plot_canvas.draw()
        except (ValueError, IndexError) as e:
            messagebox.showerror("Plotting Error", f"Could not create plot.\nCheck if selected columns contain valid numeric data.\n\nDetails: {e}", parent=self.log_window)
                
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

    def _parse_output_file(self, filepath=None):
        """Reads a completed FASTRAN output file and extracts the tabular data with improved error handling."""
        if not filepath:
            if not self.input_filepath: return None, None
            filepath = os.path.join(os.path.dirname(self.input_filepath), self.vars['OUTPUT_FILE'].get())

        if not os.path.exists(filepath):
            messagebox.showerror("File Not Found", f"The output file could not be found:\n{filepath}", parent=self)
            return None, None

        header = []
        data_table = []
        in_data_section = False
        line_num = 0

        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line_num += 1
                    stripped_line = line.strip()
                    if not stripped_line:
                        continue

                    # Make header detection more flexible for different run types
                    if "BLOCK" in stripped_line and ("C_crack" in stripped_line or "C*-RAD" in stripped_line):
                        # Clean up the header and handle different column names
                        header = [h.replace('C*-RAD', 'C_crack') for h in stripped_line.split() if h]
                        in_data_section = True
                        continue
                    
                    if in_data_section:
                        # Add more flexible end-of-data section checks
                        if "SPECIMEN FAILED" in stripped_line or "CRACK LENGTH EXCEEDS" in stripped_line:
                            break
                        
                        parts = stripped_line.split()
                        if not parts: continue

                        try:
                            # Check if the first element is a valid number for a data row
                            float(parts[0])
                            
                            if parts[-1] == '*':
                                parts.pop()
                            
                            # Ensure the number of data columns matches the header
                            if len(parts) == len(header):
                                data_table.append(parts)
                            else:
                                print(f"Warning: Skipping malformed data line {line_num}: {stripped_line}")

                        except (ValueError, IndexError):
                            # This line is not a data line, so we skip it
                            continue
            
            if not data_table:
                # This message will show if parsing still fails
                messagebox.showwarning("Parsing Warning", "Could not find a valid data table in the output file.", parent=self)
                return None, None

            return header, data_table

        except Exception as e:
            messagebox.showerror("Parsing Error", f"An error occurred while parsing the output file near line {line_num}.\n{e}", parent=self)
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
            self._update_growth_rate_plot()
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
            self._update_growth_rate_plot()
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

        self._reset_all_fields()
        self._set_input_path(filepath)
        parsed_data, table_data, block_data = parse_fastran_file(filepath)

        if parsed_data:
            # Load simple variables first
            for key, value in parsed_data.items():
                if key in self.vars: self.vars[key].set(value)

            # Set descriptive variables for comboboxes using reverse maps
            for map_name in ['nalp', 'nep', 'neqn', 'ntyp', 'ltyp', 'nfopt', 'irate', 'ngc', 'nodkl', 'ndkth', 'ndke', 'lfast', 'kconst', 'ntcmax', 'kth']:
                code_key = map_name.upper()
                if map_name == 'nodkl': code_key = 'NODKL'

                desc_key = f"{code_key}_DESC"

                if code_key in parsed_data and hasattr(self, f"{map_name}_rev_map"):
                    rev_map = getattr(self, f"{map_name}_rev_map")
                    original_map = getattr(self, f"{map_name}_map")
                    
                    code_from_file = parsed_data[code_key]
                    desc_val = rev_map.get(code_from_file) # Find description for the code

                    # If the code from the file is not valid in the GUI's map
                    if desc_val is None:
                        messagebox.showwarning(
                            "Invalid Code in File",
                            f"The input file contained an unrecognized code '{code_from_file}' for the parameter {code_key}.\n\n"
                            "The GUI will select a valid default for this field."
                        )
                        # Fallback to the first valid option to prevent errors
                        desc_val = list(original_map.keys())[0]

                    if desc_key in self.vars:
                        self.vars[desc_key].set(desc_val)

            # Load the parsed table data
            self.table_data = table_data if table_data else [['0.0', '0.0']]
            self.vars['NTAB'].set(str(len(self.table_data)))
            self._redraw_table()

            # Load the parsed block data
            if block_data:
                self.block_data = block_data

            self._update_all_states()

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
        
        success = generate_fastran_file(current_values, current_table_data, self.block_data, self.input_filepath, maps_to_pass)
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