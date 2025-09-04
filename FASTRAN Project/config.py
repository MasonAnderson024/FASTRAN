# config.py
"""
config.py
----------
Holds all static configuration data for the FASTRAN GUI. This includes:
- A dictionary of default values for all input fields.
- Mapping dictionaries (description -> FASTRAN code).
- Reverse mapping dictionaries (code -> description).
- Categories for organizing UI elements.

This module should contain no executable functions, only data constants.
"""

# ------------------------------
# DEFAULT VALUES FOR GUI STATE
# ------------------------------
# Defines the default state for a new or reset analysis.
DEFAULT_VALUES = {
    'OUTPUT_FILE': 'output.fou', 'SPECTRA': 'cstamp.txt', 'MAT': 'material name',
    'SYIELD': '0.0', 'SULT': '0.0', 'E': '0.0', 'ETA': '0.0',
    'ALP': '1.0', 'BETAT': '1.0', 'BETAW': '1.0', 'CRKNGC': '0.0',
    'C1': '0.0', 'C2': '0.0', 'C3': '0.0', 'C4': '0.0', 'C5': '0.0',
    'C6': '1.0', 'C7': '1.0', 'KF': '0.0', 'M': '0.0',
    'NTAB': '1', 'KTAB': '0', 'IRATE': '1', 'NGC': '0', 'NEQN': '0',
    'RATE1': '1.E-9', 'ALP1': '3.0', 'BETAT1': '1.0', 'BETAW1': '1.0',
    'RATE2': '1.E-6', 'ALP2': '1.0', 'BETAT2': '1.0', 'BETAW2': '1.0',
    'NIPT': '0', 'NPRT': '0', 'LSTEP': '1', 'DCPR': '0.0',
    'NS': '1', 'INVERT': '0', 'NRC': '0', 'NTYP': '1', 'LTYP': '0',
    'LFAST': '0', 'KCONST': '0', 'NTCMAX': '0', 'NDKTH': '0', 'NDKE': '0',
    'W': '0.0', 'T': '0.0', 'CI': '0.0', 'AI': '0.0', 'CN': '0.0', 'AN': '0.0',
    'HN': '0.0', 'RAD': '0.0', 'RADF': '0.0', 'CF': '0.0', 'NALP': '0', 'NEP': '1',
    'SMAX': '0.0', 'SMIN': '0.0', 'DVALUE': '0.0', 'KTH': '0',
    'NCYCLE1': '0', 'NCYCLE2': '0', 'NODKL': '0',
    'MAXSEQ': '0', 'MAXBLK': '0', 'LPRINT': '0', 'MAXLPR': '0',
    'NREP': '0', 'MARKER': '0', 'SPEAK': '0.0', 'SMEAN': '0.0',
    'SMAXP': '0.0', 'SMINP': '0.0', 'NCYCP': '1000',
    'SMAXTH': '0', 'RTH': '0', 'CONST': '0', 'PRT': '0',
    'SCALE': '1.0',
    'GAMMA': '0.0', 'RADIUS': '0.0', 'RIVETS': '0.0', 'RLF1': '0.5',
    'RLF2': '0.5', 'DELTA': '0.0'
}

# ------------------------------
# FASTRAN FAILURE CODES
# ------------------------------
# Maps the NFCODE from the output file to a user-friendly description.
# Source: FASTRAN Version 5.4-User Guide, page 63
FAILURE_MODES = {
    '0': "KMAX > C5 (Maximum stress intensity factor exceeded the cyclic fracture toughness)",
    '1': "CRACK DRIVE > MATERIAL RESISTANCE (Crack driving force exceeded material resistance)",
    '2': "KMAX > C5 (Maximum stress intensity factor exceeded the cyclic fracture toughness)",
    '3': "SMAX > 0.99*SFLOW (Maximum applied stress exceeded 99% of the material's flow stress)",
    '4': "KMAX > KIe (Maximum stress intensity factor exceeded the elastic SIF at failure)",
    '5': "CRACK LENGTH EXCEEDS WIDTH",
    '6': "CRACK LENGTH PLUS PLASTIC ZONE EXCEEDS WIDTH"
}

# ------------------------------
# MAPPING DICTIONARIES
# (Description-to-Code)
# ------------------------------

nalp_map = {'0: Constant': '0', '1: Variable': '1'}
nep_map = {'0: Elastic': '0', '1: Plasticity-Corrected': '1', '2: Closure Corrected': '2'}
neqn_map = {'0: FASTRAN Equation': '0', '1: NASGRO Equation': '1'}
ntyp_map = {
    'Surface Crack': '0',
    'Center Crack Tension': '1',
    'Compact C(T)': '2',
    'Single-Edge Crack': '3',
    'Single-Edge Bend': '4',
    'Pressurized Cylinder': '5',
    'Corner Crack (AGARD)': '6',
    'Corner Crack in Plate Under Tension': '7',
    'Double Edge Crack': '8',
    'One Corner Crack at Hole': '-1',
    'Two Corner Cracks at Hole': '-2',
    'Through Crack at Hole': '-3',
    'Two Through Cracks at Hole': '-4',
    'One Surface Crack at Hole': '-5',
    'Two Surface Cracks at Hole': '-6',
    'Surface Crack at Semi-Circular Edge Notch': '-7',
    'Through Crack at Semi-Circular Edge Notch': '-8',
    'Corner Crack at Semi-Circular Edge Notch': '-9',
    'Array of Symmetric Through Cracks Under Pin-Load': '-10',
    'Array of Symmetric Through Cracks Under S': '-11',
    'Lap-Splice Joint (Through)': '-12',
    'Lap-Splice Joint (Corner)': '-13',
    'Surface Crack at Semi-Circular Edge Notch Bend (t=B/2)': '-14',
    'Through Crack at Semi-Circular Edge Notch Bend (t=B)': '-15',
    'Custom SIF (no hole)': '99',
    'Custom SIF (at hole)': '-99'
}
ltyp_map = {'0: Tension': '0', '1: Bending': '1', '2: Combined': '2'}
nfopt_map = {
    '0: Constant-Amplitude': '0', '1: Variable/Block Loading': '1', '2: TWIST Spectrum': '2',
    '3: Mini-TWIST Spectrum': '3', '4: FALSTAFF Spectrum': '4', '5: Space Shuttle Spectrum': '5',
    '6: Gaussian Spectrum (Not Recommended)': '6', '7: Helicopter Spectra': '7',
    '8: File - List of Stress Points': '8', '9: File - Flight-by-Flight': '9', '10: File - Flight Schedule': '10'
}
irate_map = {'1: dc/dN=da/dN': '1', '2: Independent Curves': '2', '4: Small/Large Cracks': '4'}
ngc_map = {'0: Disable Transition': '0', '1: Enable Transition': '1'}
nodkl_map = {'0: No Rivet-Load Decay': '0', '1: Use Rivet-Load Decay': '1'}
ndkth_map = {'0: Direct Lookup': '0', '1: FASTRAN Form': '1', '2: NASGRO Form': '2'}
ndke_map = {'0: Print Elastic SIF': '0', '1: Print Effective SIF': '1'}
lfast_map = {
    '0: Normal Closure': '0', '1: Equivalent S\'o (SOBAR)': '1', '2: Linear Cumulative Dmg': '2',
    '3: Constant S\'o': '3', '4: Manual S\'o Ratio': '4'
}
kconst_map = {'0: Stress Loading': '0', '1: SIF Loading': '1'}
ntcmax_map = {'0: Input Constraint': '0', '1: Plane-Stress (1st cycle)': '1'}
kth_map = {
    '0: No Test': '0', '1: ASTM (K-gradient)': '1', '2: SIF Gradient': '2',
    '3: Step Loading': '3', '4: Kmax Controlled': '4'
}

# For organizing the NTYP dropdown menu
ntyp_categories = {
    "Standard Specimens": [
        'Surface Crack', 'Center Crack Tension', 'Compact C(T)',
        'Single-Edge Crack', 'Single-Edge Bend', 'Pressurized Cylinder',
        'Corner Crack (AGARD)', 'Corner Crack in Plate Under Tension', 'Double Edge Crack'
    ],
    "Cracks at Holes / Notches": [
        'One Corner Crack at Hole', 'Two Corner Cracks at Hole', 'Through Crack at Hole',
        'Two Through Cracks at Hole', 'One Surface Crack at Hole', 'Two Surface Cracks at Hole',
        'Surface Crack at Semi-Circular Edge Notch', 'Through Crack at Semi-Circular Edge Notch',
        'Corner Crack at Semi-Circular Edge Notch',
        'Surface Crack at Semi-Circular Edge Notch Bend (t=B/2)',
        'Through Crack at Semi-Circular Edge Notch Bend (t=B)'
    ],
    "Special / Custom": [
        'Array of Symmetric Through Cracks Under Pin-Load',
        'Array of Symmetric Through Cracks Under S',
        'Lap-Splice Joint (Through)', 'Lap-Splice Joint (Corner)',
        'Custom SIF (no hole)', 'Custom SIF (at hole)'
    ]
}

# ------------------------------
# REVERSE MAPPING DICTIONARIES
# (Code-to-Description)
# ------------------------------
_maps_to_reverse = [
    'nalp', 'nep', 'neqn', 'ntyp', 'ltyp', 'nfopt', 'irate', 'ngc',
    'nodkl', 'ndkth', 'ndke', 'lfast', 'kconst', 'ntcmax', 'kth'
]

for _map_name in _maps_to_reverse:
    _original_map = globals()[f"{_map_name}_map"]
    globals()[f"{_map_name}_rev_map"] = {v: k for k, v in _original_map.items()}