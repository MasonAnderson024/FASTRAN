# batch.py
"""
batch.py
--------
Sensitivity Analysis Engine for FASTRAN GUI.

Responsibilities:
1. Job Generation: Creates a suite of input files by varying a single parameter.
2. Result Extraction: Parses output files to find key metrics (Total Cycles).
3. State Management: Tracks the progress of batch runs.
"""

import os
import copy
import parsers

class BatchManager:
    def __init__(self, project_manager, base_vars_dict):
        """
        Args:
            project_manager: Instance of ProjectManager (for secure paths).
            base_vars_dict: Dictionary of current GUI values (baseline).
        """
        self.project = project_manager
        self.base_vars = base_vars_dict
        self.jobs = []

    def generate_jobs(self, target_var, start_val, end_val, steps):
        """
        Generates N input files by varying target_var from start to end.
        """
        self.jobs = []
        
        try:
            # Parse Range Inputs
            start = float(start_val)
            end = float(end_val)
            steps = int(steps)
            
            if steps < 2:
                step_size = 0
                steps = 1 # Run at least one if user enters 1
            else:
                step_size = (end - start) / (steps - 1)
            
            # Generate Jobs
            for i in range(steps):
                if steps == 1:
                    val = start
                else:
                    val = start + (i * step_size)
                
                # Format value (keep reasonable precision)
                val_str = f"{val:.4f}"
                
                # Create Job Configuration
                job_vars = copy.deepcopy(self.base_vars)
                job_vars[target_var] = val_str
                
                # Define Filenames
                # e.g. batch_SMAX_100.5.txt
                safe_val_name = val_str.replace('.', 'p')
                job_name = f"batch_{target_var}_{i+1}_{safe_val_name}"
                
                input_filename = f"{job_name}.txt"
                output_filename = f"{job_name}.fou"
                
                # Get Secure Paths
                input_path = os.path.join(self.project.get_path('input'), input_filename)
                
                # Generate Input File using the Parser
                # Note: We pass is_dict=True because job_vars is a dict, not Tkinter vars
                success, msg = parsers.generate_fastran_input(input_path, job_vars, is_dict=True)
                
                if not success:
                    return False, f"Failed to generate job {i+1}: {msg}"
                
                self.jobs.append({
                    'id': i,
                    'val': val,
                    'input_path': input_path,
                    'output_filename': output_filename
                })
                
            return True, f"Successfully generated {len(self.jobs)} analysis jobs."

        except ValueError:
            return False, "Invalid numeric range provided."
        except Exception as e:
            return False, f"Batch Generation Error: {str(e)}"

    def extract_cycles(self, output_filepath):
        """
        Parses a FASTRAN .fou output file to find the total life.
        Looking for line: "TOTAL CYCLES =  123456"
        """
        if not os.path.exists(output_filepath):
            return 0.0
            
        try:
            with open(output_filepath, 'r') as f:
                # Read line by line to find the summary
                for line in f:
                    if "TOTAL CYCLES" in line and "=" in line:
                        # Example: "  TOTAL CYCLES =   15000"
                        parts = line.split('=')
                        if len(parts) > 1:
                            # Parse the number after equals
                            clean_num = parts[1].strip().split()[0] # Take first token
                            return float(clean_num)
                            
            return 0.0 # Not found (analysis might have failed)
            
        except Exception:
            return 0.0