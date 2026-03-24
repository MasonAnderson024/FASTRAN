# config.py
"""
config.py
----------
The 'Knowledge Base' for the FASTRAN GUI.
Defines valid ranges, default values, special input rules, and geometry mappings.
This file enforces the logic found in the FASTRAN Version 5.4 User Guide.
"""

# ------------------------------
# DEFAULT VALUES
# ------------------------------
# These populate the GUI when a new project is created.
DEFAULT_VALUES = {
    # File Management
    'OUTPUT_FILE': 'output.fou', 
    'SPECTRA': 'cstamp.txt', 
    'MAT': 'AL-7075-T6',
    
    # [FIXED] These were missing and causing the KeyError
    'NTYP': '1: Center Crack Tension',
    'NFOPT': '1: Constant Amplitude',
    
    # Material Properties (Standard)
    'SYIELD': '500.0', 'SULT': '600.0', 'E': '70000.0', 'ETA': '0.0',
    'ALP': '1.0', 'BETAT': '1.0', 'BETAW': '1.0', 
    
    # Crack Growth (Paris / Table)
    'CRKNGC': '0.0',
    'C1': '1.0E-10', 'C2': '3.0', 'C3': '0.0', 'C4': '0.0', 
    'C5': '0.0', 'C6': '1.0', 'C7': '1.0', # Thresholds
    'KF': '0.0', 'M': '0.0',
    'NTAB': '0', 'KTAB': '0', 'IRATE': '1', 'NGC': '0', 'NEQN': '0',
    
    # Rate Constants (Optional advanced)
    'RATE1': '1.E-9', 'RATE2': '1.E-5', 'RATE3': '1.0', 'RATE4': '1.0',
    'DK1': '1.0', 'DK2': '10.0', 'DK3': '100.0', 'DK4': '100.0',
    
    # General Options
    'LUNIT': '0', 'IUNIT': '0', 'NPLOT': '0', 'IPLOT': '0', 'NDK': '0',
    
    # Loading
    'SMAX': '100.0', 'R': '0.1', 'FW': '0.0', 'FH': '0.0',
    'INVERT': '0', 'HILO': '0', 'OMIT': '0.0', 'IOPEN': '1',
    
    # Geometry Dimensions
    'CI': '2.0', 'CF': '20.0', 'CN': '1.0', 
    'W': '50.0', 'B': '5.0', 'AN': '0.0', 
    
    # Special / Conditional Inputs
    'RADIUS': '0.0', 'HL': '0.0', 'HT': '0.0',
    'NDI': '0', 'K': '0', 'Q': '0', 'F': '0'
}

# ------------------------------
# GEOMETRY DEFINITIONS (NTYP)
# ------------------------------
# Maps NTYP code to:
#   - Name: Display name for the GUI
#   - Image: Key for the visualization (GeometryCanvas)
#   - special: List of EXTRA inputs required by Section 14 of User Guide
NTYP_DATA = {
    1:  {'name': 'Center Crack Tension',    'image': 'center_crack',       'special': []},
    2:  {'name': 'Compact Specimen C(T)',   'image': 'compact_tension',    'special': []},
    3:  {'name': 'Single-Edge Crack',       'image': 'single_edge',        'special': []},
    4:  {'name': 'Single-Edge Bend',        'image': 'single_edge_bend',   'special': []},
    5:  {'name': 'Pressurized Cylinder',    'image': 'cylinder',           'special': ['RADIUS']},
    -1: {'name': 'Corner Crack at Hole',    'image': 'corner_hole',        'special': []},
    
    # Complex Types (Examples)
    11: {'name': 'Surface Crack',           'image': 'surface_crack',      'special': []},
    12: {'name': 'Corner Crack',            'image': 'corner_crack',       'special': []},
    -12:{'name': 'Lap-Splice Joint',        'image': 'lap_splice',         'special': ['RIVETS']}, 
}

# ------------------------------
# LOADING DEFINITIONS (NFOPT)
# ------------------------------
# Maps NFOPT to behavior rules.
# - requires_spectrum: If True, enables file picker.
# - invert_label: Changes the label for the "INVERT" field to be context-aware.
NFOPT_DATA = {
    1: {'name': 'Constant Amplitude',   'requires_spectrum': False, 'invert_label': 'Invert (0/1)'},
    2: {'name': 'TWIST (Transport)',    'requires_spectrum': True,  'invert_label': 'Clip Level (1-3)'},
    3: {'name': 'MINI-TWIST',           'requires_spectrum': True,  'invert_label': 'Clip Level (1-3)'},
    4: {'name': 'FALSTAFF (Fighter)',   'requires_spectrum': True,  'invert_label': 'Invert (0=Ten, 1=Comp)'},
    5: {'name': 'Spectrum File (User)', 'requires_spectrum': True,  'invert_label': 'Invert (0/1)'},
    8: {'name': 'Felix/28 (Helicopter)','requires_spectrum': True,  'invert_label': 'Invert (0/1)'},
}

# ------------------------------
# DROPDOWN LIST GENERATORS
# ------------------------------
# Used by the GUI to populate Comboboxes. 
# Format: "ID: Description"
GEOMETRY_OPTIONS = [f"{k}: {v['name']}" for k, v in NTYP_DATA.items()]
LOADING_OPTIONS = [f"{k}: {v['name']}" for k, v in NFOPT_DATA.items()]