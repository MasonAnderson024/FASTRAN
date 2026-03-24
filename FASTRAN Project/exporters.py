# exporters.py
"""
exporters.py
------------
Data Export Module for FASTRAN GUI.

Responsibilities:
1. Parsing: Reads raw FASTRAN output files (.fou/.txt).
2. Extraction: Identifies tabular data (Crack Length vs Cycles) amidst text logs.
3. Formatting: Writes clean, comma-separated values (CSV) for external tools.
"""

import csv
import os
import re

def export_to_csv(fou_filepath, csv_filepath):
    """
    Parses a FASTRAN .fou output file and writes the data table to CSV.
    
    Args:
        fou_filepath (str): Path to the raw FASTRAN output.
        csv_filepath (str): Destination path for the .csv file.

    Returns:
        tuple: (Success (bool), Message (str))
    """
    if not os.path.exists(fou_filepath):
        return False, "Output file not found."

    try:
        data_rows = []
        header_found = False
        num_columns = 0
        
        with open(fou_filepath, 'r') as f:
            lines = f.readlines()

        for line in lines:
            clean_line = line.strip()
            
            # ----------------------------------------------------------
            # 1. HEADER DETECTION
            # FASTRAN headers usually contain 'CYCLES' and 'C-LENGTH'
            # ----------------------------------------------------------
            if "CYCLES" in clean_line and "C-LENGTH" in clean_line and not header_found:
                # Normalize whitespace
                parts = re.split(r'\s+', clean_line)
                
                # Cleanup headers (remove units like "(cycles)" or "(mm)")
                # e.g. "C-LENGTH(mm)" -> "C-LENGTH"
                clean_headers = [h.split('(')[0] for h in parts]
                
                data_rows.append(clean_headers)
                num_columns = len(clean_headers)
                header_found = True
                continue

            # ----------------------------------------------------------
            # 2. DATA EXTRACTION
            # ----------------------------------------------------------
            if header_found:
                # Stop conditions: Summary section usually starts with "TOTAL CYCLES"
                # or we hit a blank line followed by text.
                if "TOTAL CYCLES" in clean_line or "FAILURE CODE" in clean_line:
                    break
                
                if not clean_line:
                    continue

                # Split line by whitespace
                parts = re.split(r'\s+', clean_line)
                
                # Heuristic: Valid data line must have same # of columns as header
                # and the first item must be a number (Cycle count)
                if len(parts) >= num_columns:
                    # Check if first item is numeric
                    # (FASTRAN sometimes puts asterisks '*' for overflow, ignore those lines)
                    if parts[0].replace('.', '', 1).isdigit():
                        # We only take the columns corresponding to headers
                        # (Sometimes there are trailing comments)
                        row_data = parts[:num_columns]
                        data_rows.append(row_data)

        if len(data_rows) < 2:
            return False, "No tabular data found in the output file."

        # ----------------------------------------------------------
        # 3. WRITE TO CSV
        # ----------------------------------------------------------
        with open(csv_filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(data_rows)
            
        return True, f"Successfully exported {len(data_rows)-1} data rows."

    except Exception as e:
        return False, f"Export Error: {str(e)}"