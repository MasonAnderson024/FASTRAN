# parsers.py
"""
parsers.py
----------
Input Generation and Output Parsing Logic for FASTRAN GUI.

Responsibilities:
1. Input Generator: Converts GUI variables into the strict whitespace-delimited
   text format required by FASTRAN 5.4.
2. Output Parser: Reads .fou files and extracts tabular data for plotting.
3. Legacy Material Support: Parses old XML material files if needed.
"""

import os
import config
import re

# ------------------------------------------------------------------
# 1. INPUT GENERATION
# ------------------------------------------------------------------
def generate_fastran_input(filepath, vars_dict, is_dict=False):
    """
    Generates a FASTRAN input file following the 18-section format defined in
    FASTRAN Version 5.4/5.78f User Guide (Sections B1-B18).

    Args:
        filepath (str): Absolute path where the input file will be saved.
        vars_dict (dict): GUI Tkinter StringVars (is_dict=False) or plain dict (is_dict=True).

    Returns:
        tuple: (success (bool), message (str))
    """
    try:
        def get_val(key):
            if key not in vars_dict:
                return config.DEFAULT_VALUES.get(key, "0.0")
            val = vars_dict[key]
            return val if is_dict else val.get()

        def row(*vals):
            return "  ".join(str(v) for v in vals)

        def int_prefix(raw):
            """Extract leading integer from 'N: label' or '-N: label' combobox values; pass plain ints through."""
            s = str(raw).strip()
            return int(s.split(':', 1)[0]) if ':' in s else int(s)

        # Extract commonly used integers up front
        ntyp  = int_prefix(get_val('NTYP'))
        nfopt = int_prefix(get_val('NFOPT'))
        nalp  = int_prefix(get_val('NALP'))
        irate = int(get_val('IRATE'))
        ltyp  = int_prefix(get_val('LTYP'))

        lines = []

        # ── Section 1: Problem Title ──────────────────────────────────────────
        lines.append(get_val('TITLE')[:80])

        # ── Section 2: Spectrum Filename ──────────────────────────────────────
        lines.append(get_val('SPECTRA'))

        # ── Section 3: Material Title ─────────────────────────────────────────
        lines.append(get_val('MAT'))

        # ── Section 4: SYIELD SULT E ETA ALP BETAT BETAW NALP NEP ────────────
        lines.append(row(
            get_val('SYIELD'), get_val('SULT'), get_val('E'), get_val('ETA'),
            get_val('ALP'), get_val('BETAT'), get_val('BETAW'),
            int_prefix(get_val('NALP')), int_prefix(get_val('NEP'))
        ))

        # ── Section 5: IRATE NGC CRKNGC ───────────────────────────────────────
        lines.append(row(irate, get_val('NGC'), get_val('CRKNGC')))

        # ── Sections 6 & 7 — repeated IRATE times ────────────────────────────
        # IRATE=1 single law (eq 1 only); IRATE=2 c/a independent; IRATE=4
        # small/large transition. Eq 1 uses base keys (C1, C2, ...); eq 2..4
        # use suffixed keys (C1_2, NTAB_3, ...) populated by the GUI Notebook.
        def eq_key(base, eq_idx):
            return base if eq_idx == 1 else f"{base}_{eq_idx}"

        for j in range(1, irate + 1):
            # Section 6: C1 C2 C3 C4 C5 C6 C7 KF m NEQN
            lines.append(row(
                get_val(eq_key('C1', j)), get_val(eq_key('C2', j)),
                get_val(eq_key('C3', j)), get_val(eq_key('C4', j)),
                get_val(eq_key('C5', j)), get_val(eq_key('C6', j)),
                get_val(eq_key('C7', j)),
                get_val(eq_key('KF', j)), get_val(eq_key('M', j)),
                get_val(eq_key('NEQN', j))
            ))
            # Section 7a: NTAB NDKTH (per-equation)
            try:
                ntab_j = int(get_val(eq_key('NTAB', j)))
            except (TypeError, ValueError):
                ntab_j = 0
            lines.append(row(ntab_j, get_val(eq_key('NDKTH', j))))
            # Section 7b: table rows (NTAB data pairs) per equation. The GUI
            # stores each equation's table as a JSON-encoded list under
            # CGR_TABLE (eq 1) or CGR_TABLE_{j} (eq 2+).
            if ntab_j > 0:
                tkey = 'CGR_TABLE' if j == 1 else f'CGR_TABLE_{j}'
                table_data = vars_dict.get(tkey, [])
                if not is_dict and hasattr(table_data, 'get'):
                    table_data = table_data.get()
                if isinstance(table_data, str):
                    s = table_data.strip()
                    try:
                        import json as _json
                        table_data = _json.loads(s) if s else []
                    except Exception:
                        try:
                            import ast
                            table_data = ast.literal_eval(s)
                        except Exception:
                            table_data = []
                for dk, rate in list(table_data)[:ntab_j]:
                    lines.append(row(dk, rate))

        # ── Section 8: NALP=1 transition rates ───────────────────────────────
        if nalp == 1:
            lines.append(row(
                get_val('RATE1'), get_val('ALP1'), get_val('BETAT1'), get_val('BETAW1'),
                get_val('RATE2'), get_val('ALP2'), get_val('BETAT2'), get_val('BETAW2')
            ))

        # ── Section 9: NIPT NPRT LSTEP NDKE DCPR ─────────────────────────────
        lines.append(row(
            get_val('NIPT'), get_val('NPRT'), get_val('LSTEP'),
            get_val('NDKE'), get_val('DCPR')
        ))

        # ── Section 10: NTYP LTYP LFAST NS NFOPT INVERT KCONST NTCMAX ────────
        lines.append(row(
            ntyp, ltyp, int_prefix(get_val('LFAST')), get_val('NS'),
            nfopt, get_val('INVERT'), int_prefix(get_val('KCONST')), get_val('NTCMAX')
        ))

        # ── Section 11: W T CI AI CN AN HN RAD RADF ──────────────────────────
        # T = specimen thickness. GUI field is 'B'; fall back to 'T' default.
        t_val = get_val('B')
        lines.append(row(
            get_val('W'), t_val, get_val('CI'), get_val('AI'),
            get_val('CN'), get_val('AN'), get_val('HN'),
            get_val('RAD'), get_val('RADF')
        ))

        # ── Section 12: KTAB + table (NTYP=99 or -99 only) ───────────────────
        if abs(ntyp) == 99:
            ktab = int(get_val('KTAB'))
            lines.append(str(ktab))
            if ktab > 0:
                ktab_data = vars_dict.get('KTAB_TABLE', [])
                if not is_dict and hasattr(ktab_data, 'get'):
                    ktab_data = ktab_data.get()
                if isinstance(ktab_data, str):
                    try:
                        import ast
                        ktab_data = ast.literal_eval(ktab_data)
                    except Exception:
                        ktab_data = []
                for cw, fc in list(ktab_data)[:ktab]:
                    lines.append(row(cw, fc))

        # ── Section 13: CF ────────────────────────────────────────────────────
        lines.append(get_val('CF'))

        # ── Section 14: Special inputs (conditional on NTYP / LTYP) ──────────
        if ntyp == 5:
            lines.append(get_val('RADIUS'))
        elif ntyp in (0, 7) and ltyp == 2:
            lines.append(get_val('GAMMA'))
        elif ntyp == -10:
            lines.append(get_val('GAMMA'))
        elif ntyp in (-7, -8, -9):
            lines.append(row(get_val('XKT'), get_val('NBCF')))
        elif ntyp in (-12, -13):
            lines.append(row(
                get_val('RIVETS'), get_val('RLF1'), get_val('RLF2'),
                get_val('NODKL'), get_val('GAMMA'), get_val('DELTA')
            ))

        # ── Section 15: SMAX SMIN (pre-cracking constant amplitude) ──────────
        smax = float(get_val('SMAX'))
        smin = smax * float(get_val('R'))
        lines.append(row(smax, smin))

        # ── Section 16: NRC DVALUE NCYCLE1 NCYCLE2 ───────────────────────────
        lines.append(row(
            get_val('NRC'), get_val('DVALUE'),
            get_val('NCYCLE1'), get_val('NCYCLE2')
        ))

        # ── Section 17: Primary fatigue loading (varies by NFOPT) ─────────────
        _write_loading_section(lines, nfopt, get_val, smax, smin)

        # ── Section 18: Load-reduction threshold test ─────────────────────────
        lines.append(row(
            get_val('KTH'), get_val('SMAXTH'), get_val('RTH'),
            get_val('CONST'), get_val('PRT')
        ))

        # ── Terminator ────────────────────────────────────────────────────────
        lines.append("HALT")
        lines.append("HALT")

        with open(filepath, 'w') as f:
            f.write("\n".join(lines) + "\n")

        return True, "Input file generated successfully."

    except Exception as e:
        return False, f"Generation Error: {str(e)}"


def _write_loading_section(lines, nfopt, get_val, smax, smin):
    """Write Section 17 (primary fatigue loading) for the given NFOPT."""

    def row(*vals):
        return "  ".join(str(v) for v in vals)

    maxseq = get_val('MAXSEQ')
    maxblk = get_val('MAXBLK')
    lprint = get_val('LPRINT')
    maxlpr = get_val('MAXLPR')
    speak  = get_val('SPEAK')
    smean  = get_val('SMEAN')

    if nfopt in (0, 1):
        # Constant amplitude or user-specified block loading
        # Line 1: MAXSEQ MAXBLK LPRINT MAXLPR
        lines.append(row(maxseq, maxblk, lprint, maxlpr))
        # Line 2: SCALE
        lines.append(get_val('SCALE'))
        # Lines 3+: block definitions
        # For NFOPT=1, full block data comes from BlockEditorWindow (not wired yet).
        # For NFOPT=0, generate a single block with one constant-amplitude level.
        block_data = get_val('BLOCK_DATA') if 'BLOCK_DATA' in {} else None
        if block_data is None:
            # Default: one block, one stress level
            lines.append(row(1, 1, 1))              # NBLK=1  NSL=1  NSQ=1
            lines.append(row(smax, smin, 1))        # SMAXP SMINP NCYCP

    elif nfopt in (2, 3):
        # TWIST / Mini-TWIST: MAXSEQ=4000 MAXBLK=10 (code-defined)
        lines.append(row(maxseq, maxblk, lprint, maxlpr))
        lines.append(smean)

    elif nfopt == 4:
        # FALSTAFF: MAXSEQ=MAXBLK=200
        lines.append(row(maxseq, maxblk, lprint, maxlpr))
        lines.append(speak)

    elif nfopt == 5:
        # Space Shuttle: MAXSEQ=MAXBLK=MAXLPR=2
        lines.append(row(maxseq, maxblk, lprint, maxlpr))
        lines.append(speak)

    elif nfopt == 6:
        # Gaussian — not allowed in current FASTRAN version
        lines.append(row(maxseq, maxblk, lprint, maxlpr))
        lines.append(row(speak, smean))

    elif nfopt == 7:
        # Helicopter (Felix-28 or Helix-32)
        lines.append(row(maxseq, maxblk, lprint, maxlpr))
        lines.append(speak)

    elif nfopt == 8:
        # Spectrum from list of stress points — needs NREP and MARKER
        nrep   = get_val('NREP')
        marker = get_val('MARKER')
        lines.append(row(maxseq, maxblk, lprint, maxlpr, nrep, marker))
        lines.append(speak)

    elif nfopt in (9, 10):
        # Flight-by-flight or flight schedule
        lines.append(row(maxseq, maxblk, lprint, maxlpr))
        lines.append(speak)

    else:
        # Unknown NFOPT — write minimal placeholder
        lines.append(row(maxseq, maxblk, lprint, maxlpr))
        lines.append(speak)

# ------------------------------------------------------------------
# 2. OUTPUT PARSING (For Post-Processor)
# ------------------------------------------------------------------
def parse_output_table(filepath):
    """
    Reads a .fou output file and extracts numeric data columns.
    Used by the Post-Processor to plot results.

    Returns:
        headers (list): List of column names (e.g. ['CYCLES', 'C-LENGTH'])
        data (dict): Dictionary mapping header name to list of floats.
    """
    data_dict = {}
    headers = []
    
    if not os.path.exists(filepath):
        return [], {}

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        start_parsing = False
        
        for line in lines:
            stripped = line.strip()
            
            # Detect Header Line
            if "CYCLES" in stripped and "C-LENGTH" in stripped and not start_parsing:
                # Normalize headers
                raw_headers = stripped.split()
                # Clean up headers (remove parens like (mm))
                headers = [h.split('(')[0] for h in raw_headers] 
                
                # Initialize lists
                for h in headers:
                    data_dict[h] = []
                
                start_parsing = True
                continue
                
            if start_parsing:
                # Stop conditions
                if "TOTAL CYCLES" in stripped or len(stripped) == 0:
                    if len(data_dict[headers[0]]) > 0:
                        break # Done
                    else:
                        continue # Empty line but maybe more data coming?
                
                # Parse Numbers
                parts = stripped.split()
                
                # Validate line structure
                if len(parts) >= len(headers) and parts[0][0].isdigit():
                    try:
                        # Attempt to parse row
                        row_vals = []
                        for val in parts[:len(headers)]:
                            row_vals.append(float(val))
                        
                        # If successful, add to dict
                        for i, val in enumerate(row_vals):
                            data_dict[headers[i]].append(val)
                    except ValueError:
                        continue # Skip malformed lines

        return headers, data_dict

    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return [], {}

# ------------------------------------------------------------------
# 3. LEGACY MATERIAL SUPPORT (Optional)
# ------------------------------------------------------------------
def parse_material_xml(filepath):
    """
    Parses legacy .lkpx or XML material files (NASGRO style).
    This logic is preserved from your original upload for backward compatibility.
    """
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        # Extract basic properties if available
        # This is highly dependent on the XML schema used
        name = root.findtext('.//Material/Name', 'Unknown')

        # Return a dict structure compatible with our GUI
        # (Simplified implementation)
        return {'MAT': name}

    except Exception:
        return None


def parse_lkpx_for_batch(filepath):
    """
    Parses an LK Pro-X .lkpx file (XML) to extract material properties and
    all R-ratio crack-growth datasets for batch DKEFF conversion.

    Returns:
        (mat_props: dict, datasets: dict[r_ratio_str -> list[[dk, dadn]]])

    Raises:
        ValueError  if expected XML structure is not found
        ET.ParseError  if the file is not valid XML
    """
    import xml.etree.ElementTree as ET

    tree = ET.parse(filepath)
    root = tree.getroot()

    mat_props = {
        'SYIELD': root.findtext(".//PropertyData[@property='yld']/Data", '0.0'),
        'SULT':   root.findtext(".//PropertyData[@property='ult_strength']/Data", '0.0'),
        'E':      root.findtext(".//PropertyData[@property='e']/Data", '0.0'),
    }

    tlookup = root.find(".//PropertyData[@property='tlookup']/DataTable")
    if tlookup is None:
        raise ValueError("Could not find 'tlookup' data table in the .lkpx file.")

    # Map column position → R-ratio string  (fields named like "r_0.1", "r_0.5", …)
    r_map = {}
    for field in tlookup.findall(".//Fields/Field"):
        prop = field.get('property', '')
        if prop.startswith('r_'):
            r_map[field.get('pos')] = prop.split('_', 1)[1]

    if not r_map:
        raise ValueError("No R-ratio columns found in the .lkpx tlookup table.")

    datasets = {r: [] for r in r_map.values()}
    for row in tlookup.findall(".//Data/row"):
        dadn_node = row.find("./FieldData[@pos='1']")
        if dadn_node is None or dadn_node.text is None:
            continue
        dadn = dadn_node.text.strip()
        for pos, r_val in r_map.items():
            dk_node = row.find(f"./FieldData[@pos='{pos}']")
            if dk_node is not None and dk_node.text:
                datasets[r_val].append([dk_node.text.strip(), dadn])

    return mat_props, datasets