# plots.py
"""
plots.py
--------
All Matplotlib visualization logic for the FASTRAN GUI.
Handles Paris Law preview, spectrum bar charts, and post-processing plots.
"""

from matplotlib.axes import Axes
import numpy as np
import utils


def setup_growth_plot(ax: Axes):
    """Initializes the Paris Law plot with correct log scales."""
    ax.clear()
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel(r'$\Delta K_{eff}$ (MPa$\sqrt{m}$)')
    ax.set_ylabel(r'$da/dN$ (m/cycle)')
    ax.set_title("Crack Growth Rate Preview")
    ax.grid(True, which="both", linestyle='--', linewidth=0.5, alpha=0.7)


def plot_paris_law(ax: Axes, c1, c2, c3=0, c4=0, label="Growth Rate"):
    """
    Plots the Paris Law curve: da/dN = C1 * dK^C2.
    C3/C4 are accepted for future threshold extension but not yet applied in preview.
    """
    try:
        val_c1 = utils.safe_float(c1)
        val_c2 = utils.safe_float(c2)

        if val_c1 <= 0 or val_c2 == 0:
            setup_growth_plot(ax)
            return

        dk = np.logspace(0, 2.2, 60)
        dadn = val_c1 * (dk ** val_c2)

        ax.clear()
        ax.plot(dk, dadn, '-', color='royalblue', linewidth=2,
                label=f"C1={val_c1:.2e}, C2={val_c2:.2f}")
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel(r'$\Delta K_{eff}$ (MPa$\sqrt{m}$)')
        ax.set_ylabel(r'$da/dN$ (m/cycle)')
        ax.set_title("Crack Growth Rate Preview")
        ax.grid(True, which="both", linestyle='--', linewidth=0.5, alpha=0.7)
        ax.legend(loc='lower right', fontsize='small')

    except Exception as e:
        print(f"Paris Law plot error: {e}")
        ax.clear()


def plot_tabular_growth(ax: Axes, table_data):
    """
    Plots crack growth from a dKeff table (list of [dK, da/dN] pairs).
    Used when NTAB > 0 (tabular input from dkeff).
    """
    try:
        if not table_data or len(table_data) < 2:
            setup_growth_plot(ax)
            return

        dk_vals = [utils.safe_float(row[0]) for row in table_data]
        dadn_vals = [utils.safe_float(row[1]) for row in table_data]

        valid = [(dk, dn) for dk, dn in zip(dk_vals, dadn_vals) if dk > 0 and dn > 0]
        if len(valid) < 2:
            setup_growth_plot(ax)
            return

        dks, dadns = zip(*valid)
        ax.clear()
        ax.plot(dks, dadns, 'o-', color='darkorange', linewidth=2, markersize=4,
                label=f"dKeff Table ({len(valid)} pts)")
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel(r'$\Delta K_{eff}$ (MPa$\sqrt{m}$)')
        ax.set_ylabel(r'$da/dN$ (m/cycle)')
        ax.set_title("Crack Growth Rate (Tabular)")
        ax.grid(True, which="both", linestyle='--', linewidth=0.5, alpha=0.7)
        ax.legend(loc='lower right', fontsize='small')

    except Exception as e:
        print(f"Tabular growth plot error: {e}")
        ax.clear()


def plot_spectrum(ax: Axes, levels_data, speak_val=1.0):
    """
    Plots a bar chart of spectrum stress levels.
    Called by SpectrumCreatorWindow to preview the spectrum.

    Args:
        ax: Matplotlib axes to draw on.
        levels_data: List of [smax_str, smin_str, cycles_str] rows.
        speak_val: Scale factor applied to all stress values (SPEAK).
    """
    try:
        ax.clear()

        if not levels_data:
            ax.text(0.5, 0.5, "No spectrum data to display",
                    ha='center', va='center', transform=ax.transAxes, fontsize=10)
            ax.set_title("Spectrum Preview")
            return

        scale = utils.safe_float(speak_val, 1.0)
        if scale == 0:
            scale = 1.0

        smaxes, smins, cycles = [], [], []
        for row in levels_data:
            sm = utils.safe_float(row[0]) * scale
            sn = utils.safe_float(row[1]) * scale
            cy = utils.safe_int(row[2], 1)
            if cy > 0:
                smaxes.append(sm)
                smins.append(sn)
                cycles.append(cy)

        if not smaxes:
            ax.text(0.5, 0.5, "No valid stress levels defined",
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Spectrum Preview")
            return

        x = np.arange(len(smaxes))
        width = 0.8

        bars_max = ax.bar(x, smaxes, width, label='Smax', color='steelblue', alpha=0.8)
        bars_min = ax.bar(x, smins, width, label='Smin', color='tomato', alpha=0.8)

        ax.set_xlabel("Level Index")
        ax.set_ylabel("Stress")
        ax.set_title(f"Spectrum Preview ({len(smaxes)} levels)")
        ax.legend(loc='upper right', fontsize='small')
        ax.grid(True, axis='y', linestyle='--', alpha=0.5)
        ax.axhline(0, color='black', linewidth=0.8)

        if len(x) <= 20:
            ax.set_xticks(x)
            ax.set_xticklabels([str(i + 1) for i in x], fontsize=7)

    except Exception as e:
        print(f"Spectrum plot error: {e}")
        ax.clear()


def plot_post_processing(ax: Axes, header, data, x_col, y_col, log_x=False, log_y=False):
    """
    Plots parsed FASTRAN output data for the PostProcessingWindow.

    Args:
        ax: Matplotlib axes to draw on.
        header: List of column name strings.
        data: Dict mapping column name → list of float values.
        x_col: Name of the X-axis column.
        y_col: Name of the Y-axis column.
        log_x: Apply log scale to X axis.
        log_y: Apply log scale to Y axis.
    """
    try:
        ax.clear()

        if not header or not data:
            ax.text(0.5, 0.5, "No data to display",
                    ha='center', va='center', transform=ax.transAxes)
            return

        if x_col not in data or y_col not in data:
            ax.text(0.5, 0.5, f"Columns '{x_col}' or '{y_col}' not found in data",
                    ha='center', va='center', transform=ax.transAxes)
            return

        x_vals = data[x_col]
        y_vals = data[y_col]

        if not x_vals or not y_vals:
            ax.text(0.5, 0.5, "Empty data columns",
                    ha='center', va='center', transform=ax.transAxes)
            return

        ax.plot(x_vals, y_vals, '-o', linewidth=2, markersize=3,
                color='royalblue', markerfacecolor='white')

        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(f"{y_col} vs {x_col}")
        ax.grid(True, linestyle='--', alpha=0.6)

        if log_x:
            ax.set_xscale('log')
        if log_y:
            ax.set_yscale('log')

    except Exception as e:
        print(f"Post-processing plot error: {e}")
        ax.clear()


def plot_live_crack_growth(ax: Axes, cycles, crack_vals, ci=None, cf=None):
    """
    Redraws the real-time crack-size vs. cycles plot during a FASTRAN run.
    Called once per queue-poll cycle, not per line, to avoid excessive redraws.
    """
    try:
        ax.clear()
        if not cycles:
            ax.text(0.5, 0.5, "Waiting for data...",
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=10, color='gray')
            ax.set_title("Live Crack Growth")
            ax.set_xlabel("Cycles")
            ax.set_ylabel("Crack Length")
            return

        ax.plot(cycles, crack_vals, '-', color='firebrick', linewidth=1.5,
                marker='.', markersize=3)

        if ci is not None:
            ax.axhline(ci, color='steelblue', linewidth=1, linestyle='--',
                       label=f'Ci = {ci:.4g}')
        if cf is not None:
            ax.axhline(cf, color='darkorange', linewidth=1, linestyle='--',
                       label=f'Cf = {cf:.4g}')
        if ci is not None or cf is not None:
            ax.legend(loc='lower right', fontsize='small')

        ax.set_xlabel("Cycles")
        ax.set_ylabel("Crack Length")
        ax.set_title(f"Live Crack Growth  ({len(cycles)} pts)")
        ax.grid(True, linestyle='--', alpha=0.6)

    except Exception as e:
        print(f"Live crack plot error: {e}")
        ax.clear()
