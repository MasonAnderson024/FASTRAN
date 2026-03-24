# importers.py
"""
importers.py
------------
Legacy Data Importer for FASTRAN GUI.

Responsibilities:
1. Parsing: Reads raw text FASTRAN input files (positional format).
2. Mapping: Converts legacy numeric codes (e.g., NTYP=1) into GUI-friendly 
   string selections (e.g., "1: Center Crack Tension").
3. Logic: Handles conditional lines (Section 14 Special Inputs) automatically.
"""

import config
import os

def parse_fastran_input(filepath):
    """
    Reads a legacy input file and returns a dictionary of values
    mapped to the GUI's variable names.

    Args:
        filepath (str): Path to the legacy file.

    Returns:
        tuple: (Success (bool), Result (dict or error string))
    """
    data = {}
    
    if not os.path.exists(filepath):
        return False, "File not found."

    try:
        with open(filepath, 'r') as f:
            # Read non-empty lines
            lines = [line.strip() for line in f if line.strip()]

        if len(lines) < 8:
            return False, "File is too short to be a valid FASTRAN input."

        # --------------------------------------------------------
        # LINE 1: Title (Ignored by GUI, but good for validation)
        # --------------------------------------------------------
        # title = lines[0]

        # --------------------------------------------------------
        # LINE 2: Units & Plotting
        # Format: LUNIT IUNIT NPLOT IPLOT
        # --------------------------------------------------------
        parts = lines[1].split()
        if len(parts) >= 4:
            data['LUNIT'] = parts[0]
            data['IUNIT'] = parts[1]
            data['NPLOT'] = parts[2]
            data['IPLOT'] = parts[3]

        # --------------------------------------------------------
        # LINE 3: Geometry Type & Material Name
        # Format: NTYP MAT_NAME (MAT can contain spaces)
        # --------------------------------------------------------
        line3_parts = lines[2].split(maxsplit=1)
        try:
            ntyp_id = int(line3_parts[0])
            
            # Map ID to Full String from Config
            # e.g. Maps "1" -> "1: Center Crack Tension"
            matching_opt = next((opt for opt in config.GEOMETRY_OPTIONS if opt.startswith(f"{ntyp_id}:")), None)
            data['NTYP'] = matching_opt if matching_opt else f"{ntyp_id}: Unknown Legacy Type"
            
            if len(line3_parts) > 1:
                data['MAT'] = line3_parts[1]
        except ValueError:
            return False, f"Invalid NTYP on line 3: {lines[2]}"

        # --------------------------------------------------------
        # LINE 4: Mechanical Props
        # Format: SYIELD SULT E ETA ALP BETAT BETAW
        # --------------------------------------------------------
        parts = lines[3].split()
        keys = ['SYIELD', 'SULT', 'E', 'ETA', 'ALP', 'BETAT', 'BETAW']
        for i, key in enumerate(keys):
            if i < len(parts): data[key] = parts[i]

        # --------------------------------------------------------
        # LINE 5: Crack Growth Options
        # Format: NTAB KTAB IRATE NGC NEQN
        # --------------------------------------------------------
        parts = lines[4].split()
        if len(parts) >= 5:
            data['NTAB'] = parts[0]
            data['KTAB'] = parts[1]
            data['IRATE'] = parts[2]
            data['NGC'] = parts[3]
            data['NEQN'] = parts[4]

        # --------------------------------------------------------
        # CONDITIONAL LINES: Paris Constants
        # If NTAB=0, lines 6 and 7 contain constants.
        # If NTAB>0, these lines might be skipped or point to tables.
        # Standard FASTRAN usually includes them even if NTAB>0, but ignored.
        # We assume standard structure.
        # --------------------------------------------------------
        current_line_idx = 5
        ntab = int(data.get('NTAB', 1))
        
        # We try to read them if available, usually lines 6 & 7
        if current_line_idx < len(lines):
            # Line 6: C1 C2 C3 C4
            parts = lines[current_line_idx].split()
            for i, k in enumerate(['C1', 'C2', 'C3', 'C4']):
                if i < len(parts): data[k] = parts[i]
            current_line_idx += 1
            
        if current_line_idx < len(lines):
            # Line 7: C5 C6 C7 (Thresholds)
            parts = lines[current_line_idx].split()
            for i, k in enumerate(['C5', 'C6', 'C7']):
                if i < len(parts): data[k] = parts[i]
            current_line_idx += 1

        # --------------------------------------------------------
        # CONDITIONAL LINE: Special Geometry Inputs (Section 14)
        # Check config to see if this NTYP expects extra lines
        # --------------------------------------------------------
        rules = config.NTYP_DATA.get(ntyp_id, {})
        specials = rules.get('special', [])
        
        if specials and current_line_idx < len(lines):
            # Read the special line
            special_line = lines[current_line_idx]
            parts = special_line.split()
            
            # Map parts to special keys defined in config
            for i, req_key in enumerate(specials):
                if i < len(parts): data[req_key] = parts[i]
            
            current_line_idx += 1

        # --------------------------------------------------------
        # LOADING LINE
        # Format: NFOPT SMAX R FW FH ...
        # --------------------------------------------------------
        if current_line_idx < len(lines):
            parts = lines[current_line_idx].split()
            
            try:
                nfopt_id = int(parts[0])
                # Map to GUI string
                matching_opt = next((opt for opt in config.LOADING_OPTIONS if opt.startswith(f"{nfopt_id}:")), None)
                data['NFOPT'] = matching_opt if matching_opt else str(nfopt_id)

                # Remaining Loading Parameters
                keys = ['SMAX', 'R', 'FW', 'FH', 'INVERT', 'OMIT', 'IOPEN']
                # Skip the first part (NFOPT)
                for i, key in enumerate(keys):
                    if i+1 < len(parts): data[key] = parts[i+1]
                    
            except ValueError:
                pass # Loading line parsing failed, keep defaults
            
            current_line_idx += 1

        # --------------------------------------------------------
        # SPECTRUM FILE (Conditional)
        # Some versions put the filename here if NFOPT expects it
        # --------------------------------------------------------
        # Simple heuristic: if the next line is a single string ending in .txt/.spt
        if current_line_idx < len(lines):
            potential_file = lines[current_line_idx]
            if "." in potential_file and len(potential_file.split()) == 1:
                data['SPECTRA'] = potential_file
                current_line_idx += 1

        # --------------------------------------------------------
        # GEOMETRY DIMENSIONS
        # Format: CI CF CN W B AN
        # --------------------------------------------------------
        if current_line_idx < len(lines):
            parts = lines[current_line_idx].split()
            keys = ['CI', 'CF', 'CN', 'W', 'B', 'AN']
            for i, key in enumerate(keys):
                if i < len(parts): data[key] = parts[i]

        return True, data

    except Exception as e:
        return False, f"Parser Exception: {str(e)}"