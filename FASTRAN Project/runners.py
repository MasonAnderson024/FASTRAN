# runners.py
"""
runners.py
----------
Secure Execution Engine for FASTRAN GUI.

Responsibilities:
1. Process Management: Runs external EXEs (FASTRAN, DKEFF) in background threads.
2. Security Enforcement: Performs pre-execution Integrity Checks (Hashing).
3. Audit Integration: Logs start/stop times and outcomes to the project audit trail.
4. Input Injection: Pipes data to the solver's STDIN (simulating user typing).
"""

import subprocess
import threading
import queue
import os
import time

# [SEC] Security Module for Integrity and Logging
import security 

def _execute_process(exe_path, input_str, working_dir, output_queue):
    """
    Generic worker to run a CLI tool safely.
    
    Args:
        exe_path (str): Absolute path to the executable.
        input_str (str): The text to 'type' into the console (STDIN).
        working_dir (str): The directory to run command in (Sandbox Root).
        output_queue (Queue): Where to send stdout lines for the GUI to read.
    """
    try:
        if not os.path.exists(exe_path):
            output_queue.put(f"ERROR: Executable not found at {exe_path}")
            return

        # Start the process
        # shell=False is CRITICAL for security (prevents injection)
        process = subprocess.Popen(
            [exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=working_dir,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        # Feed the inputs (simulate user typing)
        if input_str:
            output_queue.put(f"Sending Inputs:\n{input_str}")
            try:
                process.stdin.write(input_str)
                process.stdin.flush()
                process.stdin.close() # Signal EOF
            except IOError as e:
                output_queue.put(f"Error writing to stdin: {e}")

        # Stream the output line-by-line
        for line in iter(process.stdout.readline, ''):
            if line:
                output_queue.put(line.strip())

        process.stdout.close()
        return_code = process.wait()
        
        if return_code == 0:
            output_queue.put("\n--- PROCESS FINISHED SUCCESS ---")
        else:
            output_queue.put(f"\n--- PROCESS FAILED (Code {return_code}) ---")

    except Exception as e:
        output_queue.put(f"CRITICAL EXECUTION ERROR: {str(e)}")


def run_fastran(exe_path, input_file_abs, output_dir_abs, output_queue, project_root):
    """
    Runs the FASTRAN solver securely.
    
    Args:
        exe_path: Path to fastran.exe
        input_file_abs: Absolute path to the input file.
        output_dir_abs: Absolute path to the output folder.
        output_queue: Queue for log messages.
        project_root: The 'Jail' directory to run inside.
    """
    # ------------------------------------------------------------------
    # 1. SECURITY: INTEGRITY CHECK
    # ------------------------------------------------------------------
    try:
        # Verify this is the approved, un-tampered executable
        security.IntegrityChecker.verify_tool("fastran", exe_path)
    except security.SecurityError as e:
        output_queue.put(f"SECURITY BLOCK: {str(e)}")
        return

    # ------------------------------------------------------------------
    # 2. SECURITY: AUDIT LOGGING
    # ------------------------------------------------------------------
    try:
        # Setup Logger
        log_path = os.path.join(project_root, "config", "audit_trail.log")
        logger = security.AuditLogger(log_path)
        
        # Hash the Input File (Proof of what was analyzed)
        input_hash = security.IntegrityChecker.calculate_hash(input_file_abs)
        logger.log_event("ANALYSIS_START", f"Input Hash: {input_hash}")
    except:
        logger = None # Fail open on logging if file system error, or handle strictly

    # ------------------------------------------------------------------
    # 3. PATH PREPARATION
    # ------------------------------------------------------------------
    # FASTRAN assumes files are relative to CWD. We run inside project_root.
    input_rel = os.path.relpath(input_file_abs, project_root)
    
    # Construct output filename based on input name
    base_name = os.path.splitext(os.path.basename(input_file_abs))[0]
    output_rel = os.path.join(os.path.relpath(output_dir_abs, project_root), f"{base_name}.fou")

    # The input string FASTRAN expects:
    # Line 1: Input Filename
    # Line 2: Output Filename
    input_str = f"{input_rel}\n{output_rel}\n"

    # ------------------------------------------------------------------
    # 4. THREADED EXECUTION
    # ------------------------------------------------------------------
    def _threaded_wrapper():
        start_time = time.time()
        try:
            _execute_process(exe_path, input_str, project_root, output_queue)
            
            duration = time.time() - start_time
            if logger:
                logger.log_event("ANALYSIS_COMPLETE", f"Duration: {duration:.2f}s", status="SUCCESS")
                
        except Exception as e:
            if logger:
                logger.log_event("ANALYSIS_FAILED", str(e), status="ERROR")
            output_queue.put(f"Run Error: {e}")

    thread = threading.Thread(target=_threaded_wrapper, daemon=True)
    thread.start()


def run_dkeff(exe_path, dkin_file_abs, output_file_abs, ikeff_option, test_type, output_queue, project_root):
    """
    Runs DKEFF (Crack Opening Stress Analysis).
    Inputs derived from dkeff21f.for interaction logic.
    """
    # 1. Integrity Check
    try:
        security.IntegrityChecker.verify_tool("dkeff", exe_path)
    except security.SecurityError as e:
        output_queue.put(f"SECURITY BLOCK: {str(e)}")
        return

    # 2. Path Prep
    dkin_rel = os.path.relpath(dkin_file_abs, project_root)
    out_rel = os.path.relpath(output_file_abs, project_root)

    # 3. Input String Construction
    # Logic:
    # 1. Option (IKEFF)
    # 2. Test Type (Only if IKEFF=1)
    # 3. Input File
    # 4. Output File
    input_str = f"{ikeff_option}\n"
    if str(ikeff_option) == "1":
        input_str += f"{test_type}\n"
    input_str += f"{dkin_rel}\n"
    input_str += f"{out_rel}\n"

    # 4. Execution
    thread = threading.Thread(
        target=_execute_process,
        args=(exe_path, input_str, project_root, output_queue),
        daemon=True
    )
    thread.start()