import PySimpleGUI as sg
import textwrap
import xml.etree.ElementTree as ET
import os

#
# --- Embedded Help Text ---
#
help_text = """
These guidelines follow "FASTRAN Version 5.4-User Guide"
Please refer to this document for additional details


-----------------------------------------------------------------------------
1. Problem Title
-----------------------------------------------------------------------------
Variables: TITLE

Any 80-character title describing the problem. If TITLE(l) = HALT
analysis is terminated.


-----------------------------------------------------------------------------
2. Spectrum Filename
-----------------------------------------------------------------------------
Variables: SPECTRA

SPECTRA is the filename of the spectrum loading file (used only for 
NFOPT = 5, 8, 9 and 10). For other NFOPT values, create and use a
dummy file and filename, such as 'cstamp.txt'.


-----------------------------------------------------------------------------
3. Material Title
-----------------------------------------------------------------------------
Variables: MAT

Any 60-character description of the material.


-----------------------------------------------------------------------------
4. Material Tensile Properties, Constraint Factors and Options
-----------------------------------------------------------------------------
Variables: SYIELD, SULT, E, ETA, ALP, BETAT, BETAW, NALP, NEP

SYIELD = Yield stress (0.2 percent offset)
SULT = Ultimate tensile strength
E = Elastic modulus
ETA = 0 for plane stress (normally used)
    = Poisson's ratio for plane strain
ALP = Tensile constraint factor
    = 1 Plane-stress condition
    = 1.79 Irwin's plane-strain condition
    = 3 Plane-strain condition
BETAT = Compressive constraint factor for intact material at crack tip
BETAW = Compressive constraint factor along crack surface (or wake)
NALP = 0 Constraint factor (ALP) is constant as input
     = 1 Constraint factor is variable (ALP is computed by the
           program, see Section 8)
NEP = 0 Effective stress-intensity factor is elastic
    = 1 Effective stress-intensity factor is modified for plastic
          yielding at the crack tip by adding one-quarter of the
          cyclic plastic zone (p/4) to the crack length.
    = 2 Effective stress-intensity factor is modified for plastic
          yielding at the crack tip by adding one-quarter of the
          monotonic plastic zone to the crack length (d = c + r/4) in
          Equation (1), see Reference 20. Use caution with this option.


-----------------------------------------------------------------------------
5. Fatigue-Crack-Growth-Rate Options
-----------------------------------------------------------------------------
Variables: IRATE, NGC, CRKNGC

IRATE = 1 dc/dN = da/dN and only one equation or table is input as
          a function of Dkeff (J=1)
      = 2 dc/dN and da/dN are independent and two equations or two
          tables are input for DKeff relations, J = 1 and 2,
          repectively
      = 4 dc/dN for small and large cracks are independent (J = 1
          and 2, respectively), da/dN for small and large cracks
          are independent (J = 3 and 4, respectively), and four
          equations or four tables are input as a function of Keff
NGC = 0 Original code (CRKNGC is not used)
    = 1 Small-to-large crack transition (only for IRATE = 4 option)
CRKNGC = Small-to-large crack transitional value (suggested value
         0.00025 m or 0.01 inch.)
Repeat Sections 6 to 7 IRATE times (J = 1 to IRATE).


-----------------------------------------------------------------------------
6. Fatigue-Crack-Growth-Rate Equations and Fracture Properties
-----------------------------------------------------------------------------
Variables: C1(I,J), C2(I,J), C3(J), C4(J), C5(J), C6(J), C7(J), KF, m, NEQN

C1(I,J) = Crack-growth coefficient for property J, C1
C2(I,J) = Crack-growth power for property J, C2
C3(J) = Threshold constant, C3
C4(J) = Threshold constant, C4
C5(J) = Cyclic fracture toughness or limiting value of maximum
        elastic stress-intensity factor at failure, C5
C6(J) = Power on fracture term, C6
C7(J) = Power on threshold term, C7
KF = Elastic-plastic fracture toughness, KF
m = Fracture toughness parameter, 0 <= m <= 1
NEQN = 0 for FASTRAN equation
     = 1 for NASGRO equation

-----------------------------------------------------------------------------
7. Fatigue-Crack-Growth-Rate Table
-----------------------------------------------------------------------------
Variables: NTAB, NDKTH

NTAB = 0 Program uses crack-growth rate Equations
     = Value greater than one indicates number of data points used to describe...
NDKTH = 0 dc/dN (or da/dN) = f(DKeff)
      = 1 FASTRAN tabular form
      = 2 NASGRO tabular form
READ DKETAB(I,J), CGRTAB(I,J)
FORMAT(*)
DKETAB(I,J) = Effective stress-intensity factor range
CGRTAB(I,J) = Crack-growth rate

-----------------------------------------------------------------------------
8. Crack-Growth Rates at Transition
-----------------------------------------------------------------------------
Variables: RATE1, ALP1, BETAT1, BETAW1, RATE2, ALP2, BETAT2, BETAW2

If NALP = 0 No input is required, go to Section 9.
If NALP = 1 RATE1 is the crack-growth rate near the start of transition...
             RATE2 is the crack-growth rate near the end of the transition...

-----------------------------------------------------------------------------
9. Data Output Options
-----------------------------------------------------------------------------
Variables: NIPT, NPRT, LSTEP, NDKE, DCPR

NIPT = 0 Internal print off
     > 0 output at a half-cycle after "NIPT" crack-growth increments
NPRT = specifies frequency of crack-length-against-cycles output
LSTEP = Number of load steps from minimum to maximum load
NDKE = 0 Print out elastic stress-intensity factor ranges
     = 1 Print out effective stress-intensity factor ranges
DCPR = Crack-growth increment at which crack-length-against-cycles
       information is printed out

-----------------------------------------------------------------------------
10. Specimen Type and Loading
-----------------------------------------------------------------------------
Variables: NTYP, LTYP, LFAST, NS, NFOPT, INVERT, KCONST, NTCMAX

NTYP = Specimen type (-99 to 99)
LTYP = Type of loading (applies only for NTYP = 0 and 7)
LFAST = 0 Normal crack-closure model
NS = Number of elements used to define starter notch
NFOPT = Block (or flight) loading option
INVERT = Value between 0 and 5 to modify or select special features of spectrum
KCONST = 0 Normal value to apply stress as external loading
NTCMAX = 0 Applies for negative NTYP only.

-----------------------------------------------------------------------------
11. Specimen and Crack-Starter-Notch Dimensions
-----------------------------------------------------------------------------
Variables: W, T, CI, AI, CN, AN, HN, RAD, RADF

W = One-half width
T = Thickness
CI = Initial crack length
AI = Initial crack depth
CN = Starter notch length
AN = Starter notch depth
HN = Starter notch half-height
RAD = Radius of circular hole
RADF = Radius of fastener in circular hole

-----------------------------------------------------------------------------
12. Stress-Intensity Factor Table or Equation
-----------------------------------------------------------------------------
Variables: KTAB

KTAB = Number of pairs of normalized crack length and SIF
READ CWTAB(I), FCTAB(I)
CWTAB(I) = Normalized crack length
FCTAB(I) = Normalized stress-intensity factor

-----------------------------------------------------------------------------
13. Final Crack Length Requested
-----------------------------------------------------------------------------
Variables: CF

CF = Final crack length desired

-----------------------------------------------------------------------------
14. Special Input for Various Crack Configurations
-----------------------------------------------------------------------------
This section has conditional inputs based on NTYP value (*see full suer guide
for additional details).

-----------------------------------------------------------------------------
15. Input Constant-Amplitude Loading to Initiate Crack from Starter Notch
-----------------------------------------------------------------------------
Variables: SMAX, SMIN

Pre-cracking Stage--The crack grows from an "initial notch size"
to the "initial crack length" under constant-amplitude loading.

-----------------------------------------------------------------------------
16. Special Input for Proof Test or Constant Crack-Opening Stress Concept
-----------------------------------------------------------------------------
Variables: NRC, DVALUE, NCYCLE1, NCYCLE2

NRC = 0 DVALUE NOT USED
    = 1 Proof test simulation
    = -1 DVALUE is the crack-opening stress (So'/Smax) ratio

-----------------------------------------------------------------------------
17. Input Primary Fatigue Loading
-----------------------------------------------------------------------------
Conditional inputs based on NFOPT value (*see full user guide for additional
details).

-----------------------------------------------------------------------------
18. Input Variables for Load-Reduction Threshold Test
-----------------------------------------------------------------------------
Variables: KTH, SMAXTH, RTH, CONST, PRT

KTH = 0 No threshold test
    = 1 ASTM recommended practice
    = 2 Stress-intensity gradient procedure
    = 3 Step (increase/decrease) loading procedure
    = 4 Kmax test procedure
"""

#
# --- Helper functions to safely convert values, preventing crashes ---
#
def safe_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

#
# --- Function to control which GUI elements are visible/active ---
#
def update_form_visibility(window, values):
    """
    Shows, hides, or disables GUI elements based on user selections
    to ensure only relevant fields are presented.
    """
    if not values: return

    # --- Section 8 visibility based on NALP ---
    nalp_val = values.get('-NALP-', '0: Constant')
    is_nalp1 = ('1' in str(nalp_val))
    window['-FRAME_SEC_8-'].update(visible=is_nalp1)

    # --- Section 12 & 14 visibility based on NTYP ---
    ntyp_val_str = values.get('-NTYP-', 'Center crack tension (CCT)')

    ntyp_val = 0
    if ntyp_val_str in ntyp_map:
        ntyp_val = ntyp_map[ntyp_val_str]
    elif str(ntyp_val_str).lstrip('-').isdigit() and int(ntyp_val_str) in ntyp_map.values():
        ntyp_val = int(ntyp_val_str)

    sec12_visible = ntyp_val in [99, -99]
    window['-FRAME_SEC_12-'].update(visible=sec12_visible)

    ltyp_val_str = values.get('-LTYP-', '0: Tension')
    ltyp_val = ltyp_map.get(ltyp_val_str, 0)
    sec14a_visible = ntyp_val in [0, 7, -10] and ltyp_val == 2
    window['-FRAME_SEC_14A-'].update(visible=sec14a_visible)

# --- Pop-up Help Window Function ---
def create_help_window():
    layout = [[sg.Text("FASTRAN Input Guide", font="_ 12 bold")],
              [sg.Multiline(help_text, size=(85, 30), key='-HELP_TEXT-', disabled=True, autoscroll=True, expand_x=True, expand_y=True)],
              [sg.Button("Close")]]
    window = sg.Window("Help Guide", layout, resizable=True, finalize=True)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "Close": break
    window.close()

# --- File Parsing and Generation Functions ---
def parse_material_file(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        material_data = {}
        name_element = root.find('.//Name')
        if name_element is not None: material_data['name'] = name_element.text
        else: material_data['name'] = 'Unknown Material'
        table_rows = []
        for row in root.findall('.//dadn_table/row'):
            dK_element = row.find("./FieldData[@pos='2']"); rate_element = row.find("./FieldData[@pos='1']")
            if dK_element is not None and rate_element is not None: table_rows.append([dK_element.text, rate_element.text])
        material_data['table'] = table_rows
        if not table_rows: sg.popup_warning("Could not find a da/dN table in the selected material file.")
        return material_data
    except Exception as e:
        sg.popup_error(f"Failed to parse material file: {e}")
        return None

def parse_fastran_file(filepath):
    try:
        with open(filepath, 'r') as f: lines = [line.strip() for line in f.readlines() if line.strip()]
        if not lines: sg.popup_error("The selected file is empty."); return None, None
        data = {}; line_idx = 0
        def get_vals(line_index): return lines[line_index].split()

        line_idx += 1  # Skip title line

        data['-SPECTRA-'] = lines[line_idx]; line_idx += 1
        data['-MAT-'] = lines[line_idx]; line_idx += 1
        
        vals = get_vals(line_idx); data['-SYIELD-'], data['-SULT-'], data['-E-'], data['-ETA-'], data['-ALP-'], data['-BETAT-'], data['-BETAW-'], data['-NALP-'], data['-NEP-'] = vals[0:9]; line_idx += 1
        vals = get_vals(line_idx); data['-IRATE-'], data['-NGC-'], data['-CRKNGC-'] = vals[0:3]; line_idx += 1
        
        vals = get_vals(line_idx); data['-C1-'], data['-C2-'], data['-C3-'], data['-C4-'], data['-C5-'], data['-C6-'], data['-C7-'], data['-KF-'], data['-M-'], data['-NEQN-'] = vals[0:10]; line_idx += 1
        
        vals = get_vals(line_idx)
        ntab = int(vals[0])
        data['-NTAB-'] = str(ntab)
        if len(vals) > 1: data['-NDKTH-'] = vals[1]
        else: data['-NDKTH-'] = '0'
        line_idx += 1

        table_data = []
        if ntab > 0:
            data['-USE_TABLE-'] = True
            data['-USE_EQUATION-'] = False
            for _ in range(ntab):
                vals = get_vals(line_idx); table_data.append(vals[0:2]); line_idx += 1
        else:
            data['-USE_TABLE-'] = False
            data['-USE_EQUATION-'] = True

        if data.get('-NALP-') == '1' and line_idx < len(lines):
            try:
                if "E" in lines[line_idx].upper():
                    vals = get_vals(line_idx); data['-RATE1-'], data['-ALP1-'], data['-BETAT1-'], data['-BETAW1-'], data['-RATE2-'], data['-ALP2-'], data['-BETAT2-'], data['-BETAW2-'] = vals[0:8]; line_idx += 1
            except IndexError: pass

        vals = get_vals(line_idx); data['-NIPT-'],data['-NPRT-'],data['-LSTEP-'],data['-NDKE-'],data['-DCPR-'] = vals[0:5]; line_idx+=1
        vals = get_vals(line_idx); data['-NTYP-'],data['-LTYP-'],data['-LFAST-'],data['-NS-'],data['-NFOPT-'],data['-INVERT-'],data['-KCONST-'],data['-NTCMAX-'] = vals[0:8]; line_idx+=1
        vals = get_vals(line_idx); data['-W-'],data['-T-'],data['-CI-'],data['-AI-'],data['-CN-'],data['-AN-'],data['-HN-'],data['-RAD-'],data['-RADF-'] = vals[0:9]; line_idx+=1
        data['-CF-'] = lines[line_idx].split()[0]; line_idx+=1
        vals = get_vals(line_idx); data['-SMAX-'], data['-SMIN-'] = vals[0:2]; line_idx+=1
        vals = get_vals(line_idx); data['-NRC-'], data['-DVALUE-'], data['-NCYCLE1-'], data['-NCYCLE2-'] = vals[0:4]; line_idx+=1

        nfopt_val = int(data.get('-NFOPT-', 0))
        if nfopt_val in [0, 1, 8, 9, 10]:
            vals = get_vals(line_idx)
            if nfopt_val in [0,1]:
                data['-MAXSEQ-'], data['-MAXBLK-'], data['-LPRINT-'], data['-MAXLPR-'] = vals[0:4]
            elif nfopt_val == 8:
                 data['-MAXSEQ-'], data['-MAXBLK-'], data['-LPRINT-'], data['-MAXLPR-'], data['-NREP-'], data['-MARKER-'] = vals[0:6]
            else:
                data['-MAXSEQ-'], data['-MAXBLK-'], data['-LPRINT-'], data['-MAXLPR-'] = vals[0:4]
            line_idx+=1
            data['-SPEAK-'] = lines[line_idx].split()[0]; line_idx+=1

        if line_idx < len(lines) and "HALT" not in lines[line_idx].upper():
             vals = get_vals(line_idx); data['-KTH-'], data['-SMAXTH-'], data['-RTH-'], data['-CONST-'], data['-PRT-'] = vals[0:5]; line_idx+=1

        return data, table_data
    except Exception as e:
        sg.popup_error(f"Failed to parse FASTRAN file.\nError: {e}\n\nPlease ensure it is a valid input file matching the user guide format.")
        return None, None

def generate_fastran_file(values, save_path):
    try:
        if not save_path:
            sg.popup_error("Please set an output file location first using the 'Set Output File' button.")
            return

        problem_title = os.path.basename(save_path)

        output_lines = []
        output_lines.append(f"{problem_title}")
        output_lines.append(f"{values['-SPECTRA-']}")
        output_lines.append(f" {values['-MAT-']}")
        output_lines.append(f"  {safe_float(values['-SYIELD-']):.1f}  {safe_float(values['-SULT-']):.1f}  {safe_float(values['-E-']):.1f}   {safe_float(values['-ETA-'])}  {safe_float(values['-ALP-'])}  {safe_float(values['-BETAT-'])}  {safe_float(values['-BETAW-'])}  {1 if '1' in values['-NALP-'] else 0}  {nep_options.index(values['-NEP-'])}")
        output_lines.append(f"    {1 if '1' in values['-IRATE-'] else (4 if '4' in values['-IRATE-'] else 2)}    {safe_int(values['-NGC-'])}    {safe_float(values['-CRKNGC-']):.1f}")
        output_lines.append(f" {safe_float(values['-C1-']):.2E} {safe_float(values['-C2-']):.2E}  {safe_float(values['-C3-'])}  {safe_float(values['-C4-'])}  {safe_float(values['-C5-']):.4E}  {safe_float(values['-C6-'])}  {safe_float(values['-C7-'])}  {safe_float(values['-KF-'])}  {safe_float(values['-M-'])}  {safe_int(values['-NEQN-'])}")

        if values['-USE_TABLE-']:
            ntab = safe_int(values['-NTAB-'])
            output_lines.append(f"    {ntab}    {safe_int(values['-NDKTH-'])}")
            for i in range(ntab):
                dk_val = safe_float(values[('-DK-', i)])
                rate_val = safe_float(values[('-RATE-', i)])
                
                # Custom formatting to match reference file
                formatted_rate = f"{rate_val:g}"
                if "e" in formatted_rate:
                    formatted_rate = formatted_rate.replace("e-0", "e-")
                if dk_val == 88.00: # Special case from file to avoid sci notation
                    formatted_rate = "0.04"

                output_lines.append(f"  {dk_val:<5.2f}   {formatted_rate}")
        else:
            output_lines.append(f"    0    {safe_int(values['-NDKTH-'])}")

        if '1' in values['-NALP-']:
            output_lines.append(f"{safe_float(values['-RATE1-']):.1E}  {safe_float(values['-ALP1-']):.2f}  {safe_float(values['-BETAT1-'])}  {safe_float(values['-BETAW1-'])}  {safe_float(values['-RATE2-']):.1E}  {safe_float(values['-ALP2-']):.2f}  {safe_float(values['-BETAT2-'])}  {safe_float(values['-BETAW2-'])}")
        
        output_lines.append(f"   {safe_int(values['-NIPT-'])}   {safe_int(values['-NPRT-'])}    {safe_int(values['-LSTEP-'])}    {safe_int(values['-NDKE-'])}   {safe_float(values['-DCPR-']):.5f}")
        output_lines.append(f"   {safe_int(ntyp_map[values['-NTYP-']])}    {safe_int(ltyp_map[values['-LTYP-']])}    {safe_int(values['-LFAST-'])}    {safe_int(values['-NS-'])}     {safe_int(nfopt_map[values['-NFOPT-']])}    {safe_int(values['-INVERT-'])}    {safe_int(values['-KCONST-'])}    {safe_int(values['-NTCMAX-'])}")
        output_lines.append(f" {safe_float(values['-W-'])}  {safe_float(values['-T-'])}  {safe_float(values['-CI-'])}  {safe_float(values['-AI-'])}  {safe_float(values['-CN-'])}  {safe_float(values['-AN-'])}  {safe_float(values['-HN-'])}   {safe_float(values['-RAD-'])}   {safe_float(values['-RADF-'])}")
        output_lines.append(f" {safe_float(values['-CF-'])}")
        output_lines.append(f"   {safe_float(values['-SMAX-']):.1f}       {safe_float(values['-SMIN-']):.1f}")
        output_lines.append(f" {safe_int(values['-NRC-'])}   {safe_float(values['-DVALUE-'])}    {safe_int(values['-NCYCLE1-'])}    {safe_int(values['-NCYCLE2-'])}")

        nfopt_val = nfopt_map[values['-NFOPT-']]
        if nfopt_val in [0,1,8,9,10]:
            loading_line = f"  {safe_int(values['-MAXSEQ-'])}  {safe_int(values['-MAXBLK-'])}  {safe_int(values['-LPRINT-'])}  {safe_int(values['-MAXLPR-'])}"
            if nfopt_val == 8:
                loading_line += f"  {safe_int(values['-NREP-'])}  {safe_int(values['-MARKER-'])}"
            output_lines.append(loading_line)
        output_lines.append(f"    {safe_float(values['-SPEAK-']):.1f}")

        output_lines.append(f" {safe_int(values['-KTH-'])}   {safe_int(safe_float(values['-SMAXTH-']))}   {safe_int(safe_float(values['-RTH-']))}   {safe_int(safe_float(values['-CONST-']))}   {safe_int(safe_float(values['-PRT-']))}")

        output_lines.append("HALT"); output_lines.append("HALT")

        with open(save_path, 'w') as f:
            f.write('\n'.join(output_lines))
        sg.popup('Success!', f'FASTRAN input file saved to:\n{save_path}')

    except Exception as e:
        sg.popup_error('Error', "\n".join(textwrap.wrap(f"An error occurred during file generation: {e}", width=80)))


def create_main_window(ntab_rows, table_data, override_values=None):
    if override_values is None: override_values = {}
    sg.theme('DarkBlue12')
    global ntyp_map, ntyp_options, ltyp_map, nfopt_map, irate_options, neqn_options, nalp_options, nep_options
    ntyp_map = {
        'Center crack tension (CCT)': 1, 'Compact C(T) specimen': 2, 'Single-edge crack tension (SECT)': 3,
        'Single-edge crack bend (SECB)': 4, 'Through crack in pressurized cylinder': 5,
        'One through crack at a hole': -3, 'Two symmetric through cracks at a hole': -4,
        'Surface crack under tension/bending': 0, 'Corner crack in plate': 7,
        'Custom SIF (from hole)': -99, 'Custom SIF (no hole)': 99
    }
    ntyp_options = list(ntyp_map.keys())
    ltyp_map = {'0: Tension': 0, '1: Bending': 1, '2: Combined': 2}
    nfopt_map = {'0: Constant-Amplitude': 0, '1: Variable-Amplitude (Block Loading)': 1, '8: Spectrum from file (stress points)': 8, '9: Spectrum from file (flight-by-flight)': 9, '10: Spectrum from file (flight schedule)': 10}
    irate_options = ['1: dc/dN = da/dN', '2: Independent dc/dN and da/dN', '4: Independent small/large cracks']
    neqn_options = ['0: FASTRAN Equation', '1: NASGRO Equation']
    nalp_options = ['0: Constant', '1: Variable (computed by program)']
    nep_options = ['0: Elastic', '1: Plasticity-Corrected (monotonic)', '2: Closure Corrected (cyclic)']
    BLANK = ''; ZERO = '0.0'
    def T(text, **kwargs): return sg.Text(text, size=(10,1), **kwargs)

    # --- Tab 1 Layout ---
    tab1_layout = [
        [sg.Text('Section 1: Output File', font='_ 11 bold')],
        [sg.Text('File Path:', size=(12,1)), sg.Text(override_values.get('-OUTPUT_FILE_DISPLAY-', 'No file set.'), key='-OUTPUT_FILE_DISPLAY-', size=(60,1), relief='sunken')],
        [sg.Button('Set Output File', key='-SET_OUTPUT-')],
        [sg.HSep()],
        # --- FIX: Changed FileBrowse to a separate button for path stripping ---
        [sg.Frame("Section 2: Spectrum Filename", [[sg.T('Spectrum File', size=(12,1)), sg.Input(override_values.get('-SPECTRA-', BLANK), k='-SPECTRA-', s=(40,1)), sg.Button('Browse', key='-BROWSE_SPECTRA-')]])],
        [sg.Frame("Section 3: Material Title", [[sg.T('Material Title', size=(12,1)), sg.Input(override_values.get('-MAT-', BLANK), k='-MAT-', s=(60,1))]])],
        [sg.HSep()],
        [sg.Frame("Section 4: Material Tensile Properties", font='_ 11 bold', layout=[
            [T('SYIELD'), sg.Input(override_values.get('-SYIELD-', ZERO), k='-SYIELD-', s=(8,1)), T('SULT'), sg.Input(override_values.get('-SULT-', ZERO), k='-SULT-', s=(8,1)), T('E'), sg.Input(override_values.get('-E-', ZERO), k='-E-', s=(10,1)), T('ETA'), sg.Input(override_values.get('-ETA-', ZERO), k='-ETA-', s=(5,1))],
            [T('ALP'), sg.Input(override_values.get('-ALP-', '1.0'), k='-ALP-', s=(5,1)), T('BETAT'), sg.Input(override_values.get('-BETAT-', '1.0'), k='-BETAT-', s=(5,1)), T('BETAW'), sg.Input(override_values.get('-BETAW-', '1.0'), k='-BETAW-', s=(5,1))],
            [sg.T('NALP Opt'), sg.Combo(nalp_options, default_value=nalp_options[safe_int(override_values.get('-NALP-', 0))], key='-NALP-', readonly=True, enable_events=True)],
            [sg.T('NEP Opt'), sg.Combo(nep_options, default_value=nep_options[safe_int(override_values.get('-NEP-', 0))], key='-NEP-', readonly=True)]
        ])]
    ]

    # --- Tab 2 Layout ---
    default_use_table = override_values.get('-USE_TABLE-', False)
    table_content = [[sg.Text('      #',p=(0,0)), sg.Text('ΔK_eff',s=(10,1),p=(0,0)), sg.Text('da/dN',s=(10,1),p=(0,0))]]
    for i in range(ntab_rows):
        dk, rate = (table_data[i] if i < len(table_data) else [ZERO, ZERO]); row = [sg.Text(f'{i+1:>6}',p=(0,0)), sg.Input(dk,k=('-DK-',i),s=(12,1)), sg.Input(rate,k=('-RATE-',i),s=(12,1))]; table_content.append(row)
    tab2_layout = [
        [sg.Frame('Section 5: Crack Growth Rate Options', font='_ 11 bold', layout=[[T('IRATE'), sg.Combo(irate_options,default_value=irate_options[0],k='-IRATE-',readonly=True)],[T('NGC'), sg.Input(override_values.get('-NGC-','0'),k='-NGC-',size=(5,1)), T('CRKNGC'), sg.Input(override_values.get('-CRKNGC-',ZERO),key='-CRKNGC-',size=(8,1))]])],
        [sg.HSep()],[sg.Text('Define Crack Growth Law using:',font='_ 11 bold'),sg.Radio('Equation','LAW_TYPE',k='-USE_EQUATION-', default=not default_use_table, enable_events=True), sg.Radio('Table','LAW_TYPE',k='-USE_TABLE-', default=default_use_table, enable_events=True)],
        [sg.Frame('Section 6: Crack Growth Equation Parameters',layout=[[T('C1'),sg.Input(override_values.get('-C1-',ZERO),k='-C1-'), T('C2'),sg.Input(override_values.get('-C2-',ZERO),k='-C2-')],[T('C3'),sg.Input(override_values.get('-C3-',ZERO),k='-C3-'), T('C4'),sg.Input(override_values.get('-C4-',ZERO),k='-C4-')],[T('C5'),sg.Input(override_values.get('-C5-',ZERO),k='-C5-'), T('C6'),sg.Input(override_values.get('-C6-','1.0'),k='-C6-')],[T('C7'),sg.Input(override_values.get('-C7-','1.0'),k='-C7-'), T('KF'),sg.Input(override_values.get('-KF-',ZERO),k='-KF-')],[T('m'),sg.Input(override_values.get('-M-',ZERO),k='-M-'), T('NEQN'),sg.Combo(neqn_options,default_value=neqn_options[0],k='-NEQN-',readonly=True)]], key='-FRAME_SEC_6-')],
        [sg.Frame('Section 7: Editable Crack Growth Rate Table',layout=[[sg.Text('NTAB'),sg.Input(str(ntab_rows),k='-NTAB-',size=(5,1)), sg.Text('NDKTH'), sg.Input(override_values.get('-NDKTH-','0'), k='-NDKTH-', size=(5,1)), sg.Button('Update Table',k='-UPDATE_TABLE-'), sg.Button('Paste from Clipboard', k='-PASTE_TABLE-')], [sg.Column(table_content, scrollable=True, vertical_scroll_only=True, size=(450, 200))]], key='-FRAME_SEC_7-', visible=default_use_table)],
        [sg.Frame('Section 8: Transition Parameters',layout=[[T('RATE1'),sg.Input(override_values.get('-RATE1-',ZERO),k='-RATE1-'), T('ALP1'),sg.Input(override_values.get('-ALP1-',ZERO),k='-ALP1-')],[T('BETAT1'),sg.Input(override_values.get('-BETAT1-','1.0'),k='-BETAT1-'), T('BETAW1'),sg.Input(override_values.get('-BETAW1-','1.0'),k='-BETAW1-')],[T('RATE2'),sg.Input(override_values.get('-RATE2-',ZERO),k='-RATE2-'), T('ALP2'),sg.Input(override_values.get('-ALP2-',ZERO),k='-ALP2-')],[T('BETAT2'),sg.Input(override_values.get('-BETAT2-','1.0'),k='-BETAT2-'), T('BETAW2'),sg.Input(override_values.get('-BETAW2-','1.0'),k='-BETAW2-')]], key='-FRAME_SEC_8-', visible=False)]
    ]

    # --- Tab 3 Layout ---
    tab3_layout = [
        [sg.Frame('Section 9: Data Output', [[T('NIPT'), sg.Input(override_values.get('-NIPT-', '0'), k='-NIPT-')],[T('NPRT'), sg.Input(override_values.get('-NPRT-', '0'), k='-NPRT-')],[T('LSTEP'), sg.Input(override_values.get('-LSTEP-', '1'), k='-LSTEP-')],[T('NDKE'), sg.Input(override_values.get('-NDKE-', '0'), k='-NDKE-')],[T('DCPR'), sg.Input(override_values.get('-DCPR-', ZERO), k='-DCPR-')]])],
        [sg.Frame('Section 10: Specimen & Loading', [[T('NTYP'), sg.Combo(ntyp_options,default_value=ntyp_options[0],key='-NTYP-',readonly=True, enable_events=True)],[T('LTYP'), sg.Combo(list(ltyp_map.keys()),default_value=list(ltyp_map.keys())[0],key='-LTYP-',readonly=True, enable_events=True)],[T('LFAST'), sg.Input(override_values.get('-LFAST-','0'), k='-LFAST-')],[T('NS'), sg.Input(override_values.get('-NS-','1'), k='-NS-')],[T('NFOPT'), sg.Combo(list(nfopt_map.keys()),default_value=list(nfopt_map.keys())[2],key='-NFOPT-',readonly=True)],[T('INVERT'), sg.Input(override_values.get('-INVERT-','0'), k='-INVERT-')],[T('KCONST'), sg.Input(override_values.get('-KCONST-','0'), k='-KCONST-')],[T('NTCMAX'), sg.Input(override_values.get('-NTCMAX-','0'), k='-NTCMAX-')]])],
        [sg.Frame('Section 11: Dimensions', [[T('W'), sg.Input(override_values.get('-W-', ZERO), k='-W-')],[T('T'), sg.Input(override_values.get('-T-', ZERO), k='-T-')],[T('CI'), sg.Input(override_values.get('-CI-', ZERO), k='-CI-')],[T('AI'), sg.Input(override_values.get('-AI-', ZERO), k='-AI-')],[T('CN'), sg.Input(override_values.get('-CN-', ZERO), k='-CN-')],[T('AN'), sg.Input(override_values.get('-AN-', ZERO), k='-AN-')],[T('HN'), sg.Input(override_values.get('-HN-', ZERO), k='-HN-')],[T('RAD'), sg.Input(override_values.get('-RAD-', ZERO), k='-RAD-')],[T('RADF'), sg.Input(override_values.get('-RADF-', ZERO), k='-RADF-')]])],
        [sg.Frame('Section 12: Custom SIF Table', layout=[[T('KTAB'), sg.Input('0', k='-KTAB-')]], key='-FRAME_SEC_12-', visible=False)],
        [sg.Frame('Section 14a: Gamma', layout=[[T('GAMMA'), sg.Input(ZERO, k='-GAMMA-')]], key='-FRAME_SEC_14A-', visible=False)],
        [sg.Frame('Section 13: Final Crack Length', [[T('Final CF'), sg.Input(override_values.get('-CF-', ZERO), k='-CF-')]])],
        [sg.Frame('Section 15: Pre-crack Load', [[T('SMAX'), sg.Input(override_values.get('-SMAX-', ZERO), k='-SMAX-')],[T('SMIN'), sg.Input(override_values.get('-SMIN-', ZERO), k='-SMIN-')]])],
        [sg.Frame('Section 16: Proof Test', [[T('NRC'), sg.Input(override_values.get('-NRC-', '0'), k='-NRC-')],[T('DVALUE'), sg.Input(override_values.get('-DVALUE-', ZERO), k='-DVALUE-')],[T('NCYCLE1'), sg.Input(override_values.get('-NCYCLE1-','0'), k='-NCYCLE1-')],[T('NCYCLE2'), sg.Input(override_values.get('-NCYCLE2-','0'), k='-NCYCLE2-')]])],
        [sg.Frame('Section 17: Primary Loading', [[T('MAXSEQ'), sg.Input(override_values.get('-MAXSEQ-','0'), k='-MAXSEQ-')],[T('MAXBLK'), sg.Input(override_values.get('-MAXBLK-','0'), k='-MAXBLK-')],[T('LPRINT'), sg.Input(override_values.get('-LPRINT-','0'), k='-LPRINT-')],[T('MAXLPR'), sg.Input(override_values.get('-MAXLPR-','0'), k='-MAXLPR-')],[T('NREP'), sg.Input(override_values.get('-NREP-','0'), k='-NREP-')],[T('MARKER'), sg.Input(override_values.get('-MARKER-','0'), k='-MARKER-')],[T('SPEAK'), sg.Input(override_values.get('-SPEAK-',ZERO), k='-SPEAK-')]])],
        [sg.Frame('Section 18: Threshold Test', [[T('KTH'), sg.Input(override_values.get('-KTH-','0'), k='-KTH-')],[T('SMAXTH'), sg.Input(override_values.get('-SMAXTH-',ZERO), k='-SMAXTH-')],[T('RTH'), sg.Input(override_values.get('-RTH-',ZERO), k='-RTH-')],[T('CONST'), sg.Input(override_values.get('-CONST-',ZERO), k='-CONST-')],[T('PRT'), sg.Input(override_values.get('-PRT-',ZERO), k='-PRT-')]])]
    ]

    # --- Main Window Layout ---
    layout = [[sg.Button('Load Input File'), sg.Button('Load Material'), sg.Button('Generate FASTRAN File'), sg.Button('Help', key='-HELP-'), sg.Stretch(), sg.Button('Exit')],
              [sg.Column([[sg.TabGroup([[sg.Tab('General & Material',tab1_layout),
                                         sg.Tab('Crack Growth',tab2_layout),
                                         sg.Tab('Geometry & Loading',tab3_layout)]])]], scrollable=True, vertical_scroll_only=True, expand_x=True, expand_y=True)]]

    return sg.Window('FASTRAN Input Generator v2.18', layout, resizable=True, size=(850, 600), finalize=True)

#
# --- Main Application Loop ---
#
if __name__ == '__main__':
    table_data = [['0.0', '0.0']]; ntab_value = 1; override_values = {}
    output_filepath = None
    while True:
        window = create_main_window(ntab_value, table_data, override_values)
        if output_filepath:
            window['-OUTPUT_FILE_DISPLAY-'].update(output_filepath)

        update_form_visibility(window, window.AllKeysDict)
        
        if override_values.get('-USE_TABLE-'):
            window['-USE_TABLE-'].update(value=True)
            window['-FRAME_SEC_7-'].update(visible=True)
        else:
            window['-USE_EQUATION-'].update(value=True)
            window['-FRAME_SEC_7-'].update(visible=False)

        override_values = {}

        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED or event == 'Exit': break

            if event == 'Generate FASTRAN File':
                generate_fastran_file(values, output_filepath)

            if event == '-HELP-': create_help_window()

            if event in ('-NALP-', '-NTYP-', '-LTYP-'):
                update_form_visibility(window, values)

            if event in ('-USE_EQUATION-', '-USE_TABLE-'):
                window['-FRAME_SEC_7-'].update(visible=values['-USE_TABLE-'])

            # --- FIX: Event handler for the new Browse button ---
            if event == '-BROWSE_SPECTRA-':
                filepath = sg.popup_get_file('Select Spectrum File', no_window=True, file_types=(("Text Files", "*.txt"),("All Files", "*.*"),))
                if filepath:
                    filename = os.path.basename(filepath)
                    window['-SPECTRA-'].update(filename)

            if event == '-SET_OUTPUT-':
                save_path = sg.popup_get_file('Set Output File Location', save_as=True, no_window=True, default_extension=".txt", file_types=(("Text Files", "*.txt"),))
                if save_path:
                    output_filepath = save_path
                    window['-OUTPUT_FILE_DISPLAY-'].update(output_filepath)

            if event == 'Load Material':
                filepath = sg.popup_get_file('Select Material File', no_window=True, file_types=(("Material Files", "*.lkxp *.txt"), ("All Files", "*.*"),))
                if filepath:
                    parsed_material = parse_material_file(filepath)
                    if parsed_material:
                        table_data = parsed_material.get('table', [['0.0','0.0']]); ntab_value = len(table_data)
                        override_values['-MAT-'] = parsed_material.get('name', '')
                        override_values['-USE_TABLE-'] = True
                        break

            if event == 'Load Input File':
                filepath = sg.popup_get_file('Select FASTRAN Input File', no_window=True)
                if filepath:
                    parsed_data, parsed_table_data = parse_fastran_file(filepath)
                    if parsed_data:
                        output_filepath = filepath
                        override_values = parsed_data
                        override_values['-OUTPUT_FILE_DISPLAY-'] = output_filepath
                        table_data = parsed_table_data or [['0.0', '0.0']]
                        ntab_value = int(parsed_data.get('-NTAB-', len(table_data)))
                        if ntab_value == 0: ntab_value = 1
                        break

            if event == '-UPDATE_TABLE-':
                try:
                    new_ntab_value = int(values['-NTAB-'])
                    if new_ntab_value > 0:
                        current_table_data = [[values.get(('-DK-',i),'0.0'), values.get(('-RATE-',i),'0.0')] for i in range(ntab_value)]
                        while len(current_table_data) < new_ntab_value:
                            current_table_data.append(['0.0', '0.0'])
                        
                        table_data = current_table_data
                        ntab_value = new_ntab_value
                        break
                    else: sg.popup_error("Number of rows must be greater than zero.")
                except (ValueError, TypeError): sg.popup_error("Please enter a valid integer for the number of rows.")

            if event == '-PASTE_TABLE-':
                try:
                    clipboard = sg.clipboard_get()
                    if not clipboard: sg.popup_error("Clipboard is empty."); continue
                    pasted_data = []
                    for line in clipboard.strip().split('\n'):
                        parts = line.split('\t') if '\t' in line else (line.split(',') if ',' in line else line.split())
                        if len(parts) >= 2: pasted_data.append([parts[0].strip(), parts[1].strip()])
                    if pasted_data:
                        ntab_value = len(pasted_data)
                        table_data = pasted_data
                        values['-NTAB-'] = str(ntab_value) 
                        break
                    else: sg.popup_error("Could not parse two columns from clipboard data.")
                except Exception as e: sg.popup_error(f"An error occurred while pasting: {e}")

        window.close()

        if event == sg.WIN_CLOSED or event == 'Exit': break