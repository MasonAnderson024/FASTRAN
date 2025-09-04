# plots.py
"""
plots.py
----------
Handles all Matplotlib plotting for the FASTRAN GUI.
Each function takes a Matplotlib Axes object and data, and is responsible
for drawing a specific type of plot onto that Axes.
"""
from matplotlib.axes import Axes
from typing import List
import utils # For safe conversions

def plot_growth_rate(ax: Axes, table_data: List[List[str]]):
    """
    Generates the da/dN vs. dK_eff log-log plot for the Crack Growth tab.

    Args:
        ax (Axes): The Matplotlib Axes object to draw on.
        table_data (List[List[str]]): The data from the crack growth table.
    """
    dkeff_data = []
    rate_data = []

    for row in table_data:
        dkeff_val = utils.safe_float(row[0])
        rate_val = utils.safe_float(row[1])
        if dkeff_val > 0 and rate_val > 0:
            dkeff_data.append(dkeff_val)
            rate_data.append(rate_val)

    ax.clear()
    if dkeff_data and rate_data:
        ax.plot(dkeff_data, rate_data, marker='o', linestyle='-', markersize=4)

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel("ΔK_eff")
    ax.set_ylabel("da/dN")
    ax.grid(True, which="both", ls="--", linewidth=0.5)

def plot_real_time_growth(ax: Axes, x_data: List[float], y_data: List[float]):
    """
    Generates the real-time Crack Length vs. Cycles plot during a FASTRAN run.

    Args:
        ax (Axes): The Matplotlib Axes object to draw on.
        x_data (List[float]): The data for the x-axis (Cycles).
        y_data (List[float]): The data for the y-axis (Crack Length).
    """
    ax.clear()
    if x_data and y_data:
        ax.plot(x_data, y_data, marker='.', markersize=3, linestyle='-')
    
    last_cycle = x_data[-1] if x_data else 0
    last_crack = y_data[-1] if y_data else 0
    
    ax.set_title(f"FASTRAN Running... Cycle: {last_cycle:.0f}, Crack Length: {last_crack:.4f}")
    ax.set_xlabel("Cycles")
    ax.set_ylabel("Crack Length")
    ax.grid(True)

def plot_spectrum(ax: Axes, levels_data: List[List[str]], speak_value: float):
    """
    Generates the stress spectrum visualization plot for the SpectrumCreatorWindow.

    Args:
        ax (Axes): The Matplotlib Axes object to draw on.
        levels_data (List[List[str]]): The stress levels [smax, smin, cycles].
        speak_value (float): The SPEAK multiplier to apply to stress values.
    """
    plot_x = [0]
    plot_y = [0]
    cumulative_cycles = 0

    for level in levels_data:
        smax = utils.safe_float(level[0]) * speak_value
        smin = utils.safe_float(level[1]) * speak_value
        cycles = utils.safe_int(level[2])
        
        for _ in range(cycles):
            plot_x.extend([cumulative_cycles, cumulative_cycles + 0.5, cumulative_cycles + 1])
            plot_y.extend([smin, smax, smin])
            cumulative_cycles += 1
            if cumulative_cycles > 200: # Limit plot to first 200 cycles for performance
                break
        if cumulative_cycles > 200:
            break

    ax.clear()
    ax.plot(plot_x, plot_y, marker='o', markersize=2, linestyle='-')
    ax.set_title("Spectrum Visualization (First 200 Cycles)")
    ax.set_xlabel("Cumulative Cycles")
    ax.set_ylabel("Stress")
    ax.grid(True)

def plot_post_processing(ax: Axes, header: List[str], data: List[List[str]], x_var: str, y_var: str, log_x: bool, log_y: bool):
    """
    Generates the user-defined plot in the PostProcessingWindow.

    Args:
        ax (Axes): The Matplotlib Axes object to draw on.
        header (List[str]): The list of column headers.
        data (List[List[str]]): The tabular result data.
        x_var (str): The name of the variable for the x-axis.
        y_var (str): The name of the variable for the y-axis.
        log_x (bool): Whether to use a log scale for the x-axis.
        log_y (bool): Whether to use a log scale for the y-axis.
    """
    if not x_var or not y_var: return

    try:
        x_index = header.index(x_var)
        y_index = header.index(y_var)
        
        x_data = [utils.safe_float(row[x_index]) for row in data]
        y_data = [utils.safe_float(row[y_index]) for row in data]

        ax.clear()
        
        # Use scatter for rate-based plots, line for history-based plots
        plot_style = {'marker': '.', 'linestyle': ''} if 'DKEC' in x_var or 'DKEA' in x_var else {'marker': '.', 'markersize': 4, 'linestyle': '-'}
        
        ax.plot(x_data, y_data, **plot_style)
        
        ax.set_xlabel(x_var)
        ax.set_ylabel(y_var)
        ax.set_title(f"{y_var} vs. {x_var}")
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        
        ax.set_xscale('log' if log_x else 'linear')
        ax.set_yscale('log' if log_y else 'linear')
        
    except (ValueError, IndexError) as e:
        # Error handling should be done in the calling UI
        raise e