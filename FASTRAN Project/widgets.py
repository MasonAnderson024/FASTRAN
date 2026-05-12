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

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from contextlib import contextmanager
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

        self.current_ntyp = None
        self.current_dims = {}  # latest dim values pushed by the main GUI

        # View-toggle and export-target state
        self.show_plan    = tk.BooleanVar(value=True)
        self.show_section = tk.BooleanVar(value=True)
        self.export_target = tk.StringVar(value="Both")

        # Taller figure: top = plan view, bottom = cross-section view
        self.figure = Figure(figsize=(5, 4.5), dpi=100)
        self.figure.patch.set_facecolor('#f0f0f0')

        self.ax = self.figure.add_subplot(121)
        self.ax.set_axis_off()

        self.ax_cs = self.figure.add_subplot(122)
        self.ax_cs.set_axis_off()

        # Button row sits at the bottom; canvas takes the remaining space.
        btn_row = ttk.Frame(self)
        btn_row.pack(side='bottom', fill='x', padx=4, pady=(2, 4))

        ttk.Button(btn_row, text="Save Image...", command=self.save_image).pack(side='left', padx=2)
        ttk.Button(btn_row, text="Copy",          command=self.copy_to_clipboard).pack(side='left', padx=2)

        ttk.Separator(btn_row, orient='vertical').pack(side='left', fill='y', padx=5)

        ttk.Label(btn_row, text="Show:").pack(side='left')
        ttk.Checkbutton(btn_row, text="Plan",    variable=self.show_plan,
                        command=self._update_view_layout).pack(side='left')
        ttk.Checkbutton(btn_row, text="Section", variable=self.show_section,
                        command=self._update_view_layout).pack(side='left', padx=(0, 2))

        ttk.Separator(btn_row, orient='vertical').pack(side='left', fill='y', padx=5)

        ttk.Label(btn_row, text="Export:").pack(side='left')
        ttk.Combobox(btn_row, textvariable=self.export_target, width=9, state='readonly',
                     values=["Both", "Plan View", "Section A–A"]).pack(side='left', padx=2)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(side='top', fill=tk.BOTH, expand=True)

        # Set initial axis positions (both visible)
        self._update_view_layout()

    def update_diagram(self, ntyp_id, dims=None):
        """
        Clears the canvas and draws the schematic for the given NTYP ID.

        Args:
            ntyp_id (int): The FASTRAN geometry code (e.g. 1, 2, 5).
            dims (dict, optional): Current dimension values keyed by FASTRAN variable
                name (W, B, CI, CF, AI, AN, CN, RAD).  When provided the crack and
                feature sizes in the schematic scale proportionally so the diagram
                reflects the user's actual inputs.
        """
        if dims is not None:
            self.current_dims = dims

        self.ax.clear()
        self.ax.set_axis_off()
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 100)

        self.ax_cs.clear()
        self.ax_cs.set_axis_off()
        self.ax_cs.set_xlim(0, 100)
        self.ax_cs.set_ylim(0, 100)

        try:
            ntyp = int(ntyp_id)
        except (ValueError, TypeError):
            self.current_ntyp = None
            self.canvas.draw()
            return
        self.current_ntyp = ntyp

        self.ax.set_title("Plan View", fontsize=8, pad=2)
        self.ax_cs.set_title("Section A–A", fontsize=8, pad=2)

        # --- DRAWING LOGIC ---

        if ntyp == 0:  # Surface Crack (Tension/Bending)
            self._draw_plate()
            c_w = self._crack_half_px(default=11) * 2  # 2c width
            self.ax.add_patch(patches.Ellipse((50, 90), c_w, 6, color='red'))
            self._draw_tension_arrows()
            self._add_label(50, 80, f"2c={self._dim('CI', '?'):.4g}" if self._dim('CI') else "2c")
            self.ax.annotate("", xy=(20, 60), xytext=(20, 90),
                             arrowprops=dict(arrowstyle='<->', color='blue'))
            self._add_label(15, 75, "B", color='blue')

        elif ntyp == 1:  # Center Crack Tension (M(T))
            self._draw_plate()
            a_px = self._crack_half_px(default=10)
            self.ax.add_patch(patches.Rectangle((50 - a_px, 48), 2 * a_px, 4, color='red'))
            self._add_label(50, 55, f"2a={self._dim('CI', '?'):.4g}" if self._dim('CI') else "2a")
            self._add_label(50, 90, f"W={self._dim('W', '?'):.4g}" if self._dim('W') else "W")
            self._draw_tension_arrows()

        elif ntyp == 2:  # Compact Specimen C(T)
            path_x = [10, 90, 90, 10, 10]
            path_y = [20, 20, 80, 80, 20]
            self.ax.add_patch(patches.Polygon(list(zip(path_x, path_y)), closed=True,
                                              fill=False, edgecolor='black', linewidth=2))
            self.ax.add_patch(patches.Circle((25, 30), 5, fill=False, edgecolor='black'))
            self.ax.add_patch(patches.Circle((25, 70), 5, fill=False, edgecolor='black'))
            a_px = self._crack_full_px(default=40)
            self.ax.add_patch(patches.Rectangle((10, 48), a_px, 2, color='red'))
            self._add_label(10 + a_px / 2, 53, f"a={self._dim('CI', '?'):.4g}" if self._dim('CI') else "a")
            self._add_label(95, 50, "W", color='black')

        elif ntyp == 3:  # Single Edge Crack (Tension)
            self._draw_plate()
            a_px = self._crack_full_px(default=30)
            self.ax.add_patch(patches.Rectangle((10, 48), a_px, 2, color='red'))
            self._add_label(10 + a_px / 2, 55, f"a={self._dim('CI', '?'):.4g}" if self._dim('CI') else "a")
            self._draw_tension_arrows()

        elif ntyp == 4:  # Single Edge Bend (SE(B))
            self.ax.add_patch(patches.Rectangle((10, 30), 80, 40,
                                                fill=False, edgecolor='black', linewidth=2))
            a_px = self._crack_full_px(lo=4, hi=36, default=20)
            self.ax.add_patch(patches.Rectangle((48, 30), 4, a_px, color='red'))
            self.ax.add_patch(patches.Circle((20, 25), 3, color='blue'))
            self.ax.add_patch(patches.Circle((80, 25), 3, color='blue'))
            self.ax.arrow(50, 85, 0, -10, head_width=3, head_length=3, fc='blue', ec='blue')
            self._add_label(56, 30 + a_px / 2,
                            f"a={self._dim('CI', '?'):.4g}" if self._dim('CI') else "a")

        elif ntyp == 5: # Pressurized Cylinder
            # Draw Cylinder Cross section
            self.ax.add_patch(patches.Circle((50, 50), 40, fill=False, edgecolor='black', linewidth=2))
            self.ax.add_patch(patches.Circle((50, 50), 35, fill=False, edgecolor='black', linestyle='--'))
            # Crack on outer wall
            self.ax.add_patch(patches.Rectangle((85, 48), 10, 4, color='red'))
            self._add_label(50, 50, "Radius")
            self._add_label(90, 55, "a")

        elif ntyp == 6:  # Corner Crack a=c in Square-Bar (AGARD)
            self.ax.add_patch(patches.Rectangle((20, 20), 60, 60, fill=False,
                                                edgecolor='black', linewidth=2))
            # Quarter-ellipse at top-right corner
            self.ax.add_patch(patches.Wedge((80, 80), 14, 180, 270, color='red'))
            self._add_label(75, 70, "a=c")
            self._add_label(50, 13, "Square Bar")

        elif ntyp == 7:  # Corner Crack in Plate (Tension/Bending)
            self._draw_plate()
            self.ax.add_patch(patches.Wedge((90, 90), 14, 180, 270, color='red'))
            self._draw_tension_arrows()
            self._add_label(80, 80, "a, c")

        elif ntyp == 8:  # Double-Edge Crack Tension D(T)
            self._draw_plate()
            a_px = self._crack_full_px(lo=4, hi=35, default=22)
            self.ax.add_patch(patches.Rectangle((10, 48), a_px, 4, color='red'))
            self.ax.add_patch(patches.Rectangle((90 - a_px, 48), a_px, 4, color='red'))
            self._draw_tension_arrows()
            lbl = f"a={self._dim('CI', '?'):.4g}" if self._dim('CI') else "a"
            self._add_label(10 + a_px / 2, 56, lbl)
            self._add_label(90 - a_px / 2, 56, lbl)

        elif ntyp == 99:  # User-Defined Geometry
            self.ax.add_patch(patches.Rectangle((20, 30), 60, 40, fill=False,
                                                edgecolor='gray', linestyle='--'))
            self.ax.text(50, 50, "User-Defined Geometry\n(Fc vs c/w table)",
                         ha='center', va='center', fontsize=10, fontstyle='italic')

        elif ntyp == -1:  # Corner Crack at Hole
            self._draw_plate()
            r_px = self._hole_px(default=12)
            a_px = self._crack_full_px(lo=3, hi=25, default=8)
            self.ax.add_patch(patches.Circle((50, 50), r_px, fill=False, edgecolor='black'))
            cx = 50 + r_px
            self.ax.add_patch(patches.Polygon(
                [[cx, 50], [cx + a_px, 50], [cx, 50 + a_px]], color='red'))
            self._add_label(cx + a_px + 4, 53, f"c={self._dim('CI', '?'):.4g}" if self._dim('CI') else "c")
            self._add_label(50, 50 - r_px - 6, f"R={self._dim('RAD', '?'):.4g}" if self._dim('RAD') else "Dia")

        elif ntyp == -2:  # Two Corner Cracks at Hole
            self._draw_plate()
            r_px = self._hole_px(default=12)
            a_px = self._crack_full_px(lo=3, hi=20, default=8)
            self.ax.add_patch(patches.Circle((50, 50), r_px, fill=False, edgecolor='black'))
            cx = 50 + r_px
            self.ax.add_patch(patches.Polygon([[cx, 50], [cx + a_px, 50], [cx, 50 + a_px]], color='red'))
            cx2 = 50 - r_px
            self.ax.add_patch(patches.Polygon([[cx2, 50], [cx2 - a_px, 50], [cx2, 50 + a_px]], color='red'))
            self._add_label(50, 50 - r_px - 6, f"R={self._dim('RAD', '?'):.4g}" if self._dim('RAD') else "Dia")

        elif ntyp == -3:  # One Through Crack at Hole
            self._draw_plate()
            r_px = self._hole_px(default=10)
            a_px = self._crack_full_px(lo=4, hi=30, default=20)
            self.ax.add_patch(patches.Circle((50, 50), r_px, fill=False, edgecolor='black'))
            self.ax.add_patch(patches.Rectangle((50 + r_px, 49), a_px, 2, color='red'))
            self._add_label(50 + r_px + a_px / 2, 55,
                            f"c={self._dim('CI', '?'):.4g}" if self._dim('CI') else "c")
            self._add_label(50, 50 - r_px - 6, f"R={self._dim('RAD', '?'):.4g}" if self._dim('RAD') else "Dia")

        elif ntyp == -4:  # Two Through Cracks at Hole
            self._draw_plate()
            r_px = self._hole_px(default=10)
            a_px = self._crack_full_px(lo=4, hi=28, default=18)
            self.ax.add_patch(patches.Circle((50, 50), r_px, fill=False, edgecolor='black'))
            self.ax.add_patch(patches.Rectangle((50 + r_px, 49), a_px, 2, color='red'))
            self.ax.add_patch(patches.Rectangle((50 - r_px - a_px, 49), a_px, 2, color='red'))
            self._add_label(50, 50 - r_px - 6, f"R={self._dim('RAD', '?'):.4g}" if self._dim('RAD') else "Dia")

        elif ntyp == -5:  # One Surface Crack at Center of Hole (bore)
            self._draw_plate()
            self.ax.add_patch(patches.Circle((50, 50), 12, fill=False, edgecolor='black'))
            # Surface crack on bore wall (right side, mid-thickness)
            self.ax.add_patch(patches.Ellipse((62, 50), 5, 12, color='red'))
            self._add_label(72, 50, "2c (bore)")

        elif ntyp == -6:  # Two Surface Cracks at Center of Hole (bore)
            self._draw_plate()
            self.ax.add_patch(patches.Circle((50, 50), 12, fill=False, edgecolor='black'))
            self.ax.add_patch(patches.Ellipse((62, 50), 5, 12, color='red'))
            self.ax.add_patch(patches.Ellipse((38, 50), 5, 12, color='red'))
            self._add_label(50, 30, "2c (each side)")

        elif ntyp == -7:  # Surface Crack at Semi-Circular Edge Notch
            self._draw_plate()
            self._draw_edge_notch(side='left', y=50, radius=8)
            self.ax.add_patch(patches.Ellipse((25, 50), 12, 4, color='red'))
            self._add_label(25, 60, "2c")
            self._add_label(15, 70, "Notch")

        elif ntyp == -8:  # Through Crack at Semi-Circular Edge Notch
            self._draw_plate()
            self._draw_edge_notch(side='left', y=50, radius=8)
            self.ax.add_patch(patches.Rectangle((18, 49), 22, 2, color='red'))
            self._add_label(28, 56, "c")
            self._add_label(15, 70, "Notch")

        elif ntyp == -9:  # Corner Crack at Semi-Circular Edge Notch
            self._draw_plate()
            self._draw_edge_notch(side='left', y=50, radius=8)
            self.ax.add_patch(patches.Wedge((18, 50), 8, 270, 360, color='red'))
            self._add_label(30, 50, "c")
            self._add_label(15, 70, "Notch")

        elif ntyp == -10:  # Through Cracks at Holes (Pin Load + Moment γ)
            self._draw_plate()
            for cx in (30, 70):
                self.ax.add_patch(patches.Circle((cx, 50), 8, fill=False, edgecolor='black'))
                self.ax.add_patch(patches.Circle((cx, 50), 6, color='gray'))  # pin
            self.ax.add_patch(patches.Rectangle((38, 49), 8, 2, color='red'))
            self.ax.add_patch(patches.Rectangle((54, 49), 8, 2, color='red'))
            self._add_label(50, 30, "Pin Load")

        elif ntyp == -11:  # Periodic Through Cracks at Holes
            self._draw_plate()
            for cx in (25, 50, 75):
                self.ax.add_patch(patches.Circle((cx, 50), 4, fill=False, edgecolor='black'))
                self.ax.add_patch(patches.Rectangle((cx + 4, 49), 7, 2, color='red'))
            self._draw_tension_arrows()
            self._add_label(50, 30, "Periodic spacing")

        elif ntyp == -12: # Lap Splice Joint
            # Draw two overlapping plates
            self.ax.add_patch(patches.Rectangle((10, 40), 60, 40, fill=False, edgecolor='black', linewidth=1.5)) # Top
            self.ax.add_patch(patches.Rectangle((30, 10), 60, 40, fill=False, edgecolor='blue', linestyle='--', linewidth=1.5)) # Bottom
            # Fastener
            self.ax.add_patch(patches.Circle((50, 45), 4, color='black'))
            self._add_label(50, 55, "Rivet")
            # Crack
            self.ax.add_patch(patches.Rectangle((54, 45), 10, 2, color='red'))

        elif ntyp == -13:  # Lap-Splice Joint — Corner Cracks
            self.ax.add_patch(patches.Rectangle((10, 40), 60, 40, fill=False,
                                                edgecolor='black', linewidth=1.5))
            self.ax.add_patch(patches.Rectangle((30, 10), 60, 40, fill=False,
                                                edgecolor='blue', linestyle='--', linewidth=1.5))
            self.ax.add_patch(patches.Circle((50, 45), 4, color='black'))
            self._add_label(50, 60, "Rivet")
            # Corner crack (quarter ellipse)
            self.ax.add_patch(patches.Wedge((54, 45), 6, 0, 90, color='red'))

        elif ntyp == -14:  # Surface Crack at Edge Notch Bend
            # Bend specimen plate
            self.ax.add_patch(patches.Rectangle((10, 30), 80, 40, fill=False,
                                                edgecolor='black', linewidth=2))
            # Edge notch on bottom
            self.ax.add_patch(patches.Wedge((50, 30), 8, 0, 180, fc='#f0f0f0', ec='none'))
            self.ax.add_patch(patches.Arc((50, 30), 16, 16, theta1=0, theta2=180,
                                          color='black', linewidth=2))
            # Surface crack at notch root
            self.ax.add_patch(patches.Ellipse((50, 42), 12, 4, color='red'))
            # Supports + load
            self.ax.add_patch(patches.Circle((20, 25), 3, color='blue'))
            self.ax.add_patch(patches.Circle((80, 25), 3, color='blue'))
            self.ax.arrow(50, 85, 0, -10, head_width=3, head_length=3, fc='blue', ec='blue')
            self._add_label(50, 50, "2c")

        elif ntyp == -15:  # Through Crack at Edge Notch Bend
            self.ax.add_patch(patches.Rectangle((10, 30), 80, 40, fill=False,
                                                edgecolor='black', linewidth=2))
            self.ax.add_patch(patches.Wedge((50, 30), 8, 0, 180, fc='#f0f0f0', ec='none'))
            self.ax.add_patch(patches.Arc((50, 30), 16, 16, theta1=0, theta2=180,
                                          color='black', linewidth=2))
            # Through crack from notch root (vertical strip)
            self.ax.add_patch(patches.Rectangle((49, 38), 2, 18, color='red'))
            self.ax.add_patch(patches.Circle((20, 25), 3, color='blue'))
            self.ax.add_patch(patches.Circle((80, 25), 3, color='blue'))
            self.ax.arrow(50, 85, 0, -10, head_width=3, head_length=3, fc='blue', ec='blue')
            self._add_label(56, 48, "c")

        elif ntyp == -99:  # User-Defined Crack at Hole/Notch
            self.ax.add_patch(patches.Rectangle((20, 30), 60, 40, fill=False,
                                                edgecolor='gray', linestyle='--'))
            self.ax.add_patch(patches.Circle((50, 50), 6, fill=False, edgecolor='gray',
                                             linestyle='--'))
            self.ax.text(50, 18, "User-Defined Crack at Hole/Notch\n(fct vs crk/w table)",
                         ha='center', fontsize=9, fontstyle='italic')

        else:
            self.ax.text(50, 50, f"Schematic N/A\n(Type {ntyp})", ha='center', fontsize=10)

        self._draw_cross_section(ntyp)
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

    def _draw_edge_notch(self, side='left', y=50, radius=8):
        """
        Draw a semi-circular edge notch on the plate.
        Bulges into the plate from the named side. Uses canvas-color fill to
        'erase' the plate edge inside the notch, then draws the curved arc.
        """
        if side == 'left':
            x = 10
            theta1, theta2 = 270, 90  # right half of circle (bulges into plate)
        elif side == 'right':
            x = 90
            theta1, theta2 = 90, 270  # left half (bulges into plate)
        else:
            return
        self.ax.add_patch(patches.Wedge((x, y), radius, theta1, theta2,
                                        fc='#f0f0f0', ec='none'))
        self.ax.add_patch(patches.Arc((x, y), 2 * radius, 2 * radius,
                                      theta1=theta1, theta2=theta2,
                                      color='black', linewidth=2))

    # --- DIMENSION HELPERS ---
    # These convert real-world dims stored in self.current_dims into canvas-pixel
    # lengths so the schematic scales with user input.  The plan-view plate spans
    # x=10..90 (80 units wide) and y=10..90 (80 units tall).

    def _dim(self, key, default=0.0):
        """Return a dimension value, falling back to *default* when absent or zero."""
        v = self.current_dims.get(key, default)
        try:
            v = float(v)
        except (TypeError, ValueError):
            v = default
        return v if v > 0 else default

    def _crack_half_px(self, lo=3, hi=38, default=10):
        """Half-crack length in plan-view canvas pixels (CI / W * 40)."""
        w = self._dim('W'); ci = self._dim('CI')
        if w > 0 and ci > 0:
            return max(lo, min(hi, ci / w * 40))
        return default

    def _crack_full_px(self, lo=4, hi=76, default=30):
        """Full crack length from one edge (CI / W * 80)."""
        w = self._dim('W'); ci = self._dim('CI')
        if w > 0 and ci > 0:
            return max(lo, min(hi, ci / w * 80))
        return default

    def _depth_px(self, lo=5, hi=70, default=24):
        """Crack depth in cross-section canvas pixels (AI / B * 80)."""
        b = self._dim('B'); ai = self._dim('AI')
        if b > 0 and ai > 0:
            return max(lo, min(hi, ai / b * 80))
        return default

    def _hole_px(self, lo=5, hi=28, default=12):
        """Hole radius in canvas pixels (RAD / W * 80)."""
        w = self._dim('W'); rad = self._dim('RAD')
        if w > 0 and rad > 0:
            return max(lo, min(hi, rad / w * 80))
        return default

    def _final_crack_px(self, lo=4, hi=76, default=40):
        """Final crack half-length in plan-view canvas pixels (CF / W * 40)."""
        w = self._dim('W'); cf = self._dim('CF')
        if w > 0 and cf > 0:
            return max(lo, min(hi, cf / w * 40))
        return default

    # --- CROSS-SECTION DRAWING ---

    def _draw_cross_section(self, ntyp):
        """Draw the through-thickness cross-section view for the right subplot."""
        ax = self.ax_cs
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)

        if ntyp == 0:   # Surface Crack – semi-ellipse from top face
            self._cs_rect(ax)
            c_w = self._crack_half_px(default=14) * 2
            a_d = self._depth_px(default=24)
            self._cs_surface_crack(ax, cx=50, face='top', crack_w=c_w, crack_h=a_d)
            self._cs_ann_B(ax)
            lbl_2c = f"2c={self._dim('CI', '?'):.4g}" if self._dim('CI') else "2c"
            self._cs_label(ax, 50, 94, lbl_2c, color='red')

        elif ntyp == 1:  # Center Crack Tension – through crack at mid-width
            self._cs_rect(ax)
            self._cs_through_crack(ax, cx=50)
            self._cs_ann_B(ax)
            self._cs_label(ax, 60, 50, "Full\nthick.", color='red', fontsize=7)

        elif ntyp == 2:  # Compact Tension – through crack from left notch
            self._cs_rect(ax)
            self._cs_through_crack(ax, cx=50)
            self._cs_ann_B(ax)
            self._cs_label(ax, 58, 50, "a", color='red')

        elif ntyp == 3:  # Single Edge Crack (Tension) – through crack from left
            self._cs_rect(ax)
            self._cs_through_crack(ax, cx=15 + 4)
            self._cs_ann_B(ax)
            self._cs_label(ax, 35, 50, "a", color='red')

        elif ntyp == 4:  # Single Edge Bend – through crack from bottom
            self._cs_rect(ax)
            ax.add_patch(patches.Rectangle((46, 10), 8, 40, color='red'))
            self._cs_ann_B(ax)
            self._cs_label(ax, 60, 30, "a", color='red')

        elif ntyp == 5:  # Pressurized Cylinder – radial crack on outer wall
            # Show longitudinal cross-section: hollow cylinder wall with radial crack
            ax.add_patch(patches.Rectangle((20, 20), 60, 60, fill=False,
                                           edgecolor='black', linewidth=2))
            ax.add_patch(patches.Rectangle((30, 20), 40, 60, fc='#e8e8e8', ec='none'))
            ax.add_patch(patches.Rectangle((30, 20), 40, 60, fill=False,
                                           edgecolor='black', linewidth=1, linestyle='--'))
            # Radial crack from outer surface
            ax.add_patch(patches.Rectangle((78, 46), 12, 8, color='red'))
            self._cs_label(ax, 50, 50, "bore", color='#555', fontsize=8)
            self._cs_label(ax, 93, 50, "a", color='red')
            self._cs_label(ax, 15, 50, "t", color='#333')

        elif ntyp in (6, 7):  # Corner Crack – quarter ellipse at top-right corner
            self._cs_rect(ax)
            self._cs_corner_crack(ax, corner='tr')
            self._cs_ann_B(ax)
            self._cs_label(ax, 50, 94, "c", color='red')

        elif ntyp == 8:  # Double Edge Crack – through cracks from both sides
            self._cs_rect(ax)
            self._cs_through_crack(ax, cx=19, w=4)
            self._cs_through_crack(ax, cx=81, w=4)
            self._cs_ann_B(ax)
            self._cs_label(ax, 30, 50, "a", color='red')
            self._cs_label(ax, 70, 50, "a", color='red')

        elif ntyp == 99:
            ax.text(50, 50, "User-Defined\n(no section)", ha='center', va='center',
                    fontsize=9, fontstyle='italic', color='#888')

        elif ntyp == -1:  # One Corner Crack at Hole – quarter ellipse
            self._cs_rect(ax)
            self._cs_corner_crack(ax, corner='tr')
            self._cs_ann_B(ax)
            self._cs_label(ax, 50, 94, "c", color='red')

        elif ntyp == -2:  # Two Corner Cracks at Hole – both top corners
            self._cs_rect(ax)
            self._cs_corner_crack(ax, corner='tl')
            self._cs_corner_crack(ax, corner='tr')
            self._cs_ann_B(ax)

        elif ntyp == -3:  # One Through Crack at Hole
            self._cs_rect(ax)
            self._cs_through_crack(ax, cx=72)
            self._cs_ann_B(ax)
            self._cs_label(ax, 82, 50, "c", color='red')

        elif ntyp == -4:  # Two Through Cracks at Hole
            self._cs_rect(ax)
            self._cs_through_crack(ax, cx=37)
            self._cs_through_crack(ax, cx=63)
            self._cs_ann_B(ax)

        elif ntyp == -5:  # One Surface Crack on Bore
            # Show bore wall; crack from inner surface
            ax.add_patch(patches.Rectangle((20, 10), 60, 80, fill=False,
                                           edgecolor='black', linewidth=2))
            # Bore cavity on left
            ax.add_patch(patches.Rectangle((20, 10), 20, 80, fc='#d0d8e8', ec='none'))
            ax.plot([40, 40], [10, 90], 'k--', lw=1)
            # Crack from bore wall into material
            ax.add_patch(patches.Arc((40, 50), 20, 22, theta1=270, theta2=90,
                                     color='red', lw=2))
            ax.plot([40, 40], [39, 61], 'r-', lw=2)
            self._cs_label(ax, 30, 50, "bore", color='#555', fontsize=7)
            self._cs_label(ax, 55, 50, "a", color='red')
            self._cs_ann_B(ax)

        elif ntyp == -6:  # Two Surface Cracks on Bore
            ax.add_patch(patches.Rectangle((20, 10), 60, 80, fill=False,
                                           edgecolor='black', linewidth=2))
            ax.add_patch(patches.Rectangle((20, 10), 20, 80, fc='#d0d8e8', ec='none'))
            ax.plot([40, 40], [10, 90], 'k--', lw=1)
            ax.add_patch(patches.Arc((40, 35), 18, 18, theta1=270, theta2=90,
                                     color='red', lw=2))
            ax.plot([40, 40], [26, 44], 'r-', lw=2)
            ax.add_patch(patches.Arc((40, 65), 18, 18, theta1=270, theta2=90,
                                     color='red', lw=2))
            ax.plot([40, 40], [56, 74], 'r-', lw=2)
            self._cs_label(ax, 30, 50, "bore", color='#555', fontsize=7)
            self._cs_ann_B(ax)

        elif ntyp == -7:  # Surface Crack at Edge Notch – semi-ellipse at notch root
            self._cs_rect(ax)
            # Notch on left side
            ax.add_patch(patches.Wedge((15, 50), 10, 270, 90, fc='#f0f0f0', ec='none'))
            ax.add_patch(patches.Arc((15, 50), 20, 20, theta1=270, theta2=90,
                                     color='black', lw=2))
            # Surface crack from notch root, top face
            self._cs_surface_crack(ax, cx=50, face='top')
            self._cs_ann_B(ax)
            self._cs_label(ax, 50, 94, "2c", color='red')

        elif ntyp == -8:  # Through Crack at Edge Notch
            self._cs_rect(ax)
            ax.add_patch(patches.Wedge((15, 50), 10, 270, 90, fc='#f0f0f0', ec='none'))
            ax.add_patch(patches.Arc((15, 50), 20, 20, theta1=270, theta2=90,
                                     color='black', lw=2))
            self._cs_through_crack(ax, cx=28)
            self._cs_ann_B(ax)
            self._cs_label(ax, 42, 50, "c", color='red')

        elif ntyp == -9:  # Corner Crack at Edge Notch
            self._cs_rect(ax)
            ax.add_patch(patches.Wedge((15, 50), 10, 270, 90, fc='#f0f0f0', ec='none'))
            ax.add_patch(patches.Arc((15, 50), 20, 20, theta1=270, theta2=90,
                                     color='black', lw=2))
            self._cs_corner_crack(ax, corner='tr')
            self._cs_ann_B(ax)

        elif ntyp in (-10, -11):  # Through Cracks at Holes
            self._cs_rect(ax)
            self._cs_through_crack(ax, cx=38)
            self._cs_through_crack(ax, cx=62)
            self._cs_ann_B(ax)

        elif ntyp == -12:  # Lap Splice – through crack at rivet
            # Two overlapping sheets
            ax.add_patch(patches.Rectangle((10, 55), 80, 25, fill=False,
                                           edgecolor='black', lw=2))
            ax.add_patch(patches.Rectangle((10, 20), 80, 25, fill=False,
                                           edgecolor='blue', lw=1.5, linestyle='--'))
            # Through crack in top sheet from rivet hole
            ax.add_patch(patches.Rectangle((58, 55), 4, 25, color='red'))
            self._cs_label(ax, 68, 67, "c", color='red')
            ax.annotate("", xy=(8, 55), xytext=(8, 80),
                        arrowprops=dict(arrowstyle='<->', color='#333', lw=1))
            self._cs_label(ax, 3, 67, "t", color='#333', fontsize=8)

        elif ntyp == -13:  # Lap Splice – corner crack
            ax.add_patch(patches.Rectangle((10, 55), 80, 25, fill=False,
                                           edgecolor='black', lw=2))
            ax.add_patch(patches.Rectangle((10, 20), 80, 25, fill=False,
                                           edgecolor='blue', lw=1.5, linestyle='--'))
            ax.add_patch(patches.Wedge((85, 80), 14, 180, 270, color='red', alpha=0.8))
            self._cs_label(ax, 72, 68, "a,c", color='red', fontsize=7)

        elif ntyp == -14:  # Surface Crack at Edge Notch Bend
            self._cs_rect(ax)
            # Notch at bottom center
            ax.add_patch(patches.Wedge((50, 10), 10, 0, 180, fc='#f0f0f0', ec='none'))
            ax.add_patch(patches.Arc((50, 10), 20, 20, theta1=0, theta2=180,
                                     color='black', lw=2))
            # Surface crack from top face
            self._cs_surface_crack(ax, cx=50, face='top')
            self._cs_ann_B(ax)
            self._cs_label(ax, 50, 94, "2c", color='red')

        elif ntyp == -15:  # Through Crack at Edge Notch Bend
            self._cs_rect(ax)
            ax.add_patch(patches.Wedge((50, 10), 10, 0, 180, fc='#f0f0f0', ec='none'))
            ax.add_patch(patches.Arc((50, 10), 20, 20, theta1=0, theta2=180,
                                     color='black', lw=2))
            self._cs_through_crack(ax, cx=50)
            self._cs_ann_B(ax)
            self._cs_label(ax, 62, 50, "a", color='red')

        elif ntyp == -99:
            ax.text(50, 50, "User-Defined\n(no section)", ha='center', va='center',
                    fontsize=9, fontstyle='italic', color='#888')

        else:
            ax.text(50, 50, "Section N/A", ha='center', va='center',
                    fontsize=9, color='#888')

    # --- CROSS-SECTION HELPERS ---

    def _cs_rect(self, ax, x=15, y=10, w=70, h=80):
        """Draw specimen rectangle in cross-section coordinates."""
        ax.add_patch(patches.Rectangle((x, y), w, h, fill=False,
                                       edgecolor='black', linewidth=2))

    def _cs_label(self, ax, x, y, text, color='blue', fontsize=8):
        ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
                color=color, fontweight='bold')

    def _cs_ann_B(self, ax, x=7):
        """Annotate thickness B with a double-headed arrow on the left."""
        ax.annotate("", xy=(x, 10), xytext=(x, 90),
                    arrowprops=dict(arrowstyle='<->', color='#333', lw=1.2))
        self._cs_label(ax, x - 4, 50, "B", color='#333', fontsize=8)

    def _cs_through_crack(self, ax, cx=50, w=4):
        """Draw a through-thickness crack (full-height slit)."""
        ax.add_patch(patches.Rectangle((cx - w / 2, 10), w, 80, color='red'))

    def _cs_surface_crack(self, ax, cx=50, face='top', crack_w=28, crack_h=24):
        """Draw a semi-elliptical surface crack (depth ~30 % into thickness)."""
        if face == 'top':
            cy = 90
            t1, t2 = 180, 360
        else:
            cy = 10
            t1, t2 = 0, 180
        ax.add_patch(patches.Arc((cx, cy), crack_w, crack_h,
                                 theta1=t1, theta2=t2, color='red', lw=2))
        ax.plot([cx - crack_w / 2, cx + crack_w / 2], [cy, cy], 'r-', lw=2)
        label_y = cy - crack_h / 2 - 5 if face == 'top' else cy + crack_h / 2 + 5
        self._cs_label(ax, cx + crack_w / 2 + 8, label_y + (5 if face == 'top' else -5),
                       "a", color='red')

    def _cs_corner_crack(self, ax, corner='tr', r=20):
        """Draw a quarter-ellipse corner crack."""
        cfg = {
            'tl': (15, 90, 0,   90),
            'tr': (85, 90, 90,  180),
            'bl': (15, 10, 270, 360),
            'br': (85, 10, 180, 270),
        }
        cx, cy, t1, t2 = cfg[corner]
        ax.add_patch(patches.Wedge((cx, cy), r, t1, t2, color='red', alpha=0.75))
        off_x = 10 if 'l' in corner else -10
        off_y = -12 if 't' in corner else 12
        self._cs_label(ax, cx + off_x, cy + off_y, "a,c", color='#cc0000', fontsize=7)

    # --- VIEW LAYOUT ---

    # Normalized [left, bottom, width, height] positions — stacked vertically.
    _POS_BOTH_PLAN    = [0.05, 0.52, 0.90, 0.43]  # top half
    _POS_BOTH_SECTION = [0.05, 0.05, 0.90, 0.43]  # bottom half
    _POS_SINGLE       = [0.05, 0.05, 0.90, 0.90]

    def _update_view_layout(self):
        """Reposition / hide axes based on the Show checkboxes; prevent both hidden."""
        plan    = self.show_plan.get()
        section = self.show_section.get()

        # Always keep at least one visible
        if not plan and not section:
            self.show_plan.set(True)
            plan = True

        if plan and section:
            self.ax.set_position(self._POS_BOTH_PLAN)
            self.ax_cs.set_position(self._POS_BOTH_SECTION)
            self.ax.set_visible(True)
            self.ax_cs.set_visible(True)
        elif plan:
            self.ax.set_position(self._POS_SINGLE)
            self.ax.set_visible(True)
            self.ax_cs.set_visible(False)
        else:
            self.ax_cs.set_position(self._POS_SINGLE)
            self.ax_cs.set_visible(True)
            self.ax.set_visible(False)

        self.canvas.draw_idle()

    @contextmanager
    def _single_view_context(self, target):
        """
        Context manager: temporarily reshape the figure to show only *target*
        ("Plan View" or "Section A–A") at full width, then restore everything.
        Yields without changes when target == "Both".
        """
        if target == "Both":
            yield
            return

        ax_show = self.ax    if target == "Plan View" else self.ax_cs
        ax_hide = self.ax_cs if target == "Plan View" else self.ax

        saved_pos_show = ax_show.get_position().frozen()
        saved_pos_hide = ax_hide.get_position().frozen()
        saved_vis      = ax_hide.get_visible()

        ax_hide.set_visible(False)
        ax_show.set_position(self._POS_SINGLE)
        try:
            yield
        finally:
            ax_show.set_position(saved_pos_show)
            ax_hide.set_position(saved_pos_hide)
            ax_hide.set_visible(saved_vis)

    # --- EXPORT ACTIONS ---

    def _default_filename(self, ext):
        target = self.export_target.get()
        suffix = {"Plan View": "_plan", "Section A–A": "_section"}.get(target, "")
        stem = f"specimen_NTYP{self.current_ntyp}{suffix}" if self.current_ntyp is not None \
               else f"specimen{suffix}"
        return f"{stem}.{ext}"

    def save_image(self):
        """Prompt the user for a path and save the schematic at high DPI."""
        target = self.export_target.get()
        path = filedialog.asksaveasfilename(
            title="Save Specimen Schematic",
            defaultextension=".png",
            initialfile=self._default_filename("png"),
            filetypes=[("PNG Image", "*.png"),
                       ("PDF Document", "*.pdf"),
                       ("SVG Vector", "*.svg"),
                       ("All Files", "*.*")])
        if not path:
            return
        try:
            with self._single_view_context(target):
                self.figure.savefig(path, dpi=200,
                                    facecolor=self.figure.get_facecolor(),
                                    bbox_inches='tight')
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save image:\n{e}")

    def copy_to_clipboard(self):
        """Copy the current schematic to the system clipboard as an image."""
        if os.name != 'nt':
            messagebox.showinfo(
                "Copy Image",
                "Image clipboard copy is currently Windows-only.\nUse Save Image... instead.")
            return
        try:
            from PIL import Image
        except ImportError:
            messagebox.showerror(
                "Copy Image",
                "Pillow (PIL) is required for clipboard copy.\nUse Save Image... instead.")
            return

        from io import BytesIO
        import ctypes

        # Render figure to PNG bytes, reload through PIL, re-encode as BMP.
        # The Windows CF_DIB clipboard format expects the BMP without its
        # 14-byte BITMAPFILEHEADER prefix.
        target = self.export_target.get()
        buf = BytesIO()
        try:
            with self._single_view_context(target):
                self.figure.savefig(buf, format='png', dpi=200,
                                    facecolor=self.figure.get_facecolor(),
                                    bbox_inches='tight')
        except Exception as e:
            messagebox.showerror("Copy Error", f"Could not render image:\n{e}")
            return
        buf.seek(0)
        image = Image.open(buf).convert('RGB')

        bmp_buf = BytesIO()
        image.save(bmp_buf, 'BMP')
        dib = bmp_buf.getvalue()[14:]

        CF_DIB = 8
        GMEM_MOVEABLE = 0x0002
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        try:
            if not user32.OpenClipboard(0):
                raise OSError("Could not open clipboard")
            try:
                user32.EmptyClipboard()
                h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(dib))
                if not h_mem:
                    raise OSError("GlobalAlloc failed")
                p_mem = kernel32.GlobalLock(h_mem)
                ctypes.memmove(p_mem, dib, len(dib))
                kernel32.GlobalUnlock(h_mem)
                if not user32.SetClipboardData(CF_DIB, h_mem):
                    raise OSError("SetClipboardData failed")
            finally:
                user32.CloseClipboard()
        except Exception as e:
            messagebox.showerror("Copy Error", f"Could not copy to clipboard:\n{e}")


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