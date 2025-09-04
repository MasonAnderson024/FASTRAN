# project.py
"""
project.py
----------
ProjectManager for handling FASTRAN .frproj projects.

Each project is a folder with extension .frproj, containing:
- input/   (FASTRAN input files, all .txt)
- output/  (FASTRAN output files, all .txt)
- config/  (metadata.json, settings.json)
- plots/   (optional user-generated figures)
"""

import os
import json
from datetime import datetime


class ProjectManager:
    def __init__(self, project_path=None):
        self.project_path = project_path
        self.metadata = {}
        self.settings = {}
        if project_path and os.path.isdir(project_path):
            self.load_project(project_path)

    # ------------------------------
    # Project Creation
    # ------------------------------
    def create_project(self, path, name="New Project", fastran_version="5.4"):
        """
        Create a new .frproj project at given path.
        """
        if not path.endswith(".frproj"):
            path += ".frproj"
        os.makedirs(path, exist_ok=True)

        # Subfolders
        for sub in ["input", "output", "config", "plots"]:
            os.makedirs(os.path.join(path, sub), exist_ok=True)

        # Metadata
        now = datetime.now().isoformat()
        self.metadata = {
            "project_name": name,
            "created": now,
            "last_modified": now,
            "fastran_version": fastran_version,
            "schema_version": 1,
            "files": {
                "input": "input/case.txt",
                "driver": "input/driver.txt",
                "material": "input/material.txt",
                "results": "output/results.txt",
                "driver_out": "output/driver_out.txt",
                "errors": "output/errors.txt",
                "log": "output/log.txt"
            }
        }
        self.settings = {}  # empty GUI state initially

        # Save config files
        self._save_json(os.path.join(path, "config", "metadata.json"), self.metadata)
        self._save_json(os.path.join(path, "config", "settings.json"), self.settings)

        self.project_path = path
        return path

    # ------------------------------
    # Project Loading
    # ------------------------------
    def load_project(self, path):
        """
        Load existing .frproj project.
        """
        if not os.path.isdir(path):
            raise FileNotFoundError(f"Project folder not found: {path}")

        meta_file = os.path.join(path, "config", "metadata.json")
        settings_file = os.path.join(path, "config", "settings.json")

        if os.path.exists(meta_file):
            self.metadata = self._load_json(meta_file)
        else:
            raise FileNotFoundError("Missing metadata.json in project.")

        if os.path.exists(settings_file):
            self.settings = self._load_json(settings_file)
        else:
            self.settings = {}

        self.project_path = path
        return self.metadata, self.settings

    # ------------------------------
    # Saving Project State
    # ------------------------------
    def save_project(self, settings=None):
        """
        Save current metadata & settings back into project.
        """
        if not self.project_path:
            raise RuntimeError("No project loaded to save.")

        if settings is not None:
            self.settings = settings

        # Update timestamps
        self.metadata["last_modified"] = datetime.now().isoformat()

        self._save_json(os.path.join(self.project_path, "config", "metadata.json"), self.metadata)
        self._save_json(os.path.join(self.project_path, "config", "settings.json"), self.settings)

    # ------------------------------
    # File Access Helpers
    # ------------------------------
    def get_path(self, key):
        """
        Get absolute path to a known project file (e.g., "input", "results").
        """
        rel = self.metadata["files"].get(key)
        if not rel:
            raise KeyError(f"File key '{key}' not found in metadata.")
        return os.path.join(self.project_path, rel)

    def write_file(self, key, content):
        """
        Write text content to a project file by key.
        """
        fpath = self.get_path(key)
        with open(fpath, "w") as f:
            f.write(content)

    def read_file(self, key):
        """
        Read text content from a project file by key.
        """
        fpath = self.get_path(key)
        if not os.path.exists(fpath):
            return ""
        with open(fpath, "r") as f:
            return f.read()

    # ------------------------------
    # Internal JSON helpers
    # ------------------------------
    def _save_json(self, path, data):
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_json(self, path):
        with open(path, "r") as f:
            return json.load(f)
