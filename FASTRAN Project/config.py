# config.py
"""
config.py
----------
The 'Knowledge Base' for the FASTRAN GUI.
Defines valid ranges, default values, special input rules, geometry mappings,
and failure mode descriptions. Based on FASTRAN Version 5.4/5.78f User Guide.
"""

# ------------------------------
# DEFAULT VALUES
# ------------------------------
DEFAULT_VALUES = {
    # File Management
    'OUTPUT_FILE': 'output.fou',
    'SPECTRA': 'cstamp.txt',
    'MAT': 'AL-7075-T6',
    'TITLE': 'FASTRAN Analysis',

    # Geometry / Loading Selectors
    'NTYP': '1: Center Crack Tension M(T)',
    'NFOPT': '0: Constant Amplitude',

    # Material Properties (Section 4)
    'SYIELD': '500.0', 'SULT': '600.0', 'E': '70000.0', 'ETA': '0.0',
    'ALP': '1.0', 'BETAT': '1.0', 'BETAW': '1.0',
    'NALP': '0', 'NEP': '1',

    # Crack Growth Options (Section 5)
    'IRATE': '1', 'NGC': '0', 'CRKNGC': '0.0',

    # Crack Growth Equation (Section 6 — repeated IRATE times)
    'C1': '1.0E-10', 'C2': '3.0', 'C3': '0.0', 'C4': '0.0',
    'C5': '0.0', 'C6': '1.0', 'C7': '1.0',
    'KF': '0.0', 'M': '0.0', 'NEQN': '0',

    # Tabular Crack Growth (Section 7a)
    'NTAB': '0', 'NDKTH': '0', 'KTAB': '0',

    # Variable Constraint Transition (Section 8 — NALP=1 only)
    'RATE1': '1.0E-7', 'ALP1': '2.0', 'BETAT1': '1.0', 'BETAW1': '1.0',
    'RATE2': '2.5E-6', 'ALP2': '1.0', 'BETAT2': '1.0', 'BETAW2': '1.0',

    # Output Options (Section 9)
    'NIPT': '0', 'NPRT': '-50', 'LSTEP': '1', 'NDKE': '1', 'DCPR': '0.00005',

    # Specimen Type and Loading (Section 10)
    'LTYP': '0', 'LFAST': '0', 'NS': '2',
    'INVERT': '0', 'KCONST': '0', 'NTCMAX': '0',

    # Specimen Dimensions (Section 11): W T CI AI CN AN HN RAD RADF
    'W': '50.0',
    'B': '5.0',   # GUI label; maps to T in input file
    'T': '5.0',   # FASTRAN thickness variable (=B for most configurations)
    'CI': '2.0', 'AI': '0.0',
    'CN': '1.0', 'AN': '0.0',
    'HN': '0.0', 'RAD': '0.0', 'RADF': '0.0',

    # Final Crack Length (Section 13)
    'CF': '20.0',

    # Special Inputs (Section 14 — conditional on NTYP/LTYP)
    'GAMMA': '0.0',    # Sb/S ratio (NTYP=0,7 with LTYP=2; NTYP=-10)
    'XKT': '3.17',     # Stress concentration factor (NTYP=-7,-8,-9)
    'NBCF': '0',       # Boundary correction factor type (NTYP=-7,-8,-9)
    'RADIUS': '0.0',   # Cylinder radius (NTYP=5)
    'RIVETS': '0.0',   # Rivet pitch (NTYP=-12,-13)
    'RLF1': '0.5',     # Rivet load factor (NTYP=-12,-13)
    'RLF2': '0.5',     # By-pass load factor (NTYP=-12,-13)
    'NODKL': '0',      # Rivet-load decay flag (NTYP=-12,-13)
    'DELTA': '0.0',    # Rivet interference (NTYP=-12,-13)

    # Pre-cracking Loading (Section 15): SMAX SMIN
    'SMAX': '100.0', 'R': '0.1',   # SMIN computed as SMAX * R

    # Proof Test / Constant So (Section 16)
    'NRC': '0', 'DVALUE': '0.0', 'NCYCLE1': '0', 'NCYCLE2': '0',

    # Primary Fatigue Loading (Section 17 — used across all NFOPT types)
    'MAXSEQ': '1', 'MAXBLK': '1', 'LPRINT': '0', 'MAXLPR': '0',
    'SCALE': '1.0',
    'SPEAK': '1.0', 'SMEAN': '0.0',
    'NREP': '0', 'MARKER': '0',   # NFOPT=8 only

    # Threshold Test (Section 18)
    'KTH': '0', 'SMAXTH': '0.0', 'RTH': '0.0', 'CONST': '0.0', 'PRT': '0.0',

    # Unit/output flags (not part of main 18-section input format)
    'LUNIT': '0', 'IUNIT': '0', 'NPLOT': '0', 'IPLOT': '0',

    # Legacy / GUI-only fields kept for backward compatibility
    'FW': '0.0', 'FH': '0.0',   # not in FASTRAN spec

    # Block loading data (NFOPT=1) — JSON-encoded list of block dicts stored
    # as a StringVar so the parser can read it without touching the filesystem.
    # Each block: {'nsq': str, 'levels': [[smaxp, sminp, ncycp], ...]}
    'BLOCK_DATA': '[]',
}


# ------------------------------
# GEOMETRY DEFINITIONS (NTYP)
# ------------------------------
# special: extra required inputs for Section 14 (shown dynamically in GUI).
# Note: NTYP=0 and NTYP=7 need GAMMA only when LTYP=2 (handled in parsers.py).
NTYP_DATA = {
    # Standard crack configurations (NTYP >= 0)
    0:   {'name': 'Surface Crack (Tension/Bending)',                   'image': 'surface_crack',       'special': []},
    1:   {'name': 'Center Crack Tension M(T)',                         'image': 'center_crack',         'special': []},
    2:   {'name': 'Compact C(T) or ESE(T) Specimen',                   'image': 'compact_tension',      'special': []},
    3:   {'name': 'Single-Edge Crack Tension SE(T)',                   'image': 'single_edge',          'special': []},
    4:   {'name': 'Single-Edge Crack Bend SE(B)',                      'image': 'single_edge_bend',     'special': []},
    5:   {'name': 'Through Crack in Pressurized Cylinder',             'image': 'cylinder',             'special': ['RADIUS']},
    6:   {'name': 'Corner Crack (a=c) in Square-Bar (AGARD)',          'image': 'corner_bar',           'special': []},
    7:   {'name': 'Corner Crack in Plate (Tension/Bending)',           'image': 'corner_plate',         'special': []},
    8:   {'name': 'Double-Edge Crack Tension D(T)',                    'image': 'double_edge',          'special': []},
    99:  {'name': 'User-Defined Geometry (Fc vs c/w table)',           'image': 'user_geom',            'special': []},
    # Cracks from holes or notches (NTYP < 0)
    -1:  {'name': 'One Corner Crack at Hole (Tension/Bending)',        'image': 'corner_hole_1',        'special': []},
    -2:  {'name': 'Two Corner Cracks at Hole (Tension/Bending)',       'image': 'corner_hole_2',        'special': []},
    -3:  {'name': 'One Through Crack at Hole',                         'image': 'through_hole_1',       'special': []},
    -4:  {'name': 'Two Through Cracks at Hole',                        'image': 'through_hole_2',       'special': []},
    -5:  {'name': 'One Surface Crack at Center of Hole',               'image': 'surface_hole_1',       'special': []},
    -6:  {'name': 'Two Surface Cracks at Center of Hole',              'image': 'surface_hole_2',       'special': []},
    -7:  {'name': 'Surface Crack at Semi-Circular Edge Notch',         'image': 'notch_surface',        'special': ['XKT', 'NBCF']},
    -8:  {'name': 'Through Crack at Semi-Circular Edge Notch',         'image': 'notch_through',        'special': ['XKT', 'NBCF']},
    -9:  {'name': 'Corner Crack at Semi-Circular Edge Notch',          'image': 'notch_corner',         'special': ['XKT', 'NBCF']},
    -10: {'name': 'Through Cracks at Holes (Pin Load + Moment γ)', 'image': 'pin_through',         'special': ['GAMMA']},
    -11: {'name': 'Periodic Through Cracks at Holes',                  'image': 'periodic_through',     'special': []},
    -12: {'name': 'Lap-Splice Joint — Through Cracks',                 'image': 'lap_splice_thru',      'special': ['RIVETS', 'RLF1', 'RLF2', 'NODKL', 'GAMMA', 'DELTA']},
    -13: {'name': 'Lap-Splice Joint — Corner Cracks',                  'image': 'lap_splice_corner',    'special': ['RIVETS', 'RLF1', 'RLF2', 'NODKL', 'GAMMA', 'DELTA']},
    -14: {'name': 'Surface Crack at Edge Notch Bend',                  'image': 'notch_bend_surface',   'special': []},
    -15: {'name': 'Through Crack at Edge Notch Bend',                  'image': 'notch_bend_through',   'special': []},
    -99: {'name': 'User-Defined Crack at Hole/Notch (fct vs crk/w)',   'image': 'user_geom_hole',       'special': []},
}


# ------------------------------
# LOADING DEFINITIONS (NFOPT)
# ------------------------------
NFOPT_DATA = {
    0:  {'name': 'Constant Amplitude',
         'requires_spectrum': False, 'requires_block': False,
         'invert_label': 'Invert (0/1)'},
    1:  {'name': 'Block / Flight Loading (User Input)',
         'requires_spectrum': False, 'requires_block': True,
         'invert_label': 'Invert (0/1)'},
    2:  {'name': 'TWIST Transport Spectrum',
         'requires_spectrum': True,  'requires_block': False,
         'invert_label': 'Clip Level (0=None, 2-5=Level II-V)'},
    3:  {'name': 'Mini-TWIST Spectrum',
         'requires_spectrum': True,  'requires_block': False,
         'invert_label': 'Clip Level (0=None, 2-5=Level II-V)'},
    4:  {'name': 'FALSTAFF Fighter Spectrum',
         'requires_spectrum': True,  'requires_block': False,
         'invert_label': 'Invert (0=Normal, 1=Inverted)'},
    5:  {'name': 'Space Shuttle Load Sequence',
         'requires_spectrum': True,  'requires_block': False,
         'invert_label': 'Invert (0=Full spectrum, 1=Short spectrum)'},
    6:  {'name': 'Gaussian Spectrum (I=0.99) — Not Allowed in current version',
         'requires_spectrum': False, 'requires_block': False,
         'invert_label': 'N/A'},
    7:  {'name': 'Helicopter Spectrum (Felix-28 / Helix-32)',
         'requires_spectrum': True,  'requires_block': False,
         'invert_label': 'Invert (1=Felix-28, 2=Helix-32)'},
    8:  {'name': 'Spectrum: List of Stress Points (file)',
         'requires_spectrum': True,  'requires_block': False,
         'invert_label': 'Invert (0=Max/Min order, 1=Min/Max order)'},
    9:  {'name': 'Spectrum: Flight-by-Flight (file)',
         'requires_spectrum': True,  'requires_block': False,
         'invert_label': 'Invert (0=Max/Min order, 1=Min/Max order)'},
    10: {'name': 'Spectrum: Flight Schedule (file)',
         'requires_spectrum': True,  'requires_block': False,
         'invert_label': 'Invert (not used for NFOPT=10)'},
}


# ------------------------------
# FAILURE CODES (NFCODE — Output Interpretation)
# ------------------------------
FAILURE_MODES = {
    None: 'N/A',
    '0':  'KMAX > C5 — cyclic fracture toughness exceeded',
    '1':  'Crack drive > material resistance (dKeff-rate curve)',
    '2':  'KMAX > C5 — fracture (second check)',
    '3':  'Max applied stress > 0.99 × SFLOW — net-section yielding',
    '4':  'KMAX > KIe — elastic-plastic fracture toughness exceeded',
    '5':  'Crack length exceeds specimen width (W)',
    '6':  'Crack length + plastic zone exceeds specimen width (W)',
}


# ------------------------------
# LFAST OPTIONS (Crack-Closure Model)
# ------------------------------
LFAST_DATA = {
    0: "0 — Normal crack-closure model (computed S'o)",
    1: "1 — Equivalent crack-opening stress (SOBAR) for c > cmax (faster)",
    2: "2 — Linear cumulative damage using constant-amplitude S'o equation",
    3: "3 — Constant S'o computed from block min/max stresses",
    4: "4 — Constant S'o from manual input (set NRC=-1, DVALUE=S'o/Smax)",
}


# ------------------------------
# LTYP OPTIONS (Loading Sub-type)
# ------------------------------
LTYP_DATA = {
    0: '0 — Remote tension (input S)',
    1: '1 — Remote bending (input outer-fiber stress Sb)',
    2: '2 — Combined tension + bending (input S and γ = Sb/S)',
}


# ------------------------------
# KCONST OPTIONS (Loading Quantity)
# ------------------------------
KCONST_DATA = {
    0: '0 — Apply external stress as loading (normal)',
    1: '1 — Apply K (stress-intensity factor) as loading — NTYP=1 or 2 only',
}


# ------------------------------
# DROPDOWN OPTION LISTS
# Option strings use "N: label" (colon) format so parsers/importers can
# extract the integer prefix the same way they do for NTYP / NFOPT.
# ------------------------------
def _to_option_str(k, raw):
    """Convert 'N — text' form (em-dash) to 'N: text' form (colon)."""
    body = raw.split('—', 1)[1].strip() if '—' in raw else raw
    return f"{k}: {body}"


LFAST_OPTIONS  = [_to_option_str(k, v) for k, v in sorted(LFAST_DATA.items())]
LTYP_OPTIONS   = [_to_option_str(k, v) for k, v in sorted(LTYP_DATA.items())]
KCONST_OPTIONS = [_to_option_str(k, v) for k, v in sorted(KCONST_DATA.items())]


def label_for_int(value, options):
    """Look up the 'N: label' form matching the integer value. Falls back to str(value)."""
    try:
        n = int(value)
    except (ValueError, TypeError):
        return str(value)
    for opt in options:
        try:
            if int(opt.split(':', 1)[0]) == n:
                return opt
        except ValueError:
            continue
    return str(value)


# Promote the option-0 label as the GUI default for the three combobox-driven
# Section 10 fields (overrides the bare-integer defaults written above).
DEFAULT_VALUES['LTYP']   = LTYP_OPTIONS[0]
DEFAULT_VALUES['LFAST']  = LFAST_OPTIONS[0]
DEFAULT_VALUES['KCONST'] = KCONST_OPTIONS[0]


# ------------------------------
# DROPDOWN LIST GENERATORS
# ------------------------------
GEOMETRY_OPTIONS = [
    f"{k}: {v['name']}"
    for k, v in sorted(NTYP_DATA.items(), key=lambda x: (x[0] < 0, abs(x[0])))
]
LOADING_OPTIONS = [
    f"{k}: {v['name']}"
    for k, v in sorted(NFOPT_DATA.items())
]


# ------------------------------
# TOOLTIPS
# ------------------------------
TOOLTIPS = {
    'NTYP':    'Specimen geometry type. See FASTRAN User Guide Section 10 for definitions.',
    'W':       'Half-width (or full width for NTYP=2,3,6,7,-7,-8,-9). Same units as CI/CF.',
    'B':       'Full plate/sheet thickness (GUI label). Maps to T (specimen thickness) in input file.',
    'T':       'Specimen thickness t (one-half thickness for NTYP=-5,-6,-7,-14).',
    'CI':      'Initial crack length c*i (or ci+r for hole/notch types). Must be < CF.',
    'CF':      'Final crack length at which analysis terminates. Must be > CI.',
    'CN':      'Starter notch length c*n (or cn+r for hole/notch types). Set CN=CI if no pre-crack.',
    'AN':      'Starter notch depth an (surface/corner crack notches).',
    'AI':      'Initial crack depth ai. Auto-set to T for through cracks.',
    'HN':      'Starter notch half-height hn.',
    'RAD':     'Radius of circular hole (at centerline) or semi-circular edge notch.',
    'RADF':    'Fastener radius. 0=open hole. RAD=tight fastener.',
    'SYIELD':  '0.2% offset yield strength in the selected stress units.',
    'SULT':    'Ultimate tensile strength in the selected stress units.',
    'E':       "Young's modulus (elastic modulus).",
    'ETA':     "0 for plane-stress. Set to Poisson's ratio for plane-strain.",
    'ALP':     'Plastic constraint factor. 1.0=plane-stress, 1.73=Irwin plane-strain, 3.0=plane-strain.',
    'BETAT':   'Compressive constraint factor at crack tip (intact material). Typically 1.0.',
    'BETAW':   'Compressive constraint factor along crack wake surface. Typically 1.0.',
    'NALP':    '0=Constant ALP. 1=Variable ALP (program adjusts with crack growth rate).',
    'NEP':     '0=Elastic dKeff. 1=Elastic-plastic cyclic plastic zone (recommended). 2=Monotonic zone.',
    'IRATE':   '1=Single law. 2=Two independent laws (c- and a-directions). 4=Small/large-crack transition.',
    'NGC':     '0=Original code. 1=Small-to-large crack transition (IRATE=4 only).',
    'CRKNGC':  'Transition crack size. c or a < CRKNGC uses small-crack law; >= uses large-crack. Typical: 0.00025 m or 0.01 in.',
    'C1':      'Paris coefficient C1. dc/dN = C1 · ΔKeff^C2 · [threshold term] · [fracture term].',
    'C2':      'Paris exponent C2 (slope on log-log plot).',
    'C3':      'Threshold baseline constant. ΔKo = C3·(1−R)^C4 for +C4; or C3·(1+C4·R) for −C4. Use 0 to disable.',
    'C4':      'Threshold R-ratio modifier. Positive C4: ΔKo = C3·(1−R)^C4. Negative C4: ΔKo = C3·(1+C4·R). Use 0 to disable.',
    'C5':      'Cyclic fracture toughness. Set to 9999+ to use KIe from Kf/m instead.',
    'C6':      'Power on fracture term (controls sharpness of upper fracture cutoff).',
    'C7':      'Power on threshold term (controls sharpness of threshold knee).',
    'KF':      'Elastic-plastic fracture toughness Kf. Used with m to compute KIe.',
    'M':       'Fracture toughness parameter. 0=brittle (LEFM), 1=fully ductile.',
    'NTAB':    'Number of tabular crack-growth data points. 0=use Paris equation.',
    'NDKTH':   '0=table dc/dN vs ΔKeff. 1=FASTRAN tabular form. 2=NASGRO tabular form.',
    'NEQN':    '0=FASTRAN equation. 1=NASGRO equation.',
    'LTYP':    '0=Remote tension (S). 1=Remote bending (Sb). 2=Combined tension+bending (S and γ). Applies to NTYP 0, 2, 7, -1, -2.',
    'LFAST':   "0=Normal closure model. 1=SOBAR equivalent (faster). 2=Linear damage (S'o eqn). 3=Constant S'o (block). 4=Manual S'o.",
    'NS':      'Number of notch elements. Minimum 1 for notch only; minimum 2 for notch at hole.',
    'KCONST':  '0=Apply stress loading. 1=Apply K directly (NTYP=1 or 2, NFOPT<=1, LFAST=0).',
    'NTCMAX':  '0=Normal notch constraint. 1=First cycle is plane-stress (ALP=1) for negative NTYP.',
    'NFOPT':   'Loading type. 0=Constant Amplitude, 1=Block, 2-10=Spectrum files.',
    'SMAX':    'Maximum applied stress for pre-cracking (Section 15). Also used as primary loading stress for NFOPT=0.',
    'R':       'Stress ratio R=Smin/Smax. Smin is computed as SMAX × R.',
    'INVERT':  'Spectrum modification flag. Meaning depends on NFOPT; see user guide.',
    'SPEAK':   'Peak scaling stress for spectrum loading (NFOPT 4-10).',
    'SMEAN':   'Mean stress for TWIST/Mini-TWIST/Gaussian spectra (NFOPT=2,3,6).',
    'MAXSEQ':  'Total number of blocks/flights in the repeated sequence.',
    'MAXBLK':  'Number of different blocks/flights in the load history.',
    'SCALE':   'Scale factor applied to all block/flight stresses (NFOPT=0 or 1).',
    'LPRINT':  '0=No internal spectrum print. 1=Block/flight numbers. 2=Full details.',
    'GAMMA':   'Ratio of outer-fiber bending stress to remote tensile stress (γ=Sb/S). Required for NTYP=0,7 with LTYP=2, or NTYP=-10.',
    'XKT':     'Elastic stress concentration factor Kt. Required for NTYP=-7,-8,-9.',
    'NBCF':    'BCF type: 0=Uniform stress (h/w=2); 1=Disp h/w=1.5; 2=Disp h/w=2; 3=Disp h/w=3. For NTYP=-7,-8,-9.',
    'RADIUS':  'Radius of pressurized cylinder. Required for NTYP=5.',
    'RIVETS':  'Rivet pitch/spacing (center-to-center). Required for NTYP=-12,-13.',
    'RLF1':    'Rivet load factor at primary hole (0 to 1). RLF1 + RLF2 must equal 1.',
    'RLF2':    'By-pass load factor (1 to 0). RLF1 + RLF2 must equal 1.',
    'NODKL':   '0=No rivet-load decay as crack grows. 1=Typical decay equation.',
    'DELTA':   'Rivet interference (change in rivet radius). For NTYP=-12,-13.',
    'NIPT':    '0=Internal print off. >0=Print every NIPT crack-growth increments.',
    'NPRT':    'Cycles output interval. Negative value: output at DCPR crack increment.',
    'LSTEP':   'Load steps from min to max during NIPT printout. Usually 1.',
    'NDKE':    '0=Print elastic ΔK and rates. 1=Print effective ΔK and rates.',
    'DCPR':    'Crack-growth increment for output printing when NPRT < 0.',
    'NRC':     "0=Normal. -1=Manual S'o/Smax input (LFAST=4, DVALUE=S'o/Smax).",
    'DVALUE':  "Manual crack-opening stress ratio S'o/Smax (for NRC=-1, LFAST=4 option).",
    'KTH':     '0=No threshold test. 1=ASTM practice. 2=ΔK gradient. 3=Step load. 4=Kmax test. (NTYP=1, NFOPT=0, LFAST=0 only.)',
    'SPECTRA': 'Filename of the spectrum loading file (for NFOPT=5,8,9,10; use dummy file for others).',
    'LUNIT':   '0=Keep units. 1=English→SI. 2=SI→English.',
    'IUNIT':   '0=SI (MPa, m). 1=English (ksi, inches).',
}
