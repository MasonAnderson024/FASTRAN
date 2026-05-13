# runners.py
"""
runners.py
----------
Secure Execution Engine for FASTRAN GUI.

Responsibilities:
1. Process Management: Runs FASTRAN and DKEFF in background threads.
2. Security Enforcement: Performs pre-execution integrity checks (SHA-256 hashing).
3. Audit Integration: Logs analysis events to the project audit trail.
4. Blocking Variant: run_fastran_blocking() for use inside batch threads.
"""

import subprocess
import threading
import queue
import os
import time

import security


class RunHandle:
    """
    Holds a reference to the running FASTRAN subprocess so the GUI can cancel it.
    Created by run_fastran() and stored on the GUI instance.
    """
    def __init__(self):
        self._process = None

    def cancel(self):
        """Terminate the subprocess if it is still running."""
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
            except Exception:
                pass


def _execute_process(exe_path, input_str, working_dir, output_queue, handle=None):
    """
    Generic worker: runs a CLI executable, pipes input_str to stdin,
    and streams stdout/stderr to output_queue.

    The final message on the queue is either:
      "--- PROCESS FINISHED SUCCESS ---"  or  "--- PROCESS FAILED (Code N) ---"
    """
    try:
        if not os.path.exists(exe_path):
            output_queue.put(f"ERROR: Executable not found at {exe_path}")
            return

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
        if handle is not None:
            handle._process = process

        if input_str:
            try:
                process.stdin.write(input_str)
                process.stdin.flush()
                process.stdin.close()
            except IOError as e:
                output_queue.put(f"STDIN write error: {e}")

        for line in iter(process.stdout.readline, ''):
            if line:
                output_queue.put(line.strip())

        process.stdout.close()
        rc = process.wait()

        if rc == 0:
            output_queue.put("--- PROCESS FINISHED SUCCESS ---")
        else:
            output_queue.put(f"--- PROCESS FAILED (Code {rc}) ---")

    except Exception as e:
        output_queue.put(f"CRITICAL EXECUTION ERROR: {str(e)}")


# ------------------------------------------------------------------
# FASTRAN  — Asynchronous (standard use)
# ------------------------------------------------------------------
def run_fastran(exe_path, input_file_abs, output_dir_abs, output_queue, project_root):
    """
    Runs the FASTRAN solver in a daemon thread.

    Returns a RunHandle whose .cancel() method terminates the subprocess.

    Args:
        exe_path:        Path to fastran.exe
        input_file_abs:  Absolute path to the .txt input file
        output_dir_abs:  Absolute path to the output directory
        output_queue:    Queue for GUI log messages
        project_root:    Project root used as the subprocess working directory
    """
    handle = RunHandle()

    try:
        security.IntegrityChecker.verify_tool("fastran", exe_path)
    except security.SecurityError as e:
        output_queue.put(f"SECURITY BLOCK: {str(e)}")
        return handle

    logger = None
    try:
        log_path = os.path.join(project_root, "config", "audit_trail.log")
        logger = security.AuditLogger(log_path)
        input_hash = security.IntegrityChecker.calculate_hash(input_file_abs)
        logger.log_event("ANALYSIS_START", f"Input Hash: {input_hash}")
    except Exception:
        pass

    input_rel = os.path.relpath(input_file_abs, project_root)
    base_name = os.path.splitext(os.path.basename(input_file_abs))[0]
    output_rel = os.path.join(
        os.path.relpath(output_dir_abs, project_root), f"{base_name}.fou"
    )
    input_str = f"{input_rel}\n{output_rel}\n"

    def _threaded_wrapper():
        start = time.time()
        try:
            _execute_process(exe_path, input_str, project_root, output_queue, handle)
            if logger:
                logger.log_event("ANALYSIS_COMPLETE",
                                 f"Duration: {time.time()-start:.2f}s", status="SUCCESS")
        except Exception as e:
            if logger:
                logger.log_event("ANALYSIS_FAILED", str(e), status="ERROR")
            output_queue.put(f"Run Error: {e}")

    threading.Thread(target=_threaded_wrapper, daemon=True).start()
    return handle


# ------------------------------------------------------------------
# FASTRAN  — Blocking (for batch mode — called inside a worker thread)
# ------------------------------------------------------------------
def run_fastran_blocking(exe_path, input_file_abs, output_dir_abs, project_root):
    """
    Runs FASTRAN synchronously (blocks until complete).
    Use ONLY inside a background thread (e.g., batch analysis worker).

    Returns:
        (success: bool, message: str)
    """
    try:
        security.IntegrityChecker.verify_tool("fastran", exe_path)
    except security.SecurityError as e:
        return False, f"SECURITY BLOCK: {str(e)}"

    if not os.path.exists(exe_path):
        return False, f"Executable not found: {exe_path}"

    input_rel = os.path.relpath(input_file_abs, project_root)
    base_name = os.path.splitext(os.path.basename(input_file_abs))[0]
    output_rel = os.path.join(
        os.path.relpath(output_dir_abs, project_root), f"{base_name}.fou"
    )
    input_str = f"{input_rel}\n{output_rel}\n"

    try:
        result = subprocess.run(
            [exe_path],
            input=input_str,
            capture_output=True,
            text=True,
            cwd=project_root,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            timeout=300
        )
        if result.returncode == 0:
            return True, "Success"
        else:
            return False, f"FASTRAN exited with code {result.returncode}"
    except subprocess.TimeoutExpired:
        return False, "FASTRAN timed out after 5 minutes"
    except Exception as e:
        return False, str(e)


# ------------------------------------------------------------------
# DKEFF  — Asynchronous (called from DkeffWindow)
# ------------------------------------------------------------------
def run_dkeff(exe_path, dkin_file_abs, output_file_abs, test_type, output_queue,
              version="dkeff13"):
    """
    Runs the DKEFF utility in a daemon thread.

    Signature matches what DkeffWindow calls:
        runners.run_dkeff(exe_path, dkin_path, dkout_path, test_type_code, queue)
    Optional `version` kwarg selects the stdin protocol.

    Args:
        exe_path:        Path to dkeff13.exe or dkeff21f.exe
        dkin_file_abs:   Absolute path to the prepared .dkin input file
        output_file_abs: Absolute path for the .dkout output file
        test_type:       '0' = Constant-R test, '1' = Kmax test
        output_queue:    Queue for messages back to the GUI
        version:         'dkeff13' or 'dkeff21' (controls stdin protocol)
    """
    try:
        security.IntegrityChecker.verify_tool("dkeff", exe_path)
    except security.SecurityError as e:
        output_queue.put(f"SECURITY BLOCK: {str(e)}")
        return

    # Build working directory relative to the exe so relative paths work
    working_dir = os.path.dirname(os.path.abspath(exe_path))
    dkin_rel = os.path.relpath(dkin_file_abs, working_dir)
    out_rel = os.path.relpath(output_file_abs, working_dir)

    # dkeff13 stdin protocol:
    #   Line 1: IKEFF  (1 = from file, 2 = elastic only)
    #   Line 2: test type (0 = constant-R, 1 = Kmax)  — only if IKEFF=1
    #   Line 3: input filename
    #   Line 4: output filename
    #
    # dkeff21f stdin protocol differs: IKEFF prompt is removed; it goes directly
    # to test type, input file, output file. Update this block when dkeff21 is
    # available and its exact prompts are confirmed.
    if "21" in version:
        input_str = f"{test_type}\n{dkin_rel}\n{out_rel}\n"
    else:
        # dkeff13 default
        input_str = f"1\n{test_type}\n{dkin_rel}\n{out_rel}\n"

    def _notify_done():
        """Translates the generic finish token to the token DkeffWindow expects."""
        inner_q = queue.Queue()
        _execute_process(exe_path, input_str, working_dir, inner_q)
        while True:
            try:
                msg = inner_q.get(timeout=0.2)
                if "PROCESS FINISHED SUCCESS" in msg:
                    output_queue.put("DONE")
                    return
                elif "ERROR" in msg or "FAILED" in msg:
                    output_queue.put(f"ERROR: {msg}")
                    return
            except queue.Empty:
                pass

    threading.Thread(target=_notify_done, daemon=True).start()
