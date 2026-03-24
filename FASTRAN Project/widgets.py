# widgets.py
"""
widgets.py
----------
Custom Reusable UI Widgets for FASTRAN GUI.

Responsibilities:
1. GeometryCanvas: Renders schematic diagrams of fracture specimens (Center Crack, Compact Tension, etc.)
   using Matplotlib. This visual confirmation prevents geometry selection errors.
2. ToolTip: Provides hover-over help text for complex input fields.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib
import matplotlib.patches as patches
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Ensure we use the Tkinter backend for Matplotlib
matplotlib.use("TkAgg")

# ------------------------------------------------------------------
# 1. GEOMETRY SCHEMATIC (Visualizer)
# ------------------------------------------------------------------
class GeometryCanvas(tk.Frame):
    """
    A widget that draws a schematic representation of the selected FASTRAN geometry (NTYP).
    Uses Matplotlib to draw simple shapes (plates, cracks, holes) to guide the user.
    """
    def __init__(self, parent, width=300, height=200):
        super().__init__(parent, borderwidth=1, relief="sunken")
        
        # Create small figure for schematic
        self.figure = Figure(figsize=(3, 2), dpi=100)
        self.figure.patch.set_facecolor('#f0f0f0') # Match default GUI grey
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_axis_off() # We don't want graph coordinates, just the drawing
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_diagram(self, ntyp_id):
        """
        Clears the canvas and draws the schematic for the given NTYP ID.
        
        Args:
            ntyp_id (int): The FASTRAN geometry code (e.g. 1, 2, 5).
        """
        self.ax.clear()
        self.ax.set_axis_off()
        
        # Setup common drawing canvas (0-100 coordinate system)
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 100)
        
        try:
            ntyp = int(ntyp_id)
        except (ValueError, TypeError):
            self.canvas.draw()
            return

        # --- DRAWING LOGIC ---
        
        if ntyp == 1: # Center Crack Tension (M(T))
            self._draw_plate()
            # Draw Center Crack
            self.ax.add_patch(patches.Rectangle((40, 48), 20, 4, color='red', label='2a'))
            self._add_label(50, 55, "2a")
            self._add_label(50, 90, "Width (W)")
            # Arrows for tension
            self._draw_tension_arrows()

        elif ntyp == 2: # Compact Specimen C(T)
            # Draw C(T) shape
            path_x = [10, 90, 90, 10, 10]
            path_y = [20, 20, 80, 80, 20]
            self.ax.add_patch(patches.Polygon(list(zip(path_x, path_y)), closed=True, fill=False, edgecolor='black', linewidth=2))
            # Holes
            self.ax.add_patch(patches.Circle((25, 30), 5, fill=False, edgecolor='black'))
            self.ax.add_patch(patches.Circle((25, 70), 5, fill=False, edgecolor='black'))
            # Crack
            self.ax.add_patch(patches.Rectangle((10, 48), 40, 2, color='red'))
            self._add_label(30, 52, "a")
            self._add_label(95, 50, "W", color='black')

        elif ntyp == 3: # Single Edge Crack (Tension)
            self._draw_plate()
            # Crack from left edge
            self.ax.add_patch(patches.Rectangle((10, 48), 30, 2, color='red'))
            self._add_label(25, 55, "a")
            self._draw_tension_arrows()

        elif ntyp == 4: # Single Edge Bend (SE(B))
            # Plate
            self.ax.add_patch(patches.Rectangle((10, 30), 80, 40, fill=False, edgecolor='black', linewidth=2))
            # Crack from bottom
            self.ax.add_patch(patches.Rectangle((48, 30), 4, 20, color='red'))
            # Support rollers
            self.ax.add_patch(patches.Circle((20, 25), 3, color='blue'))
            self.ax.add_patch(patches.Circle((80, 25), 3, color='blue'))
            # Load arrow
            self.ax.arrow(50, 85, 0, -10, head_width=3, head_length=3, fc='blue', ec='blue')
            self._add_label(55, 40, "a")

        elif ntyp == 5: # Pressurized Cylinder
            # Draw Cylinder Cross section
            self.ax.add_patch(patches.Circle((50, 50), 40, fill=False, edgecolor='black', linewidth=2))
            self.ax.add_patch(patches.Circle((50, 50), 35, fill=False, edgecolor='black', linestyle='--'))
            # Crack on outer wall
            self.ax.add_patch(patches.Rectangle((85, 48), 10, 4, color='red'))
            self._add_label(50, 50, "Radius")
            self._add_label(90, 55, "a")

        elif ntyp == -1: # Corner Crack at Hole
            self._draw_plate()
            # Draw Hole
            self.ax.add_patch(patches.Circle((50, 50), 12, fill=False, edgecolor='black'))
            # Draw Corner Crack (Triangle-ish)
            self.ax.add_patch(patches.Polygon([[62, 50], [70, 50], [62, 58]], color='red'))
            self._add_label(72, 55, "c")
            self._add_label(50, 30, "Dia")

        elif ntyp == -12: # Lap Splice Joint
            # Draw two overlapping plates
            self.ax.add_patch(patches.Rectangle((10, 40), 60, 40, fill=False, edgecolor='black', linewidth=1.5)) # Top
            self.ax.add_patch(patches.Rectangle((30, 10), 60, 40, fill=False, edgecolor='blue', linestyle='--', linewidth=1.5)) # Bottom
            # Fastener
            self.ax.add_patch(patches.Circle((50, 45), 4, color='black'))
            self._add_label(50, 55, "Rivet")
            # Crack
            self.ax.add_patch(patches.Rectangle((54, 45), 10, 2, color='red'))

        else:
            self.ax.text(50, 50, f"Schematic N/A\n(Type {ntyp})", ha='center', fontsize=10)

        self.canvas.draw()

    # --- DRAWING HELPERS ---

    def _draw_plate(self):
        """Helper to draw a standard rectangular specimen."""
        self.ax.add_patch(patches.Rectangle((10, 10), 80, 80, fill=False, edgecolor='black', linewidth=2))

    def _draw_tension_arrows(self):
        """Helper to draw Up/Down loading arrows."""
        # Top Arrow
        self.ax.arrow(50, 92, 0, 5, head_width=3, head_length=3, fc='blue', ec='blue')
        # Bottom Arrow
        self.ax.arrow(50, 8, 0, -5, head_width=3, head_length=3, fc='blue', ec='blue')

    def _add_label(self, x, y, text, color='blue'):
        """Helper to add text labels."""
        self.ax.text(x, y, text, ha='center', fontsize=9, color=color, fontweight='bold')


# ------------------------------------------------------------------
# 2. TOOLTIP (Context Help)
# ------------------------------------------------------------------
class ToolTip:
    """
    Creates a small pop-up window with help text when the user hovers 
    over a widget. Essential for explaining cryptic variable names 
    like 'BETAW' or 'IPLOT'.
    """
    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(600, self.showtip) # 600ms delay before showing

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def showtip(self):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True) # Remove window borders
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.tooltip_window, 
            text=self.text, 
            justify='left',
            background="#ffffe0", # Light yellow
            relief='solid', 
            borderwidth=1,
            font=("Segoe UI", "8", "normal")
        )
        label.pack(ipadx=1)

    def hidetip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None