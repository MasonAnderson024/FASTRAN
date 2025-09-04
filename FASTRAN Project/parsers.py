# parsers.py
"""
parsers.py
----------
Handles parsing and generating FASTRAN and material files, using the 
ProjectManager to handle all file I/O.
"""

import os
import xml.etree.ElementTree as ET
from tkinter import messagebox
from project import ProjectManager # Import the new class

# ------------------------------
# Material File Parsing (.lkpx)
# ------------------------------
# This function remains unchanged as it deals with external material files, not project files.
def parse_material_xml(filepath):
    """
    Parses an XML-based material file to extract key properties and the crack growth table.
    """
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        name = root.findtext('.//Material/Name', 'Unknown Material')
        table_rows = []
        tlookup_table = root.find('.//PropertyData[@property="tlookup"]/DataTable/Data')
        if tlookup_table is not None:
            for row in tlookup_table.findall('row'):
                rate_el = row.find("./FieldData[@pos='1']")
                dk_el = row.find("./FieldData[@pos='2']")
                if dk_el is not None and rate_el is not None:
                    table_rows.append([dk_el.text, rate_el.text])
        if not table_rows:
            messagebox.showwarning("Material Warning", "Could not find a da/dN table in the material file.")
        properties = {
            'SYIELD': root.findtext('.//PropertyData[@property="yld"]/Data', '0.0'),
            'SULT':   root.findtext('.//PropertyData[@property="ult_strength"]/Data', '0.0'),
            'E':      root.findtext('.//PropertyData[@property="e"]/Data', '0.0'),
            'ETA':    root.findtext('.//PropertyData[@property="poisson"]/Data', '0.0'),
        }
        return name, table_rows, properties
    except Exception as e:
        messagebox.showerror("Material File Error", f"Failed to load material file: {e}")
        return None, None, None

# ------------------------------
# FASTRAN Project File Parsing
# ------------------------------
def parse_project_input_file(pm: ProjectManager):
    """
    Parses the main FASTRAN input file from within a project.

    Args:
        pm (ProjectManager): An active and loaded ProjectManager instance.

    Returns:
        tuple: A tuple containing (data_dict, table_data, block_data).
               Returns (None, None, None) on error.
    """
    try:
        content = pm.read_file("input")
        if not content:
            # Return empty state for a new project, not an error
            return {}, [], [] 
            
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines: return {}, [], []

        # The rest of the parsing logic is identical to your previous version
        line_iter = iter(lines)
        data = {}
        table_data = []
        block_data = []
        
        next(line_iter)
        data['SPECTRA'] = next(line_iter)
        data['MAT'] = next(line_iter).strip()
        keys = ['SYIELD', 'SULT', 'E', 'ETA', 'ALP', 'BETAT', 'BETAW', 'NALP', 'NEP']
        vals = next(line_iter).split()
        data.update(zip(keys, vals))
        keys = ['IRATE', 'NGC', 'CRKNGC']
        vals = next(line_iter).split()
        data.update(zip(keys, vals))
        keys = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'KF', 'M', 'NEQN']
        vals = next(line_iter).split()
        data.update(zip(keys, vals))
        vals = next(line_iter).split()
        ntab = int(vals[0])
        data['NTAB'] = str(ntab)
        data['NDKTH'] = vals[1] if len(vals) > 1 else '0'
        if ntab > 0:
            for _ in range(ntab):
                table_data.append(next(line_iter).split()[0:2])
        if data.get('NALP') == '1':
            keys = ['RATE1', 'ALP1', 'BETAT1', 'BETAW1', 'RATE2', 'ALP2', 'BETAT2', 'BETAW2']
            vals = next(line_iter).split()
            data.update(zip(keys, vals))
        keys = ['NIPT', 'NPRT', 'LSTEP', 'NDKE', 'DCPR']
        vals = next(line_iter).split()
        data.update(zip(keys, vals))
        keys = ['NTYP', 'LTYP', 'LFAST', 'NS', 'NFOPT', 'INVERT', 'KCONST', 'NTCMAX']
        vals = next(line_iter).split()
        data.update(zip(keys, vals))
        keys = ['W', 'T', 'CI', 'AI', 'CN', 'AN', 'HN', 'RAD', 'RADF']
        vals = next(line_iter).split()
        data.update(zip(keys, vals))
        data['CF'] = next(line_iter).split()[0]
        ntyp_code = data.get('NTYP')
        ltyp_code = data.get('LTYP')
        if ntyp_code == '5':
            data['RADIUS'] = next(line_iter).split()[0]
        elif ntyp_code in ['-12', '-13']:
            keys = ['RIVETS', 'RLF1', 'RLF2', 'NODKL', 'GAMMA', 'DELTA']
            vals = next(line_iter).split()
            data.update(zip(keys, vals))
        elif (ntyp_code in ['0', '7'] and ltyp_code == '2') or ntyp_code == '-10':
            data['GAMMA'] = next(line_iter).split()[0]
        keys = ['SMAX', 'SMIN']
        vals = next(line_iter).split()
        data.update(zip(keys, vals))
        keys = ['NRC', 'DVALUE', 'NCYCLE1', 'NCYCLE2']
        vals = next(line_iter).split()
        data.update(zip(keys, vals))
        current_line = next(line_iter, "HALT")
        nfopt_val = int(data.get('NFOPT', '0'))
        if 0 <= nfopt_val <= 10 and "HALT" not in current_line.upper():
            vals = current_line.split()
            keys = ['MAXSEQ', 'MAXBLK', 'LPRINT', 'MAXLPR']
            data.update(zip(keys, vals))
            if nfopt_val == 8:
                if len(vals) > 4: data['NREP'] = vals[4]
                if len(vals) > 5: data['MARKER'] = vals[5]
            current_line = next(line_iter, "HALT")
            if nfopt_val == 0:
                data['SCALE'] = current_line
                next(line_iter)
                keys = ['SMAXP', 'SMINP', 'NCYCP']
                vals = next(line_iter).split()
                data.update(zip(keys, vals))
            elif nfopt_val == 1:
                data['SCALE'] = current_line
                line_after_scale = next(line_iter, "HALT")
                while "HALT" not in line_after_scale.upper():
                    header_vals = line_after_scale.split()
                    if len(header_vals) < 2: break
                    nblk, nsl, nsq = header_vals
                    current_block_levels = []
                    for _ in range(int(nsl)):
                        current_block_levels.append(next(line_iter).split())
                    block_data.append({'nsq': str(nsq), 'levels': current_block_levels})
                    if int(nblk) >= int(data.get('MAXSEQ', 1)): break
                    line_after_scale = next(line_iter, "HALT")
            elif nfopt_val in [2, 3]: data['SMEAN'] = current_line
            elif nfopt_val == 6: data['SPEAK'], data['SMEAN'] = current_line.split()
            elif nfopt_val in [4, 5, 7, 8, 9, 10]: data['SPEAK'] = current_line
            current_line = next(line_iter, "HALT")
        if "HALT" not in current_line.upper():
            keys = ['KTH', 'SMAXTH', 'RTH', 'CONST', 'PRT']
            vals = current_line.split()
            data.update(zip(keys, vals))
        
        return data, table_data, block_data
    except Exception as e:
        messagebox.showerror("Parsing Error", f"Failed to parse project input file.\nError: {e}")
        return None, None, None

def generate_fastran_file(pm: ProjectManager, values, table_data, block_data, maps):
    """
    Generates the FASTRAN input file content and saves it to the project.
    """
    try:
        for key, desc in values.items():
            if key.endswith('_DESC'):
                base_key = key.replace('_DESC', '')
                if f"{base_key.lower()}_map" in maps:
                    values[base_key] = maps[f"{base_key.lower()}_map"].get(desc, '0')
        problem_title = pm.metadata.get("project_name", "FASTRAN Project")
        output_lines = []
        output_lines.append(f"{problem_title}")
        output_lines.append(f"{values['SPECTRA']}")
        output_lines.append(f" {values['MAT']}")
        output_lines.append(f"  {float(values['SYIELD']):.1f}  {float(values['SULT']):.1f}  {float(values['E']):.1f}   {float(values['ETA'])}  {float(values['ALP'])}  {float(values['BETAT'])}  {float(values['BETAW'])}  {int(values['NALP'])}  {int(values['NEP'])}")
        output_lines.append(f"    {int(values['IRATE'])}    {int(values['NGC'])}    {float(values['CRKNGC']):.1f}")
        output_lines.append(f" {float(values['C1']):.2E} {float(values['C2']):.2E}  {float(values['C3'])}  {float(values['C4'])}  {float(values['C5']):.4E}  {float(values['C6'])}  {float(values['C7'])}  {float(values['KF'])}  {float(values['M'])}  {int(values['NEQN'])}")
        ntab = int(values['NTAB'])
        output_lines.append(f"    {ntab}    {int(values['NDKTH'])}")
        if ntab > 0:
            for row in table_data:
                output_lines.append(f"  {float(row[0]):<5.2f}   {float(row[1]):g}")
        if values.get('NALP') == '1':
            output_lines.append(f"{float(values['RATE1']):.1E}  {float(values['ALP1']):.2f}  {float(values['BETAT1'])}  {float(values['BETAW1'])}  {float(values['RATE2']):.1E}  {float(values['ALP2']):.2f}  {float(values['BETAT2'])}  {float(values['BETAW2'])}")
        output_lines.append(f"   {int(values['NIPT']):>3d}   {int(values['NPRT']):>3d}    {int(values['LSTEP']):>3d}    {int(values['NDKE']):>3d}   {float(values['DCPR']):.5f}")
        output_lines.append(f"   {int(values['NTYP']):>3d}    {int(values['LTYP']):>3d}    {int(values['LFAST']):>3d}    {int(values['NS']):>3d}     {int(values['NFOPT']):>3d}    {int(values['INVERT']):>3d}    {int(values['KCONST']):>3d}    {int(values['NTCMAX']):>3d}")
        output_lines.append(f" {float(values['W']):.4f}  {float(values['T']):.4f}  {float(values['CI']):.4f}  {float(values['AI']):.4f}  {float(values['CN']):.4f}  {float(values['AN']):.4f}  {float(values['HN']):.4f}   {float(values['RAD']):.4f}   {float(values['RADF']):.4f}")
        output_lines.append(f" {float(values['CF']):.4f}")
        ntyp_code, ltyp_code = values['NTYP'], values['LTYP']
        if ntyp_code == '5': output_lines.append(f" {float(values['RADIUS'])}")
        elif ntyp_code in ['-12', '-13']:
            output_lines.append(f" {float(values['RIVETS'])} {float(values['RLF1'])} {float(values['RLF2'])} {int(values['NODKL'])} {float(values['GAMMA'])} {float(values['DELTA'])}")
        elif (ntyp_code in ['0', '7'] and ltyp_code == '2') or ntyp_code == '-10':
            output_lines.append(f" {float(values['GAMMA'])}")
        output_lines.append(f"   {float(values['SMAX']):.1f}       {float(values['SMIN']):.1f}")
        output_lines.append(f" {int(values['NRC'])}   {float(values['DVALUE'])}    {int(values['NCYCLE1'])}    {int(values['NCYCLE2'])}")
        nfopt_val = int(values.get('NFOPT', '0'))
        if 0 <= nfopt_val <= 10:
            loading_line = f" {int(values.get('MAXSEQ', '0'))}   {int(values.get('MAXBLK', '0'))}   {int(values.get('LPRINT', '0'))}   {int(values.get('MAXLPR', '0'))}"
            if nfopt_val == 8:
                loading_line += f"   {int(values.get('NREP', '0'))}   {int(values.get('MARKER', '0'))}"
            output_lines.append(loading_line)
            if nfopt_val == 0:
                output_lines.append(f"{float(values.get('SCALE', '1.0')):.1f}")
                output_lines.append(" 1   1   1") 
                output_lines.append(f"  {float(values.get('SMAXP', '0.0')):.1f}    {float(values.get('SMINP', '0.0')):.2f}            {int(values.get('NCYCP', '1'))}")
            elif nfopt_val == 1:
                output_lines.append(f"{float(values.get('SCALE', '1.0')):.1f}")
                for i, block in enumerate(block_data):
                    nsl = len(block.get('levels', []))
                    nsq = int(block.get('nsq', '1'))
                    output_lines.append(f" {i+1}   {nsl}   {nsq}")
                    for smax, smin, ncyc in block.get('levels', []):
                        output_lines.append(f" {float(smax):4.1f}   {float(smin):4.2f} {int(ncyc):14d}")
            elif nfopt_val == 6: 
                output_lines.append(f"    {float(values['SPEAK']):.1f}  {float(values['SMEAN']):.1f}")
            elif nfopt_val in [2, 3]: 
                output_lines.append(f"    {float(values['SMEAN']):.1f}")
            elif nfopt_val in [4, 5, 7, 8, 9, 10]: 
                output_lines.append(f"    {float(values['SPEAK']):.1f}")
        output_lines.append(f" {int(values['KTH'])}   {int(float(values['SMAXTH']))}   {float(values['RTH']):.1f}   {float(values['CONST']):.1f}   {int(float(values['PRT']))}")
        output_lines.append("HALT\nHALT")
        
        # Write the content to the project's input file
        pm.write_file("input", '\n'.join(output_lines))
        return True
    except Exception as e:
        messagebox.showerror("File Generation Error", f"An error occurred while generating the FASTRAN input file:\n{e}")
        return False

def parse_project_output_file(pm: ProjectManager):
    """
    Parses a FASTRAN output file from within a project.
    """
    try:
        content = pm.read_file("results")
        if not content:
            return None, None, None, None # No results file yet
            
        lines = content.splitlines()
        
        header, data_table = [], []
        summary_dict = {'total_cycles': 'N/A', 'failure_reason': 'N/A', 'failure_code': None}
        input_params = {}
        in_data_section = False
        for line in lines:
            stripped_line = line.strip()
            if "MATERIAL PROPERTIES:" in line: input_params['Material Name'] = line.split(':', 1)[-1].strip()
            if "SPECTRUM FILE =" in line: input_params['Spectrum Name'] = line.split('=', 1)[-1].strip()
            if "MAX STRESS =" in line and "SMAXP" not in line:
                if 'Max Stress' not in input_params: input_params['Max Stress'] = line.split('=')[-1].strip()
            if "MIDDLE CRACK TENSION" in stripped_line: input_params['Specimen Type (NTYP)'] = "Center Crack Tension"
            elif "COMPACT SPECIMEN" in stripped_line: input_params['Specimen Type (NTYP)'] = "Compact C(T)"
            if "INITIAL CRACK LENGTH (CI)" in stripped_line:
                try:
                    parts = stripped_line.split()
                    ci_index = parts.index('(CI)') + 2
                    input_params['Initial Crack Len (CI)'] = parts[ci_index]
                except (ValueError, IndexError): pass
            if "SPECIMEN WIDTH" in stripped_line:
                try:
                    parts = stripped_line.split()
                    w_index = parts.index('WIDTH') + 2
                    t_index = parts.index('THICKNESS') + 2
                    input_params['Width/Half-Width (W)'] = parts[w_index]
                    input_params['Thickness (T)'] = parts[t_index]
                except (ValueError, IndexError): pass
            if "BLOCK" in stripped_line and ("C_crack" in stripped_line or "C*-RAD" in stripped_line):
                header = [h.replace('C*-RAD', 'C_crack') for h in stripped_line.split() if h]
                in_data_section = True
                continue
            if in_data_section and stripped_line:
                if "SPECIMEN FAILED" in stripped_line or "CRACK LENGTH EXCEEDS" in stripped_line:
                    in_data_section = False
                parts = stripped_line.split()
                try:
                    float(parts[0])
                    is_data_row = True
                except (ValueError, IndexError): is_data_row = False
                if is_data_row:
                    if parts[-1] == '*': parts.pop()
                    if len(parts) == len(header): data_table.append(parts)
            if "TOTAL CYCLES =" in stripped_line:
                summary_dict['total_cycles'] = stripped_line.split('=')[-1].strip()
            if "NFCODE =" in stripped_line:
                summary_dict['failure_code'] = line.split('=')[-1].strip().split(':')[0].strip()
                summary_dict['failure_reason'] = line.split(':', 1)[-1].strip()
            elif "CRACK LENGTH EXCEEDS" in stripped_line:
                summary_dict['failure_reason'] = "CRACK LENGTH EXCEEDS INPUT VALUE FOR CF"
        
        if not header or not data_table: return None, None, None, None
        return header, data_table, summary_dict, input_params
    except Exception as e:
        print(f"Parser Error: Exception while parsing output file: {e}")
        return None, None, None, None