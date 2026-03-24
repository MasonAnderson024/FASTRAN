# plots.py
"""
plots.py
--------
Visualization Logic for FASTRAN GUI.

Responsibilities:
1. Crack Growth Plotting: Visualizes the Paris Law equation (C1, C2...) in real-time.
2. Styling: Manages the log-log scales and axis labels for engineering accuracy.
3. Safety: Handles math errors (e.g., log of zero) gracefully to prevent GUI crashes.
"""

from matplotlib.axes import Axes
from matplotlib.ticker import LogLocator
import numpy as np
import utils

def setup_growth_plot(ax: Axes):
    """
    Initializes the Paris Law plot with correct log scales and engineering labels.
    Called once during GUI setup.
    """
    ax.clear()
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel(r'$\Delta K_{eff}$ (MPa$\sqrt{m}$)')
    ax.set_ylabel(r'$da/dN$ (m/cycle)')
    ax.set_title("Crack Growth Rate Preview")
    ax.grid(True, which="both", linestyle='--', linewidth=0.5, alpha=0.7)

def plot_paris_law(ax: Axes, c1, c2, c3, c4, label="Growth Rate"):
    """
    Plots the Paris Law curve based on the constants provided.
    Equation Approximation: da/dN = C1 * (dK)^C2
    
    Args:
        ax (Axes): The matplotlib axes to draw on.
        c1 (str/float): The coefficient (intercept).
        c2 (str/float): The exponent (slope).
        c3, c4: Additional constants (reserved for future multi-slope logic).
    """
    try:
        # 1. Safe Conversion
        # Use utils to handle potentially empty strings from the GUI
        val_c1 = utils.safe_float(c1)
        val_c2 = utils.safe_float(c2)

        # 2. Validation
        # If C1 is zero, the log-log plot will crash or show nothing.
        # We only plot if we have valid physics parameters.
        if val_c1 <= 0 or val_c2 == 0:
            setup_growth_plot(ax) # Reset to blank grid
            return

        # 3. Generate Data Points
        # Create a range of Delta-K values typical for metals (1 to 100 MPa-sqrt(m))
        # Logspace generates points evenly spaced on a log scale
        dk = np.logspace(0, 2.2, 50) # Range: 1.0 to ~158.0
        
        # 4. Calculate Growth Rate
        # Simple Paris Law: da/dN = C1 * (dK)^C2
        # (Note: This is a preview. The full FASTRAN solver handles thresholds 
        # and fracture toughness clipping, but this visualizes the user's inputs).
        dadn = val_c1 * (dk ** val_c2)

        # 5. Plotting
        ax.clear()
        ax.plot(dk, dadn, '-', color='blue', linewidth=2, label=f"C1={val_c1:.1e}, C2={val_c2}")
        
        # 6. Re-Apply Styling
        # (Matplotlib's clear() resets styling, so we must re-apply)
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel(r'$\Delta K_{eff}$ (MPa$\sqrt{m}$)')
        ax.set_ylabel(r'$da/dN$ (m/cycle)')
        ax.set_title("Crack Growth Rate Preview")
        ax.grid(True, which="both", linestyle='--', linewidth=0.5, alpha=0.7)
        
        # Add a reference legend
        ax.legend(loc='lower right', fontsize='small')
        
    except Exception as e:
        print(f"Plotting Logic Error: {e}")
        # In case of error, just clear the plot so it doesn't show stale data
        ax.clear()