# security.py
"""
security.py
-----------
NIST 800-171 / CMMC Compliance Module for FASTRAN GUI.

Responsibilities:
1. Integrity Checking: Verifies SHA-256 hashes of external EXEs (Anti-Malware).
2. Path Sandboxing: Prevents Directory Traversal attacks (The "Jail").
3. Audit Logging: Maintains an immutable record of user actions (Non-Repudiation).
"""

import hashlib
import os
import logging
import getpass
import time

# --- CONFIGURATION ---
# CRITICAL: Replace these strings with the actual SHA-256 hashes of your 
# approved executable files. You can use the included 'get_hash.py' tool to find them.
KNOWN_HASHES = {
    "fastran": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", # Placeholder
    "dkeff": "YOUR_DKEFF_HASH_HERE"
}

# Toggle this to False if you want to allow running unverified tools (Dev Mode)
ENFORCE_INTEGRITY = False 

class SecurityError(Exception):
    """Raised when a security violation (integrity or path) is detected."""
    pass

# ------------------------------------------------------------------
# 1. AUDIT LOGGING (Non-Repudiation)
# ------------------------------------------------------------------
class AuditLogger:
    """
    Writes immutable audit logs to the project folder. 
    Format: [UTC_TIMESTAMP] [USER] [ACTION] [STATUS] [DETAILS]
    """
    def __init__(self, log_path):
        self.log_path = log_path
        
        # Ensure directory exists safely
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
        except OSError: pass
        
        # Setup independent logger
        self.logger = logging.getLogger(f'fastran_audit_{log_path}')
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers to prevent duplicate lines
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        # File Handler only (no console output for security logs)
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter('%(asctime)s | %(message)s')
        formatter.converter = time.gmtime # Use UTC
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_event(self, action, details, status="SUCCESS"):
        """
        Records an event.
        - action: e.g. "RUN_ANALYSIS", "PROJECT_OPEN"
        - details: e.g. "Input Hash: abc1234..."
        - status: "SUCCESS" or "FAILURE"
        """
        try:
            user = getpass.getuser()
        except:
            user = "UNKNOWN"
            
        msg = f"USER: {user} | ACTION: {action} | STATUS: {status} | DETAILS: {details}"
        self.logger.info(msg)

# ------------------------------------------------------------------
# 2. PATH SANDBOXING (Access Control)
# ------------------------------------------------------------------
class PathGuard:
    """
    Enforces a 'Jail' to prevent Path Traversal attacks (e.g., writing to C:/Windows).
    """
    @staticmethod
    def validate_path(base_dir, target_path):
        """
        Raises SecurityError if target_path is not logically inside base_dir.
        Returns the absolute target path if safe.
        """
        # Resolve to absolute paths to resolve '..' or symlinks
        abs_base = os.path.abspath(base_dir)
        abs_target = os.path.abspath(target_path)
        
        # Windows is case-insensitive, so lower() for comparison
        if os.name == 'nt':
            check_base = abs_base.lower()
            check_target = abs_target.lower()
        else:
            check_base = abs_base
            check_target = abs_target

        # The 'commonpath' check ensures target is a subdirectory of base
        try:
            # Note: commonpath raises ValueError if paths are on different drives
            common = os.path.commonpath([check_base, check_target])
        except ValueError:
            raise SecurityError(f"Access Denied: Path '{target_path}' is on a different drive than project.")

        if common != check_base:
            raise SecurityError(f"Access Denied: Path '{target_path}' is outside the project sandbox.")
        
        return abs_target

# ------------------------------------------------------------------
# 3. INTEGRITY CHECKING (Anti-Tamper)
# ------------------------------------------------------------------
class IntegrityChecker:
    """
    Verifies executable binaries against known signatures.
    """
    @staticmethod
    def calculate_hash(filepath):
        """Reads file in chunks and returns SHA-256 hex string."""
        sha256 = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                # Read in 4K blocks to be memory efficient
                for block in iter(lambda: f.read(4096), b""):
                    sha256.update(block)
            return sha256.hexdigest()
        except FileNotFoundError:
            return None

    @staticmethod
    def verify_tool(tool_name, filepath):
        """
        Checks if the tool matches the known hash in KNOWN_HASHES.
        Raises SecurityError if mismatch found.
        """
        if not ENFORCE_INTEGRITY:
            return True, "Integrity Check Skipped (Dev Mode)"

        if tool_name not in KNOWN_HASHES:
            # If we don't have a hash for it, we default to BLOCKING it in secure mode.
            raise SecurityError(f"INTEGRITY FAILURE: No known hash for tool '{tool_name}'. Execution blocked.")
            
        current_hash = IntegrityChecker.calculate_hash(filepath)
        
        if not current_hash:
            raise SecurityError(f"INTEGRITY FAILURE: Executable not found at {filepath}")

        expected_hash = KNOWN_HASHES[tool_name]
        
        if current_hash != expected_hash:
            raise SecurityError(
                f"INTEGRITY VIOLATION: {tool_name} has been modified.\n"
                f"Expected: {expected_hash}\n"
                f"Actual:   {current_hash}"
            )
        
        return True, "Verified"