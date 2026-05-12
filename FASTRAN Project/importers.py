# importers.py
"""
importers.py
------------
Legacy Data Importer for FASTRAN GUI.

Parses raw text FASTRAN input files (18-section positional format) and maps
the values to GUI variable names. Based on FASTRAN Version 5.4/5.78f User Guide.
"""

import config
import json
import os


def parse_fastran_input(filepath):
    """
    Reads a FASTRAN input file and returns a dict of values mapped to GUI variable names.

    Returns:
        tuple: (success (bool), data dict or error string)
    """
    if not os.path.exists(filepath):
        return False, "File not found."

    try:
        with open(filepath, 'r') as f:
            raw_lines = [ln.rstrip() for ln in f]

        # Strip blank lines and HALT terminators; keep originals for line counting
        lines = [ln for ln in raw_lines if ln.strip() and not ln.strip().upper().startswith('HALT')]

        if len(lines) < 10:
            return False, "File is too short to be a valid FASTRAN input."

        data = {}
        idx = 0  # current line index

        def next_parts():
            """Advance idx and return whitespace-split tokens of current line."""
            nonlocal idx
            if idx >= len(lines):
                return []
            parts = lines[idx].split()
            idx += 1
            return parts

        def next_line():
            nonlocal idx
            if idx >= len(lines):
                return ""
            ln = lines[idx]
            idx += 1
            return ln.strip()

        # ── Section 1: Problem Title ──────────────────────────────────────────
        data['TITLE'] = next_line()

        # ── Section 2: Spectrum Filename ──────────────────────────────────────
        data['SPECTRA'] = next_line()

        # ── Section 3: Material Title ─────────────────────────────────────────
        data['MAT'] = next_line()

        # ── Section 4: SYIELD SULT E ETA ALP BETAT BETAW NALP NEP ────────────
        p = next_parts()
        keys4 = ['SYIELD', 'SULT', 'E', 'ETA', 'ALP', 'BETAT', 'BETAW', 'NALP', 'NEP']
        for i, k in enumerate(keys4):
            if i < len(p):
                data[k] = p[i]
        nalp = int(data.get('NALP', '0'))

        # ── Section 5: IRATE NGC CRKNGC ───────────────────────────────────────
        p = next_parts()
        if len(p) >= 3:
            data['IRATE']  = p[0]
            data['NGC']    = p[1]
            data['CRKNGC'] = p[2]
        irate = int(data.get('IRATE', '1'))

        # ── Sections 6 & 7 — repeated IRATE times ─────────────────────────────
        # Eq 1 → base keys; eq 2..4 → suffixed keys (e.g., C1_2, NTAB_3).
        def eq_key(base, eq_idx):
            return base if eq_idx == 1 else f"{base}_{eq_idx}"

        keys6 = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'KF', 'M', 'NEQN']
        for j in range(1, irate + 1):
            # Section 6
            p = next_parts()
            for i, k in enumerate(keys6):
                if i < len(p):
                    data[eq_key(k, j)] = p[i]

            # Section 7a: NTAB NDKTH
            p = next_parts()
            ntab = 0
            if len(p) >= 2:
                data[eq_key('NTAB', j)]  = p[0]
                data[eq_key('NDKTH', j)] = p[1]
                try:
                    ntab = int(p[0])
                except ValueError:
                    ntab = 0

            # Section 7b: table rows — captured per-equation as JSON-encoded
            # list of [dk, rate] pairs under CGR_TABLE (eq 1) / CGR_TABLE_{j}.
            tab_rows = []
            for _i in range(ntab):
                parts = next_parts()
                if len(parts) >= 2:
                    tab_rows.append([parts[0], parts[1]])
            tkey = 'CGR_TABLE' if j == 1 else f'CGR_TABLE_{j}'
            data[tkey] = json.dumps(tab_rows)

        # ── Section 8: NALP=1 transition rates ───────────────────────────────
        if nalp == 1:
            p = next_parts()
            keys8 = ['RATE1', 'ALP1', 'BETAT1', 'BETAW1',
                     'RATE2', 'ALP2', 'BETAT2', 'BETAW2']
            for i, k in enumerate(keys8):
                if i < len(p):
                    data[k] = p[i]

        # ── Section 9: NIPT NPRT LSTEP NDKE DCPR ─────────────────────────────
        p = next_parts()
        keys9 = ['NIPT', 'NPRT', 'LSTEP', 'NDKE', 'DCPR']
        for i, k in enumerate(keys9):
            if i < len(p):
                data[k] = p[i]

        # ── Section 10: NTYP LTYP LFAST NS NFOPT INVERT KCONST NTCMAX ────────
        p = next_parts()
        keys10 = ['NTYP', 'LTYP', 'LFAST', 'NS', 'NFOPT', 'INVERT', 'KCONST', 'NTCMAX']
        raw_ntyp  = 1
        raw_nfopt = 0
        raw_ltyp  = 0
        for i, k in enumerate(keys10):
            if i < len(p):
                data[k] = p[i]
        try:
            raw_ntyp  = int(data.get('NTYP',  '1'))
            raw_nfopt = int(data.get('NFOPT', '0'))
            raw_ltyp  = int(data.get('LTYP',  '0'))
        except ValueError:
            pass

        # Map NTYP integer to GUI option string
        ntyp_opt = next((opt for opt in config.GEOMETRY_OPTIONS if opt.startswith(f"{raw_ntyp}:")), None)
        data['NTYP'] = ntyp_opt if ntyp_opt else f"{raw_ntyp}: Unknown"
        # Map NFOPT integer to GUI option string
        nfopt_opt = next((opt for opt in config.LOADING_OPTIONS if opt.startswith(f"{raw_nfopt}:")), None)
        data['NFOPT'] = nfopt_opt if nfopt_opt else f"{raw_nfopt}: Unknown"
        # Map combobox-driven integer fields to GUI option strings
        for key, options in (('LTYP',   config.LTYP_OPTIONS),
                             ('LFAST',  config.LFAST_OPTIONS),
                             ('KCONST', config.KCONST_OPTIONS),
                             ('NALP',   config.NALP_OPTIONS),
                             ('NEP',    config.NEP_OPTIONS)):
            if key in data:
                data[key] = config.label_for_int(data[key], options)

        # ── Section 11: W T CI AI CN AN HN RAD RADF ──────────────────────────
        p = next_parts()
        keys11 = ['W', 'B', 'CI', 'AI', 'CN', 'AN', 'HN', 'RAD', 'RADF']
        for i, k in enumerate(keys11):
            if i < len(p):
                data[k] = p[i]
        # Also write T = B for consistency
        if 'B' in data:
            data['T'] = data['B']

        # ── Section 12: KTAB + table (NTYP=99 or -99 only) ───────────────────
        if abs(raw_ntyp) == 99:
            p = next_parts()
            ktab = int(p[0]) if p else 0
            data['KTAB'] = str(ktab)
            for _i in range(ktab):
                next_line()

        # ── Section 13: CF ────────────────────────────────────────────────────
        p = next_parts()
        if p:
            data['CF'] = p[0]

        # ── Section 14: Special inputs (conditional on NTYP / LTYP) ──────────
        if raw_ntyp == 5:
            p = next_parts()
            if p: data['RADIUS'] = p[0]
        elif raw_ntyp in (0, 7) and raw_ltyp == 2:
            p = next_parts()
            if p: data['GAMMA'] = p[0]
        elif raw_ntyp == -10:
            p = next_parts()
            if p: data['GAMMA'] = p[0]
        elif raw_ntyp in (-7, -8, -9):
            p = next_parts()
            if len(p) >= 2:
                data['XKT']  = p[0]
                data['NBCF'] = p[1]
        elif raw_ntyp in (-12, -13):
            p = next_parts()
            keys14 = ['RIVETS', 'RLF1', 'RLF2', 'NODKL', 'GAMMA', 'DELTA']
            for i, k in enumerate(keys14):
                if i < len(p): data[k] = p[i]

        # ── Section 15: SMAX SMIN ─────────────────────────────────────────────
        p = next_parts()
        if len(p) >= 2:
            smax = float(p[0])
            smin = float(p[1])
            data['SMAX'] = p[0]
            # Compute R = Smin/Smax; guard against division by zero
            data['R'] = str(round(smin / smax, 6)) if smax != 0 else '0.0'

        # ── Section 16: NRC DVALUE NCYCLE1 NCYCLE2 ───────────────────────────
        p = next_parts()
        keys16 = ['NRC', 'DVALUE', 'NCYCLE1', 'NCYCLE2']
        for i, k in enumerate(keys16):
            if i < len(p): data[k] = p[i]

        # ── Section 17: Primary loading (just grab SPEAK/SMEAN if present) ────
        # Full block-data parsing not needed for the GUI import use case.
        p = next_parts()  # Line 1: MAXSEQ MAXBLK LPRINT MAXLPR [NREP MARKER]
        if len(p) >= 4:
            data['MAXSEQ'] = p[0]
            data['MAXBLK'] = p[1]
            data['LPRINT'] = p[2]
            data['MAXLPR'] = p[3]
        if raw_nfopt == 8 and len(p) >= 6:
            data['NREP']   = p[4]
            data['MARKER'] = p[5]

        if raw_nfopt not in (0, 1):
            # Line 2 is a scalar: SPEAK (or SMEAN for NFOPT=2,3)
            p2 = next_parts()
            if p2:
                if raw_nfopt in (2, 3):
                    data['SMEAN'] = p2[0]
                else:
                    data['SPEAK'] = p2[0]
        else:
            # NFOPT=0/1: Line 2 is SCALE, Line 3+ are block definitions
            p2 = next_parts()  # SCALE
            if p2: data['SCALE'] = p2[0]
            # Skip remaining block lines (not parsed into GUI vars)
            p3 = next_parts()  # NBLK NSL NSQ
            nsl = int(p3[1]) if len(p3) >= 2 else 1
            for _level in range(nsl):
                p_lvl = next_parts()  # SMAXP SMINP NCYCP
                if len(p_lvl) >= 2 and not data.get('SMAX_PRIMARY'):
                    data['SMAX_PRIMARY'] = p_lvl[0]

        # ── Section 18: KTH SMAXTH RTH CONST PRT ─────────────────────────────
        p = next_parts()
        keys18 = ['KTH', 'SMAXTH', 'RTH', 'CONST', 'PRT']
        for i, k in enumerate(keys18):
            if i < len(p): data[k] = p[i]

        return True, data

    except Exception as e:
        return False, f"Parser Exception: {str(e)}"
