# config.py
"""
config.py
----------
The 'Knowledge Base' for the FASTRAN GUI.
Defines valid ranges, default values, special input rules, geometry mappings,
and failure mode descriptions. Enforces the logic found in FASTRAN Version 5.4 User Guide.
"""

# ------------------------------
# DEFAULT VALUES
# ------------------------------
DEFAULT_VALUES = {
    # File Management
    'OUTPUT_FILE': 'output.fou',
    'SPECTRA': 'cstamp.txt',
    'MAT': 'AL-7075-T6',

    # Geometry / Loading Selectors
    'NTYP': '1: Center Crack Tension M(T)',
    'NFOPT': '0: Constant Amplitude',

    # Material Properties
    'SYIELD': '500.0', 'SULT': '600.0', 'E': '70000.0', 'ETA': '0.0',
    'ALP': '1.0', 'BETAT': '1.0', 'BETAW': '1.0',
    'NALP': '0', 'NEP': '1',

    # Crack Growth (Equation)
    'CRKNGC': '0.0',
    'C1': '1.0E-10', 'C2': '3.0', 'C3': '0.0', 'C4': '0.0',
    'C5': '0.0', 'C6': '1.0', 'C7': '1.0',
    'KF': '0.0', 'M': '0.0',
    'NTAB': '0', 'KTAB': '0', 'IRATE': '1', 'NGC': '0', 'NEQN': '0', 'NDKTH': '0',

    # Variable Constraint (NALP=1)
    'RATE1': '1.E-9', 'RATE2': '1.E-5', 'RATE3': '1.0', 'RATE4': '1.0',
    'DK1': '1.0', 'DK2': '10.0', 'DK3': '100.0', 'DK4': '100.0',

    # General Options
    'LUNIT': '0', 'IUNIT': '0', 'NPLOT': '0', 'IPLOT': '0', 'NDK': '0',
    'NPRT': '0', 'NIPT': '1', 'DCPR': '0.0',

    # Constant Amplitude Loading (NFOPT=0)
    'SMAX': '100.0', 'R': '0.1', 'FW': '0.0', 'FH': '0.0',
    'INVERT': '0', 'HILO': '0', 'OMIT': '0.0', 'IOPEN': '1',

    # Spectrum Loading (NFOPT=2,3,4,5,8,9,10)
    'SPEAK': '1.0', 'SMEAN': '0.0', 'MAXSEQ': '1',

    # Block Loading (NFOPT=1)
    'MAXBLK': '1', 'SCALE': '1.0', 'LPRINT': '0', 'MAXLPR': '0',

    # Geometry Dimensions
    'CI': '2.0', 'CF': '20.0', 'CN': '1.0',
    'W': '50.0', 'B': '5.0', 'AN': '0.0',
    'AI': '0.0', 'AF': '0.0',

    # Special / Conditional Geometry Inputs
    'RADIUS': '0.0', 'HL': '0.0', 'HT': '0.0',
    'NDI': '0',
}

# ------------------------------
# GEOMETRY DEFINITIONS (NTYP)
# ------------------------------
# Maps NTYP code to display name, schematic image key, and extra required inputs (Section 14).
NTYP_DATA = {
    1:   {'name': 'Center Crack Tension M(T)',         'image': 'center_crack',    'special': []},
    2:   {'name': 'Compact Specimen C(T)',              'image': 'compact_tension', 'special': []},
    3:   {'name': 'Single-Edge Crack Tension SE(T)',   'image': 'single_edge',     'special': []},
    4:   {'name': 'Single-Edge Bend SE(B)',             'image': 'single_edge_bend','special': []},
    5:   {'name': 'Pressurized Cylinder (internal)',   'image': 'cylinder',        'special': ['RADIUS']},
    6:   {'name': 'Pressurized Cylinder (edge crack)', 'image': 'cylinder_edge',   'special': ['RADIUS']},
    7:   {'name': 'Through Crack at Hole',              'image': 'through_hole',    'special': ['RADIUS']},
    8:   {'name': 'Corner Crack at Hole (surface)',    'image': 'corner_hole',     'special': ['RADIUS']},
    9:   {'name': 'Through Crack at Hole (wide plate)','image': 'corner_hole',     'special': ['RADIUS']},
    10:  {'name': 'Surface Crack (Tension)',            'image': 'surface_crack',   'special': []},
    11:  {'name': 'Quarter-Elliptic Surface Crack',    'image': 'surface_crack',   'special': []},
    12:  {'name': 'Corner Crack',                       'image': 'corner_crack',    'special': []},
    -1:  {'name': 'Corner Crack at Hole (thru)',       'image': 'corner_hole',     'special': ['RADIUS']},
    -12: {'name': 'Lap-Splice Joint',                  'image': 'lap_splice',      'special': ['RADIUS']},
}

# ------------------------------
# LOADING DEFINITIONS (NFOPT)
# ------------------------------
# requires_spectrum: True → show spectrum file picker in Loading tab.
# requires_block: True → show Block Loading Editor button.
NFOPT_DATA = {
    0:  {'name': 'Constant Amplitude',     'requires_spectrum': False, 'requires_block': False, 'invert_label': 'Invert (0/1)'},
    1:  {'name': 'Block Loading',          'requires_spectrum': False, 'requires_block': True,  'invert_label': 'Invert (0/1)'},
    2:  {'name': 'TWIST (Transport)',      'requires_spectrum': True,  'requires_block': False, 'invert_label': 'Clip Level (1-3)'},
    3:  {'name': 'MINI-TWIST',             'requires_spectrum': True,  'requires_block': False, 'invert_label': 'Clip Level (1-3)'},
    4:  {'name': 'FALSTAFF (Fighter)',     'requires_spectrum': True,  'requires_block': False, 'invert_label': 'Invert (0=Ten, 1=Comp)'},
    5:  {'name': 'User Spectrum File',    'requires_spectrum': True,  'requires_block': False, 'invert_label': 'Invert (0/1)'},
    8:  {'name': 'Felix/28 (Helicopter)', 'requires_spectrum': True,  'requires_block': False, 'invert_label': 'Invert (0/1)'},
    9:  {'name': 'User Spectrum File 2',  'requires_spectrum': True,  'requires_block': False, 'invert_label': 'Invert (0/1)'},
    10: {'name': 'Standardized Spectrum', 'requires_spectrum': True,  'requires_block': False, 'invert_label': 'Invert (0/1)'},
}

# ------------------------------
# FAILURE MODES (Output Interpretation)
# ------------------------------
# Maps FASTRAN failure/stop codes to human-readable descriptions.
FAILURE_MODES = {
    None: "N/A",
    "0":  "Normal: Crack reached final size (CF)",
    "1":  "Fracture: KI exceeded fracture toughness (KF or KC)",
    "2":  "Net-Section Yielding: Applied stress exceeded material limit",
    "3":  "Max Cycles Reached: Analysis stopped at cycle limit",
    "4":  "Growth Arrested: dK below threshold, crack stopped growing",
    "5":  "Analysis Error: Check input data (stress, geometry, or material)",
}

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
# TOOLTIPS (hover help for input fields)
# ------------------------------
TOOLTIPS = {
    'NTYP':   'Specimen geometry. See FASTRAN User Guide Section 14 for full definitions.',
    'W':      'Specimen width (half-width for M(T)). Same units as CI/CF.',
    'B':      'Specimen thickness.',
    'CI':     'Initial crack length (or half-length). Must be < CF.',
    'CF':     'Final crack length at which analysis terminates. Must be > CI.',
    'CN':     'Notch/starter crack length. Set CN=CI if no pre-crack stage.',
    'AN':     'Notch depth (for surface/corner crack notches).',
    'AI':     'Initial crack depth for surface/corner crack geometries.',
    'RADIUS': 'Radius of hole or cylinder (required for hole/cylinder geometry types).',
    'SYIELD': '0.2% offset yield strength in the stress units selected.',
    'SULT':   'Ultimate tensile strength in the stress units selected.',
    'E':      "Young's modulus (elastic modulus).",
    'ETA':    "Poisson's ratio. Use 0.0 for plane-stress.",
    'ALP':    'Plastic constraint factor. 1.0 = plane-stress, ~2.5 = plane-strain.',
    'BETAT':  'Compressive constraint factor (ahead of crack tip). Typically 1.0.',
    'BETAW':  'Compressive constraint factor (crack wake). Typically 1.0.',
    'NALP':   '0 = Constant ALP. 1 = Variable (program adjusts with crack growth rate).',
    'NEP':    '0 = Elastic. 1 = Cyclic plasticity correction (recommended). 2 = Monotonic.',
    'IRATE':  '1 = Single law. 2 = Two independent laws. 4 = Small/large-crack transition.',
    'NGC':    'Enable small-to-large crack transition (IRATE=4 only). 0 = Off, 1 = On.',
    'CRKNGC': 'Crack size at which transition from small- to large-crack growth occurs.',
    'C1':     'Paris coefficient C1. da/dN = C1 · ΔKeff^C2',
    'C2':     'Paris exponent C2 (slope on log-log plot).',
    'C3':     'Baseline threshold ΔK. Use 0 to disable threshold.',
    'C4':     'R-ratio threshold modifier. ΔK₀ = C3 + C4·Kmax.',
    'C5':     'Cyclic fracture toughness (upper bound on ΔK).',
    'C6':     'Fracture power exponent. Controls sharpness of fracture end of curve.',
    'C7':     'Threshold power exponent. Controls sharpness of threshold knee.',
    'KF':     'Elastic-plastic fracture toughness. Use 0 if using C5.',
    'M':      'Fracture toughness exponent for KF.',
    'NTAB':   'Number of data points in tabular crack-growth input. 0 = use Paris equation.',
    'NDKTH':  '0 = direct table. 1 = FASTRAN tabular form. 2 = NASGRO tabular form.',
    'NEQN':   '0 = FASTRAN equation. 1 = NASGRO equation.',
    'NFOPT':  'Loading type. 0 = Constant Amplitude, 1 = Block, 2-10 = Spectra.',
    'SMAX':   'Maximum applied stress for constant-amplitude loading or pre-crack.',
    'R':      'Stress ratio R = Smin/Smax for constant-amplitude loading.',
    'SPEAK':  'Peak (maximum) stress in the spectrum. Scales normalized spectrum data.',
    'SMEAN':  'Mean stress (used by some standardized spectra such as TWIST).',
    'MAXSEQ': 'Number of spectrum sequences (flights/blocks) per analysis cycle.',
    'INVERT': 'Spectrum inversion flag. Meaning depends on NFOPT; see user guide.',
    'OMIT':   'Omit fraction: cycles below this fraction of peak stress are skipped.',
    'IOPEN':  '0 = fixed crack-opening, 1 = variable crack-opening (recommended).',
    'SPECTRA': 'Filename of the spectrum loading file (for NFOPT 2, 3, 4, 5, 8, 9, 10).',
    'NPRT':   'Print interval in cycles. 0 = print at every computation step.',
    'DCPR':   'Print interval by crack increment. Overrides NPRT if > 0.',
    'LUNIT':  '0 = keep units as-is. 1 = English→SI. 2 = SI→English.',
    'IUNIT':  '0 = stress in MPa (SI). 1 = stress in ksi (English).',
}
