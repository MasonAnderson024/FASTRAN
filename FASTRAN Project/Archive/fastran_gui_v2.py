import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import xml.etree.ElementTree as ET

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

# --- CORRECTED: Help Window Class ---
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
        values['NALP'] = maps['nalp_map'][values['NALP_DESC']]
        values['NEP'] = maps['nep_map'][values['NEP_DESC']]
        values['NEQN'] = maps['neqn_map'][values['NEQN_DESC']]
        values['NTYP'] = maps['ntyp_map'][values['NTYP_DESC']]
        values['LTYP'] = maps['ltyp_map'][values['LTYP_DESC']]
        values['NFOPT'] = maps['nfopt_map'][values['NFOPT_DESC']]
        
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
        self.geometry("550x500")
        self.callback = callback
        self.output_filepath = None
        
        self.levels_data = [] 
        self.level_widgets = []

        self._create_widgets()
        
        if load_from_file:
            self._load_data_from_file(load_from_file)
        
        self.transient(parent)
        self.grab_set()

    def _create_widgets(self):
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill='x', padx=10, pady=5)
        top_frame.columnconfigure(1, weight=1)

        ttk.Label(top_frame, text="Spectrum Title:").grid(row=0, column=0, sticky='w', pady=2)
        self.title_entry = ttk.Entry(top_frame)
        self.title_entry.insert(0, "Custom Spectrum")
        self.title_entry.grid(row=0, column=1, columnspan=3, sticky='ew', padx=5)
        
        ttk.Label(top_frame, text="INVERT:").grid(row=1, column=0, sticky='w', pady=(5,2))
        self.invert_entry = ttk.Entry(top_frame, width=15)
        self.invert_entry.insert(0, "0")
        self.invert_entry.grid(row=1, column=1, sticky='w', padx=5)
        ToolTip(self.invert_entry, "0 for Smax,Smin pairs. 1 for Smin,Smax pairs.")

        # --- LFORMAT / ICLIP
        ttk.Label(top_frame, text="ICLIP:").grid(row=1, column=2, sticky='w', padx=5, pady=(5,2))
        self.iclip_entry = ttk.Entry(top_frame, width=15)
        self.iclip_entry.insert(0, "3")
        self.iclip_entry.grid(row=1, column=3, sticky='w')
        ToolTip(self.iclip_entry, "ICLIP value for spectrum header.\nAlso used to determine body format (e.g., 3 for 10I8).")
        
        ttk.Button(top_frame, text="Set Save Location...", command=self._set_output_file).grid(row=2, column=0, pady=(10,0))
        self.output_label = ttk.Label(top_frame, text="Spectrum File: Not Set", relief='sunken', anchor='w')
        self.output_label.grid(row=2, column=1, columnspan=3, sticky='ew', padx=5, pady=(10,0))

        table_container = ttk.LabelFrame(self, text="Stress Levels", padding="10")
        table_container.pack(fill='both', expand=True, padx=10, pady=5)
        canvas = tk.Canvas(table_container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=canvas.yview)
        self.table_frame = ttk.Frame(canvas, padding="5")
        self.table_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._redraw_levels_table()

        bottom_frame = ttk.Frame(self, padding="10")
        bottom_frame.pack(fill='x')
        ttk.Button(bottom_frame, text="Add Level", command=self._add_level).pack(side='left')
        ttk.Button(bottom_frame, text="Remove Last Level", command=self._remove_last_level).pack(side='left', padx=5)
        ttk.Button(bottom_frame, text="Generate/Update Spectrum File", command=self._generate_spectrum).pack(side='right', padx=5)

    def _redraw_levels_table(self):
        for widget in self.table_frame.winfo_children(): widget.destroy()
        self.level_widgets.clear()
        
        ttk.Label(self.table_frame, text="Max Stress", font="-weight bold").grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(self.table_frame, text="Min Stress", font="-weight bold").grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(self.table_frame, text="Cycles", font="-weight bold").grid(row=0, column=2, padx=5, pady=5)

        for i, data_row in enumerate(self.levels_data):
            smax, smin, cycles = data_row
            smax_entry = ttk.Entry(self.table_frame, width=15); smax_entry.insert(0, smax); smax_entry.grid(row=i + 1, column=0, padx=5, pady=2)
            smin_entry = ttk.Entry(self.table_frame, width=15); smin_entry.insert(0, smin); smin_entry.grid(row=i + 1, column=1, padx=5, pady=2)
            cycles_entry = ttk.Entry(self.table_frame, width=10); cycles_entry.insert(0, cycles); cycles_entry.grid(row=i + 1, column=2, padx=5, pady=2)
            self.level_widgets.append([smax_entry, smin_entry, cycles_entry])

    def _add_level(self):
        self.levels_data.append(['0.0', '0.0', '1'])
        self._redraw_levels_table()

    def _remove_last_level(self):
        if len(self.levels_data) > 0:
            self.levels_data.pop()
            self._redraw_levels_table()

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
            # Check if the file exists and is not a dummy file
            if not os.path.exists(filepath) or os.path.basename(filepath) == 'dummy.txt':
                messagebox.showinfo("Info", f"Spectrum file '{os.path.basename(filepath)}' not found or is a dummy file. Opening a new spectrum editor.", parent=self)
                return

            with open(filepath, 'r') as f:
                lines = f.readlines()

            if len(lines) < 2:
                messagebox.showwarning("Warning", f"File '{os.path.basename(filepath)}' is not a valid spectrum file.", parent=self)
                return

            # 1. Parse Header
            title = lines[0].strip()
            # The header line might have irregular spacing, so we split on whitespace
            header_parts = lines[1].strip().split()
            invert_val = header_parts[3]
            iclip_val = header_parts[4] # Read ICLIP instead of LFORMAT

            # 2. Update Header Widgets
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, title)
            self.invert_entry.delete(0, tk.END)
            self.invert_entry.insert(0, invert_val)
            self.iclip_entry.delete(0, tk.END) # Update ICLIP entry
            self.iclip_entry.insert(0, iclip_val)

            # 3. Parse Body
            format_specs = {1: {'width': 4}, 2: {'width': 5}, 3: {'width': 8}}
            col_width = format_specs.get(int(iclip_val), {'width': 8})['width']
            
            body_text = "".join(line.strip('\n\r') for line in lines[2:])
            all_points_int = [int(body_text[i:i+col_width]) for i in range(0, len(body_text), col_width) if body_text[i:i+col_width].strip()]
            
            # 4. Group points into pairs and then compress into levels
            if len(all_points_int) % 2 != 0:
                all_points_int.pop() # Ignore last point if odd number
            
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

            # 5. Update UI
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
            title = self.title_entry.get()
            invert = int(self.invert_entry.get())
            iclip = int(self.iclip_entry.get())
            
            levels = []
            total_cycles = 0
            overall_smax = -float('inf')
            overall_smin = float('inf')
            
            for row in self.level_widgets:
                smax = float(row[0].get())
                smin = float(row[1].get())
                cycles = int(row[2].get())
                if cycles < 1: continue
                levels.append({'smax': smax, 'smin': smin, 'cycles': cycles})
                total_cycles += cycles
                overall_smax = max(overall_smax, smax)
                overall_smin = min(overall_smin, smin)

            total_points = total_cycles * 2
            
            with open(self.output_filepath, 'w') as f:
                # Line 1: Title
                f.write(f"{title}\n")
                
                # --- Line 2: Write with precise formatting as requested
                
                smax_header = int(round(overall_smax))
                smin_header = int(round(overall_smin))
                header_line = f" {total_points}    {smax_header}    {smin_header}    {invert}    {iclip}\n"
                f.write(header_line)

                # Body formatting based on ICLIP value
                format_specs = {1: {'width': 4, 'count': 20}, 2: {'width': 5, 'count': 16}, 3: {'width': 8, 'count': 10}}
                spec = format_specs.get(iclip, {'width': 8, 'count': 10})
                col_width = spec['width']
                cols_per_line = spec['count']

                all_points = []
                for level in levels:
                    for _ in range(level['cycles']):
                        all_points.append(level['smax'])
                        all_points.append(level['smin'])

                line_str = ""
                current_col = 0
                for point in all_points:
                    point_int = int(round(point))
                    line_str += f"{point_int:{col_width}d}"
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

# --- Main Application Class and other functions ---

class FastranGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FASTRAN Input Generator v2.8")
        self.geometry("900x750")
        self.input_filepath = None
        self.help_window = None 
        self._setup_maps()
        self._init_vars()
        self._create_widgets()
        self._update_all_states()

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
            'Custom SIF (no hole)': '99', 'Custom SIF (at hole)': '-99'
        }
        self.ltyp_map = {'0: Tension': '0', '1: Bending': '1', '2: Combined': '2'}
        self.nfopt_map = {
            '0: Constant-Amplitude': '0', '1: Variable/Block Loading': '1', '2: TWIST Spectrum': '2',
            '3: Mini-TWIST Spectrum': '3', '4: FALSTAFF Spectrum': '4', '5: Space Shuttle Spectrum': '5',
            '6: Gaussian Spectrum (Not Recommended)': '6', '7: Helicopter Spectra': '7',
            '8: File - List of Stress Points': '8', '9: File - Flight-by-Flight': '9', '10: File - Flight Schedule': '10'
        }
        self.nalp_rev_map = {v: k for k, v in self.nalp_map.items()}
        self.nep_rev_map = {v: k for k, v in self.nep_map.items()}
        self.neqn_rev_map = {v: k for k, v in self.neqn_map.items()}
        self.ntyp_rev_map = {v: k for k, v in self.ntyp_map.items()}
        self.ltyp_rev_map = {v: k for k, v in self.ltyp_map.items()}
        self.nfopt_rev_map = {v: k for k, v in self.nfopt_map.items()}

    def _init_vars(self):
        self.vars = {key: tk.StringVar(value=val) for key, val in self.get_default_data().items()}
        self.vars['NALP_DESC'] = tk.StringVar(value=list(self.nalp_map.keys())[0])
        self.vars['NEP_DESC'] = tk.StringVar(value=list(self.nep_map.keys())[1]) 
        self.vars['NEQN_DESC'] = tk.StringVar(value=list(self.neqn_map.keys())[0])
        self.vars['NTYP_DESC'] = tk.StringVar(value=list(self.ntyp_map.keys())[0])
        self.vars['LTYP_DESC'] = tk.StringVar(value=list(self.ltyp_map.keys())[0])
        self.vars['NFOPT_DESC'] = tk.StringVar(value=list(self.nfopt_map.keys())[0])
        
        self.table_data = [['0.0', '0.0']]
        
        for key in ['NALP_DESC', 'NFOPT_DESC', 'NGC', 'KTH', 'NTYP_DESC', 'IRATE']:
            self.vars[key].trace_add('write', self._update_all_states)

    def get_default_data(self):
        return {
            'SPECTRA': 'spectrum.txt', 'MAT': 'material name',
            'SYIELD': '0.0', 'SULT': '0.0', 'E': '0.0', 'ETA': '0.0',
            'ALP': '1.0', 'BETAT': '1.0', 'BETAW': '1.0',
            'IRATE': '1', 'NGC': '0', 'CRKNGC': '0.0',
            'C1': '0.0', 'C2': '0.0', 'C3': '0.0', 'C4': '0.0', 'C5': '0.0',
            'C6': '1.0', 'C7': '1.0', 'KF': '0.0', 'M': '0.0',
            'NTAB': '1', 'NDKTH': '0',
            'RATE1': '1.E-9', 'ALP1': '3.0', 'BETAT1': '1.0', 'BETAW1': '1.0',
            'RATE2': '1.E-6', 'ALP2': '1.0', 'BETAT2': '1.0', 'BETAW2': '1.0',
            'NIPT': '0', 'NPRT': '0', 'LSTEP': '1', 'NDKE': '0', 'DCPR': '0.0',
            'LFAST': '0', 'NS': '1', 'INVERT': '0', 'KCONST': '0', 'NTCMAX': '0',
            'W': '0.0', 'T': '0.0', 'CI': '0.0', 'AI': '0.0', 'CN': '0.0', 'AN': '0.0',
            'HN': '0.0', 'RAD': '0.0', 'RADF': '0.0', 'CF': '0.0',
            'SMAX': '0.0', 'SMIN': '0.0', 'NRC': '0', 'DVALUE': '0.0',
            'NCYCLE1': '0', 'NCYCLE2': '0',
            'MAXSEQ': '0', 'MAXBLK': '0', 'LPRINT': '0', 'MAXLPR': '0',
            'NREP': '0', 'MARKER': '0', 'SPEAK': '0.0', 'SMEAN': '0.0',
            'KTH': '0', 'SMAXTH': '0', 'RTH': '0', 'CONST': '0', 'PRT': '0'
        }

    def _create_widgets(self):
        menubar = tk.Menu(self); self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0); file_menu.add_command(label="Save FASTRAN Input...", command=self._save_and_generate); file_menu.add_command(label="Load FASTRAN Input...", command=self._load_file); file_menu.add_command(label="Load Material File...", command=self._load_material_file); file_menu.add_separator(); file_menu.add_command(label="Exit", command=self.destroy)
        help_menu = tk.Menu(menubar, tearoff=0); help_menu.add_command(label="Help...", command=self._show_help)
        menubar.add_cascade(label="File", menu=file_menu); menubar.add_cascade(label="Help", menu=help_menu)
        
        top_frame = ttk.Frame(self, padding="5"); top_frame.pack(side="top", fill="x", pady=5)
        ttk.Button(top_frame, text="Generate FASTRAN Input File", command=self._save_and_generate).pack(side="right", padx=5)
        
        notebook = ttk.Notebook(self); notebook.pack(expand=True, fill='both', padx=5, pady=5)
        self.tab1 = ttk.Frame(notebook, padding="10"); self.tab2 = ttk.Frame(notebook, padding="10"); self.tab3 = ttk.Frame(notebook, padding="10")
        notebook.add(self.tab1, text='General & Material'); notebook.add(self.tab2, text='Crack Growth'); notebook.add(self.tab3, text='Geometry & Loading')
        
        self._create_tab1(); self._create_tab2(); self._create_tab3()
    
    def _create_entry_row(self, parent, label, var_key, row, col=0, width=15, tooltip_text=None, state=tk.NORMAL):
        lbl = ttk.Label(parent, text=label); lbl.grid(row=row, column=col*2, sticky='w', padx=5, pady=2)
        ent = ttk.Entry(parent, textvariable=self.vars[var_key], width=width, state=state); ent.grid(row=row, column=col*2+1, sticky='ew', padx=5)
        if tooltip_text: ToolTip(ent, text=tooltip_text); ToolTip(lbl, text=tooltip_text)
        return lbl, ent

    def _create_combo_row(self, parent, label, var_key, row, values, col=0, tooltip_text=None):
        lbl = ttk.Label(parent, text=label); lbl.grid(row=row, column=col*2, sticky='w', padx=5, pady=2)
        combo = ttk.Combobox(parent, textvariable=self.vars[var_key], values=values, state='readonly'); combo.grid(row=row, column=col*2+1, sticky='ew', padx=5)
        if tooltip_text: ToolTip(combo, text=tooltip_text); ToolTip(lbl, text=tooltip_text)
        return lbl, combo

    def _create_tab1(self):
        lf1 = ttk.LabelFrame(self.tab1, text="Section 1: FASTRAN Input File", padding="10"); lf1.pack(fill="x", pady=5); lf1.columnconfigure(1, weight=1)
        self.input_file_label = ttk.Label(lf1, text="Input File: Not Set", relief="sunken", padding=2, anchor='w'); self.input_file_label.grid(row=0, column=0, columnspan=2, sticky='ew', padx=5, pady=2)
        ttk.Button(lf1, text="Set Save Location...", command=self._set_input_file).grid(row=0, column=2, padx=5)
        
        lf23 = ttk.LabelFrame(self.tab1, text="Sections 2 & 3: Spectrum & Material", padding="10"); lf23.pack(fill="x", pady=5); lf23.columnconfigure(1, weight=1)
        
        spec_frame = ttk.Frame(lf23); spec_frame.grid(row=0, column=0, columnspan=3, sticky='ew'); spec_frame.columnconfigure(1, weight=1)
        self.spec_label, self.spec_entry = self._create_entry_row(spec_frame, "Spectrum File:", 'SPECTRA', 0, 0, width=40)
        self.browse_spec_button = ttk.Button(spec_frame, text="Browse...", command=self._browse_for_spectrum_file)
        self.browse_spec_button.grid(row=0, column=2, padx=5)
        self.create_spec_button = ttk.Button(spec_frame, text="Edit Spectrum...", command=self._open_spectrum_editor)
        self.create_spec_button.grid(row=0, column=3, padx=5)

        mat_frame = ttk.Frame(lf23); mat_frame.grid(row=1, column=0, columnspan=3, sticky='ew'); mat_frame.columnconfigure(1, weight=1)
        self._create_entry_row(mat_frame, "Material Title:", 'MAT', 0, 0, width=40)
        ttk.Button(mat_frame, text="Load from XML...", command=self._load_material_file).grid(row=0, column=2, padx=5)
        
        lf4 = ttk.LabelFrame(self.tab1, text="Section 4: Material Properties", padding="10"); lf4.pack(fill="x", pady=5)
        self._create_entry_row(lf4, "Yield Stress (SYIELD):", 'SYIELD', 0, 0); self._create_entry_row(lf4, "Ultimate Strength (SULT):", 'SULT', 0, 1)
        self._create_entry_row(lf4, "Elastic Modulus (E):", 'E', 1, 0); self._create_entry_row(lf4, "Poisson's Ratio (ETA):", 'ETA', 1, 1, tooltip_text="Set to 0 for plane stress.")
        self._create_entry_row(lf4, "Tensile Constraint (ALP):", 'ALP', 2, 0); self._create_entry_row(lf4, "Comp. Constraint (BETAT):", 'BETAT', 2, 1)
        self._create_entry_row(lf4, "Comp. Constraint (BETAW):", 'BETAW', 3, 0)
        self._create_combo_row(lf4, "Constraint Opt (NALP):", 'NALP_DESC', 4, list(self.nalp_map.keys()), col=0)
        self._create_combo_row(lf4, "Plasticity Opt (NEP):", 'NEP_DESC', 4, list(self.nep_map.keys()), col=1)

    def _create_tab2(self):
        canvas = tk.Canvas(self.tab2, borderwidth=0, highlightthickness=0); scrollbar = ttk.Scrollbar(self.tab2, orient="vertical", command=canvas.yview)
        content_frame = ttk.Frame(canvas, padding="10"); content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set); canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y"); content_frame.columnconfigure(0, weight=1)
        
        lf56 = ttk.LabelFrame(content_frame, text="Sections 5 & 6: Growth Rate & Fracture Properties", padding="10"); lf56.grid(row=0, column=0, sticky="ew")
        
        _, self.irate_entry = self._create_entry_row(lf56, "IRATE:", 'IRATE', 0, 0, tooltip_text="Defines how many crack growth curves are used (1, 2, or 4).")
        self.ngc_lbl, self.ngc_entry = self._create_entry_row(lf56, "NGC:", 'NGC', 0, 1, tooltip_text="Enable (1) or disable (0) the small-to-large crack transition.\nOnly for IRATE=4.")
        self.crkngc_lbl, self.crkngc_entry = self._create_entry_row(lf56, "CRKNGC:", 'CRKNGC', 0, 2, tooltip_text="The crack size where the small-to-large transition occurs.")
        
        self._create_entry_row(lf56, "Coefficient (C1):", 'C1', 1, 0); self._create_entry_row(lf56, "Power (C2):", 'C2', 1, 1)
        self._create_entry_row(lf56, "Threshold (C3):", 'C3', 2, 0); self._create_entry_row(lf56, "Threshold (C4):", 'C4', 2, 1)
        self._create_entry_row(lf56, "Fracture Tough. (C5):", 'C5', 3, 0); self._create_entry_row(lf56, "Fracture Power (C6):", 'C6', 3, 1)
        self._create_entry_row(lf56, "Threshold Power (C7):", 'C7', 4, 0); self._create_entry_row(lf56, "Elastic-Plastic (KF):", 'KF', 4, 1)
        self._create_entry_row(lf56, "Toughness Param. (m):", 'M', 5, 0); self._create_combo_row(lf56, "Equation (NEQN):", 'NEQN_DESC', 5, list(self.neqn_map.keys()), col=1)
        
        self.lf7 = ttk.LabelFrame(content_frame, text="Section 7: Crack Growth Table", padding="10"); self.lf7.grid(row=1, column=0, sticky="ew", pady=5)
        table_ctrl_frame = ttk.Frame(self.lf7); table_ctrl_frame.pack(fill='x', pady=2)
        ttk.Label(table_ctrl_frame, text="Num. Points (NTAB):").pack(side="left"); ttk.Entry(table_ctrl_frame, textvariable=self.vars['NTAB'], width=5).pack(side="left", padx=5)
        ttk.Button(table_ctrl_frame, text="Update Table Size", command=self._update_table_from_ntab).pack(side="left", padx=5)
        ndkth_lbl = ttk.Label(table_ctrl_frame, text="NDKTH:"); ndkth_lbl.pack(side="left", padx=(10,0))
        ndkth_entry = ttk.Entry(table_ctrl_frame, textvariable=self.vars['NDKTH'], width=5); ndkth_entry.pack(side="left", padx=5)
        ToolTip(ndkth_lbl, "Defines how the table is used (0=Direct, 1=FASTRAN form, 2=NASGRO form)."); ToolTip(ndkth_entry, "Defines how the table is used (0=Direct, 1=FASTRAN form, 2=NASGRO form).")
        self.table_frame_container = ttk.Frame(self.lf7, padding="5"); self.table_frame_container.pack(fill="both", expand=True)
        self._redraw_table()
        
        self.lf8 = ttk.LabelFrame(content_frame, text="Section 8: Transition Parameters (NALP=1)", padding="10"); self.lf8.grid(row=2, column=0, sticky="ew", pady=5)
        self._create_entry_row(self.lf8, "RATE1:", 'RATE1', 0, 0); self._create_entry_row(self.lf8, "ALP1:", 'ALP1', 0, 1)
        self._create_entry_row(self.lf8, "BETAT1:", 'BETAT1', 0, 2); self._create_entry_row(self.lf8, "BETAW1:", 'BETAW1', 0, 3)
        self._create_entry_row(self.lf8, "RATE2:", 'RATE2', 1, 0); self._create_entry_row(self.lf8, "ALP2:", 'ALP2', 1, 1)
        self._create_entry_row(self.lf8, "BETAT2:", 'BETAT2', 1, 2); self._create_entry_row(self.lf8, "BETAW2:", 'BETAW2', 1, 3)

    def _create_tab3(self):
        canvas = tk.Canvas(self.tab3, borderwidth=0, highlightthickness=0); scrollbar = ttk.Scrollbar(self.tab3, orient="vertical", command=canvas.yview)
        content_frame = ttk.Frame(canvas, padding="10"); content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set); canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        
        lf9 = ttk.LabelFrame(content_frame, text="Section 9: Data Output Options", padding="10"); lf9.pack(fill="x", pady=5, anchor="n")
        self._create_entry_row(lf9, "NIPT:", "NIPT", 0, 0); self._create_entry_row(lf9, "NPRT:", "NPRT", 0, 1)
        self._create_entry_row(lf9, "LSTEP:", "LSTEP", 1, 0); self._create_entry_row(lf9, "NDKE:", "NDKE", 1, 1)
        self._create_entry_row(lf9, "DCPR:", "DCPR", 2, 0)
        
        lf10 = ttk.LabelFrame(content_frame, text="Section 10: Specimen & Loading", padding="10"); lf10.pack(fill="x", pady=5, anchor="n")
        self._create_combo_row(lf10, "Specimen Type (NTYP):", 'NTYP_DESC', 0, list(self.ntyp_map.keys())); self._create_combo_row(lf10, "Loading Type (LTYP):", 'LTYP_DESC', 1, list(self.ltyp_map.keys()))
        _, self.lfast_entry = self._create_entry_row(lf10, "LFAST:", 'LFAST', 2, tooltip_text="Selects the crack-closure model (0 is standard)."); self._create_entry_row(lf10, "Num. Notch Elem. (NS):", 'NS', 3)
        self._create_combo_row(lf10, "Loading Option (NFOPT):", 'NFOPT_DESC', 4, list(self.nfopt_map.keys()), col=0, tooltip_text="Defines the type of spectrum loading.")
        self.invert_lbl, self.invert_entry = self._create_entry_row(lf10, "INVERT:", "INVERT", 5)
        self.invert_tooltip = ToolTip(self.invert_entry, "") 
        self.kconst_lbl, self.kconst_entry = self._create_entry_row(lf10, "KCONST:", "KCONST", 6); self.ntcmax_lbl, self.ntcmax_entry = self._create_entry_row(lf10, "NTCMAX:", "NTCMAX", 7)
        
        lf11 = ttk.LabelFrame(content_frame, text="Sections 11 & 13: Dimensions", padding="10"); lf11.pack(fill="x", pady=5, anchor="n")
        self._create_entry_row(lf11, "Width/Half-Width (W):", "W", 0, 0); self._create_entry_row(lf11, "Thickness (T):", "T", 0, 1)
        self._create_entry_row(lf11, "Initial Crack Len (CI):", "CI", 1, 0); self._create_entry_row(lf11, "Initial Crack Dep (AI):", "AI", 1, 1)
        self._create_entry_row(lf11, "Final Crack Len (CF):", "CF", 2, 0); self._create_entry_row(lf11, "Hole/Notch Radius (RAD):", "RAD", 2, 1)
        
        lf15 = ttk.LabelFrame(content_frame, text="Section 15: Pre-Crack Loading", padding="10"); lf15.pack(fill="x", pady=5, anchor="n")
        self._create_entry_row(lf15, "Max Stress (SMAX):", "SMAX", 0, 0); self._create_entry_row(lf15, "Min Stress (SMIN):", "SMIN", 0, 1)
        
        self.lf17 = ttk.LabelFrame(content_frame, text="Section 17: Primary Loading", padding="10"); self.lf17.pack(fill="x", pady=5, anchor="n")
        self._create_entry_row(self.lf17, "MAXSEQ:", "MAXSEQ", 0, 0, tooltip_text="Total # of blocks/flights in a sequence."); self._create_entry_row(self.lf17, "MAXBLK:", "MAXBLK", 0, 1, tooltip_text="Number of different kinds of blocks/flights.")
        self._create_entry_row(self.lf17, "LPRINT:", "LPRINT", 1, 0); self._create_entry_row(self.lf17, "MAXLPR:", "MAXLPR", 1, 1)
        self.speak_lbl, self.speak_entry_main = self._create_entry_row(self.lf17, "SPEAK:", "SPEAK", 2, 0, tooltip_text="Highest stress in the spectrum."); self.smean_lbl, self.smean_entry = self._create_entry_row(self.lf17, "SMEAN:", "SMEAN", 2, 1, tooltip_text="Mean stress for TWIST/Mini-TWIST/Gaussian spectra.")
        self.nrep_lbl, self.nrep_ent = self._create_entry_row(self.lf17, "NREP:", "NREP", 3, 0, tooltip_text="Number of spectrum repetitions (NFOPT=8)."); self.marker_lbl, self.marker_ent = self._create_entry_row(self.lf17, "MARKER:", "MARKER", 3, 1, tooltip_text="Starting point marker in spectrum (NFOPT=8).")
        
        content_frame.update_idletasks(); canvas.config(scrollregion=canvas.bbox("all"))

    def _update_all_states(self, *args):
        if self.vars['NALP_DESC'].get() == self.nalp_rev_map.get('1'): self.lf8.grid()
        else: self.lf8.grid_remove()
        
        is_irate4 = (self.vars['IRATE'].get() == '4')
        ngc_state = tk.NORMAL if is_irate4 else tk.DISABLED
        self.ngc_lbl.config(state=ngc_state)
        self.ngc_entry.config(state=ngc_state)
        self.crkngc_lbl.config(state=ngc_state)
        self.crkngc_entry.config(state=ngc_state)
        if not is_irate4:
            self.vars['NGC'].set('0')

        is_ngc1 = (self.vars['NGC'].get() == '1')
        self.crkngc_entry.config(state=tk.NORMAL if (is_irate4 and is_ngc1) else tk.DISABLED)

        nfopt_code = self.nfopt_map.get(self.vars['NFOPT_DESC'].get(), '0')
        
        invert_tooltips = {'2': "0-5=Clip Level", '3': "0-5=Clip Level", '4': "0=Normal, 1=Inverted", '5': "0=Full, 1=Short", '7': "1=Felix-28, 2=Helix-32", '8': "0=Max,Min; 1=Min,Max", '9': "0=Max,Min; 1=Min,Max"}
        if nfopt_code in invert_tooltips: 
            self.invert_entry.config(state=tk.NORMAL)
            self.invert_lbl.config(state=tk.NORMAL)
            self.invert_tooltip.text = invert_tooltips[nfopt_code]
        else: 
            self.invert_entry.config(state=tk.DISABLED)
            self.invert_lbl.config(state=tk.DISABLED)
            self.invert_tooltip.text = "Not used for this NFOPT selection."
        
        is_nfopt8 = (nfopt_code == '8')
        for widget in [self.nrep_lbl, self.nrep_ent, self.marker_lbl, self.marker_ent]: 
            widget.grid() if is_nfopt8 else widget.grid_remove()
        self.smean_entry.config(state=tk.NORMAL if nfopt_code in ['2', '3', '6'] else tk.DISABLED)
        self.speak_entry_main.config(state=tk.NORMAL if nfopt_code not in ['0', '1', '2', '3'] else tk.DISABLED)

        spec_file_needed = (nfopt_code in ['5', '8', '9', '10'])
        spec_state = tk.NORMAL if spec_file_needed else tk.DISABLED
        for widget in [self.spec_entry, self.browse_spec_button, self.spec_label]:
            widget.config(state=spec_state)
        if not spec_file_needed and self.vars['SPECTRA'].get() != "dummy.txt":
            self.vars['SPECTRA'].set("dummy.txt")

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
            
    def _load_file(self):
        filepath = filedialog.askopenfilename(title="Select FASTRAN Input File", filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")))
        if not filepath:
            return
            
        self._set_input_path(filepath)
        parsed_data, table_data = parse_fastran_file(filepath)
        
        if parsed_data:
            for key, value in parsed_data.items():
                if key in self.vars:
                    self.vars[key].set(value)
            
            if 'NALP' in parsed_data: self.vars['NALP_DESC'].set(self.nalp_rev_map.get(parsed_data['NALP'], ''))
            if 'NEP' in parsed_data: self.vars['NEP_DESC'].set(self.nep_rev_map.get(parsed_data['NEP'], ''))
            if 'NEQN' in parsed_data: self.vars['NEQN_DESC'].set(self.neqn_rev_map.get(parsed_data['NEQN'], ''))
            if 'NTYP' in parsed_data: self.vars['NTYP_DESC'].set(self.ntyp_rev_map.get(parsed_data['NTYP'], ''))
            if 'LTYP' in parsed_data: self.vars['LTYP_DESC'].set(self.ltyp_rev_map.get(parsed_data['LTYP'], ''))
            if 'NFOPT' in parsed_data: self.vars['NFOPT_DESC'].set(self.nfopt_rev_map.get(parsed_data['NFOPT'], ''))
            
            self.table_data = table_data if table_data else [['0.0', '0.0']]
            self.vars['NTAB'].set(str(len(self.table_data)))
            self._redraw_table()
            self._update_all_states()

    def _browse_for_spectrum_file(self):
        filepath = filedialog.askopenfilename(title="Select Spectrum File", filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")))
        if filepath: self.vars['SPECTRA'].set(os.path.basename(filepath))

    def _load_material_file(self):
        filepath = filedialog.askopenfilename(title="Select Material File", filetypes=(("XML/Text Files", "*.xml *.lkxp *.txt"), ("All Files", "*.*")))
        if not filepath: return
        name, table, properties = parse_material_xml(filepath)
        if name: self.vars['MAT'].set(name)
        if table: self.vars['NTAB'].set(str(len(table))); self.table_data = table; self._redraw_table()
        if properties:
            for key, value in properties.items():
                if key in self.vars: self.vars[key].set(value)

    def _set_input_file(self):
        filepath = filedialog.asksaveasfilename(title="Set FASTRAN Input File", defaultextension=".txt", filetypes=(("Text Files", "*.txt"),))
        if filepath: self._set_input_path(filepath)

    def _set_input_path(self, filepath):
        self.input_filepath = filepath
        self.input_file_label.config(text=f"Input File: {os.path.basename(filepath)}")

    def _run_validation_checks(self):
        try:
            syield = float(self.vars['SYIELD'].get())
            sult = float(self.vars['SULT'].get())
            if syield > sult:
                if not messagebox.askokcancel("Validation Warning", "Yield Stress (SYIELD) is greater than Ultimate Strength (SULT). This is unusual. Do you want to proceed?"):
                    return False
            
            ci = float(self.vars['CI'].get())
            cf = float(self.vars['CF'].get())
            cn = float(self.vars['CN'].get())
            rad = float(self.vars['RAD'].get())
            ntyp_str = self.vars['NTYP_DESC'].get()
            ntyp = int(self.ntyp_map[ntyp_str])

            if cf <= ci:
                messagebox.showerror("Validation Error", "Final crack length (CF) must be greater than initial crack length (CI).")
                return False
            if cn > ci:
                messagebox.showerror("Validation Error", "Notch length (CN) cannot be greater than initial crack length (CI).")
                return False
            if ntyp < 0 and rad > 0 and ci <= rad:
                messagebox.showerror("Validation Error", "For cracks at a hole (NTYP < 0), initial crack length (CI) must be greater than the hole radius (RAD).")
                return False

        except (ValueError, KeyError) as e:
            messagebox.showerror("Validation Error", f"Invalid numeric value or selection in input fields: {e}")
            return False
            
        return True

    def _save_and_generate(self):
        if not self.input_filepath:
            self._set_input_file()
        if not self.input_filepath:
            return 
        
        if not self._run_validation_checks():
            return

        current_values = {key: var.get() for key, var in self.vars.items()}
        current_table_data = [[row[0].get(), row[1].get()] for row in self.table_widgets]
        maps_to_pass = {
            'nalp_map': self.nalp_map, 'nep_map': self.nep_map, 'neqn_map': self.neqn_map,
            'ntyp_map': self.ntyp_map, 'ltyp_map': self.ltyp_map, 'nfopt_map': self.nfopt_map
        }
        
        success = generate_fastran_file(current_values, current_table_data, self.input_filepath, maps_to_pass)
        if success:
            messagebox.showinfo("Success", "FASTRAN file successfully created!")
            self.destroy()

    def _open_spectrum_editor(self):
        spectrum_file_to_edit = self.vars['SPECTRA'].get()
        # To prevent trying to load from a directory if the path isn't set,
        # we check if it's a real file. A more robust way is to join paths.
        # Assuming the file is in the current working directory if no path is given.
        full_path = spectrum_file_to_edit
        if not os.path.isabs(full_path) and self.input_filepath:
             full_path = os.path.join(os.path.dirname(self.input_filepath), spectrum_file_to_edit)
        
        SpectrumCreatorWindow(self, self._on_spectrum_created, load_from_file=full_path)

    def _on_spectrum_created(self, filename):
        if filename:
            nfopt_code = self.nfopt_map.get(self.vars['NFOPT_DESC'].get(), '0')
            if nfopt_code in ['5', '8', '9', '10']:
                 self.vars['SPECTRA'].set(filename)

    def _show_help(self):
        """
        This function now opens the new, independent HelpWindow
        instead of a simple messagebox. It ensures only one help window
        is open at a time.
        """
        if self.help_window is None or not self.help_window.winfo_exists():
            # Create a new help window if one doesn't exist
            self.help_window = HelpWindow(self)
        else:
            # If it exists, bring it to the front
            self.help_window.focus()

if __name__ == "__main__":
    app = FastranGui()
    app.mainloop()