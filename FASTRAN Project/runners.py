# runners.py
"""
runners.py
---------
Handles the execution of external command-line executables (FASTRAN, dkeff)
in a non-blocking way using background threads.
"""

import subprocess
import threading
import queue
import os
from project import ProjectManager

def _execute_process(exe_path: str, input_str: str, cwd: str, output_queue: queue.Queue):
    """
    A worker function that runs in a separate thread to execute a command-line program.
    (This function does not need to change.)
    """
    try:
        process = subprocess.Popen(
            [exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=cwd,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if input_str:
            process.stdin.write(input_str)
            process.stdin.flush()
            process.stdin.close()

        for line in iter(process.stdout.readline, ''):
            output_queue.put(line)
        
        process.stdout.close()
        return_code = process.wait()
        output_queue.put(f"\n--- PROCESS FINISHED (Exit Code: {return_code}) ---\n")

    except FileNotFoundError:
        output_queue.put(f"ERROR: Executable not found at the specified path:\n{exe_path}")
    except Exception as e:
        output_queue.put(f"ERROR: An unexpected error occurred while running the process:\n{e}")
    finally:
        output_queue.put(None) # Sentinel value to signal completion

def run_fastran(pm: ProjectManager, exe_path: str, output_queue: queue.Queue):
    """
    Launches the FASTRAN executable in a background thread using the active project.

    Args:
        pm (ProjectManager): The active ProjectManager instance.
        exe_path (str): Path to fastran.exe.
        output_queue (queue.Queue): Queue for capturing console output.
    """
    # Get all necessary paths and filenames from the project manager
    input_filepath = pm.get_path("input")
    results_filepath = pm.get_path("results")
    working_directory = pm.project_path
    
    # The stdin string needs relative filenames from the working directory
    input_filename_relative = os.path.relpath(input_filepath, working_directory)
    results_filename_relative = os.path.relpath(results_filepath, working_directory)
    
    # FASTRAN expects the input filename, then the output filename, each on a new line
    fastran_input_str = f"{input_filename_relative}\n{results_filename_relative}\n"

    thread = threading.Thread(
        target=_execute_process,
        args=(exe_path, fastran_input_str, working_directory, output_queue),
        daemon=True
    )
    thread.start()

def run_dkeff(exe_path: str, input_filepath: str, output_filename: str, test_type_code: str, output_queue: queue.Queue):
    """
    Launches the dkeff executable. This remains unchanged as it's a utility
    that can operate on files outside of a project context.
    """
    input_filename = os.path.basename(input_filepath)
    working_directory = os.path.dirname(input_filepath)
    
    dkeff_input_str = (
        f"1\n"
        f"{test_type_code}\n"
        f"{input_filename}\n"
        f"{os.path.basename(output_filename)}\n"
        f"0\n"
        f"1\n"
    )

    thread = threading.Thread(
        target=_execute_process,
        args=(exe_path, dkeff_input_str, working_directory, output_queue),
        daemon=True
    )
    thread.start()