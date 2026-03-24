# project.py
"""
project.py
----------
ProjectManager for the FASTRAN GUI.
Handles the creation, loading, and file management of the .frproj structure.
CRITICAL: Enforces security sandboxing via security.py to prevent path traversal.
"""

import os
import json
import shutil
from datetime import datetime

# [SEC] Import Security Module for PathGuard and AuditLogger
import security 

class ProjectManager:
    def __init__(self, project_path=None):
        self.project_path = project_path
        self.metadata = {}
        
        # Define the standard folder structure
        self.subfolders = {
            "input": "input",
            "output": "output",
            "config": "config",
            "plots": "plots"
        }

        if project_path and os.path.isdir(project_path):
            self.load_project(project_path)

    # ------------------------------------------------------------------
    # LIFECYCLE MANAGEMENT
    # ------------------------------------------------------------------
    def create_project(self, path, name="New Project"):
        """Creates a new structured project folder."""
        # Enforce extension
        if not path.endswith(".frproj"):
            path += ".frproj"
            
        self.project_path = path
        
        # Create directories safely
        os.makedirs(path, exist_ok=True)
        for folder in self.subfolders.values():
            os.makedirs(os.path.join(path, folder), exist_ok=True)

        # Initialize Metadata
        self.metadata = {
            "name": name,
            "created": datetime.now().isoformat(),
            "version": "3.0", # Schema version
            "files": self.subfolders
        }
        self._save_metadata()
        
        # [SEC] Log Creation
        try:
            logger = self.get_audit_logger()
            logger.log_event("PROJECT_CREATED", f"Name: {name}")
        except: pass

    def load_project(self, path):
        """Loads an existing project."""
        self.project_path = path
        meta_path = os.path.join(path, "config", "metadata.json")
        
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"Metadata Load Error: {e}")
                self.metadata = {"name": os.path.basename(path)}
        else:
            self.metadata = {"name": os.path.basename(path)}
            
        # [SEC] Log Access
        try:
            logger = self.get_audit_logger()
            logger.log_event("PROJECT_LOADED", f"Path: {path}")
        except: pass

    # ------------------------------------------------------------------
    # SECURE FILE ACCESS (The Sandbox)
    # ------------------------------------------------------------------
    def get_path(self, folder_key):
        """
        Returns the absolute path to a project subfolder (e.g., 'input').
        [SEC] Uses PathGuard to strictly enforce that the path is inside the project.
        """
        if not self.project_path:
            raise ValueError("No project loaded.")
            
        rel_path = self.subfolders.get(folder_key, "")
        full_path = os.path.join(self.project_path, rel_path)
        
        # Validate Path is inside Sandbox
        return security.PathGuard.validate_path(self.project_path, full_path)

    def get_relative_path(self, absolute_path):
        """Converts an absolute path to one relative to the project root."""
        if not self.project_path: return absolute_path
        return os.path.relpath(absolute_path, self.project_path)

    def get_audit_logger(self):
        """Returns the secure logger instance for this project."""
        if not self.project_path: return None
        
        # Log file lives in /config/audit_trail.log
        log_path = os.path.join(self.project_path, "config", "audit_trail.log")
        return security.AuditLogger(log_path)

    def clean_output(self):
        """Deletes old results to ensure data freshness."""
        out_dir = self.get_path("output")
        for f in os.listdir(out_dir):
            if f.endswith(".fou") or f.endswith(".out") or f.endswith(".txt"):
                try:
                    os.remove(os.path.join(out_dir, f))
                except OSError: pass

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def _save_metadata(self):
        meta_path = os.path.join(self.project_path, "config", "metadata.json")
        with open(meta_path, 'w') as f:
            json.dump(self.metadata, f, indent=4)
            
    def write_text_file(self, subfolder, filename, content):
        """
        Securely writes a text file to a subfolder.
        """
        dir_path = self.get_path(subfolder)
        full_path = os.path.join(dir_path, filename)
        
        # Double check security before write
        security.PathGuard.validate_path(self.project_path, full_path)
        
        with open(full_path, 'w') as f:
            f.write(content)
        return full_path