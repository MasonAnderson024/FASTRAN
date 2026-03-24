# materials.py
"""
materials.py
------------
Material Library Manager for FASTRAN GUI.

Responsibilities:
1. Standardization: Saves/Loads material properties to JSON to prevent data entry errors.
2. Persistence: Maintains a local library of 'Approved' materials (e.g., Al-7075-T6.json).
3. Interoperability: Simple JSON format allows for easy auditing or external editing.
"""

import json
import os
import glob

class MaterialManager:
    def __init__(self, library_dir="materials"):
        """
        Args:
            library_dir (str): Folder where material files are stored.
                               Defaults to 'materials' in the app root.
        """
        self.materials_dir = library_dir
        
        # Ensure the library directory exists
        try:
            os.makedirs(self.materials_dir, exist_ok=True)
        except OSError:
            # In restricted environments, we might not have write access.
            # We proceed silently; save operations will just fail later.
            pass

    def save_material(self, name, properties_dict):
        """
        Saves a dictionary of material properties to a JSON file.
        
        Args:
            name (str): The display name of the material (e.g. "Ti-6Al-4V").
            properties_dict (dict): The Key-Value pairs from the GUI variables.
        """
        # Sanitize filename
        safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
        filename = f"{safe_name.replace(' ', '_')}.json"
        filepath = os.path.join(self.materials_dir, filename)
        
        # Filter: We only want to save relevant material keys, not the whole GUI state.
        # This list matches the keys defined in config.py related to materials.
        allowed_keys = {
            'MAT', 'SYIELD', 'SULT', 'E', 'ETA', 'ALP', 'BETAT', 'BETAW',
            'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7',
            'IRATE', 'NTAB', 'KTAB', 'NGC', 'NEQN'
        }
        
        clean_data = {k: v for k, v in properties_dict.items() if k in allowed_keys}
        
        # Ensure the Name field matches the file
        clean_data['MAT'] = name

        try:
            with open(filepath, 'w') as f:
                json.dump(clean_data, f, indent=4)
            return True, f"Material '{name}' saved successfully to library."
        except Exception as e:
            return False, f"Failed to save material: {str(e)}"

    def load_material(self, filepath):
        """
        Loads a material JSON file and returns the dictionary.
        """
        if not os.path.exists(filepath):
            return None
            
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return data
        except Exception:
            return None

    def get_available_materials(self):
        """
        Returns a list of tuples: (Material Name, Filepath)
        """
        files = glob.glob(os.path.join(self.materials_dir, "*.json"))
        results = []
        for f in files:
            name = os.path.splitext(os.path.basename(f))[0].replace('_', ' ')
            results.append((name, f))
        return results