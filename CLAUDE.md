# FASTRAN GUI — Claude Code Project Context

## What This Is
A Python/Tkinter GUI front-end for the **FASTRAN** fracture mechanics / damage tolerance analysis code and its companion **DKEFF** material data tool. Target users are aerospace engineers running crack-growth life predictions.

## Architecture (Modular — v2.3.4+)

The monolithic `fastran_gui_v2.3.3.py` (4399 lines) was refactored into:

| File | Role |
|---|---|
| `fastran_gui_v2.3.4.py` | Main entry point — `FastranGui(tk.Tk)` class, layout, menu, orchestration |
| `config.py` | Knowledge base: `DEFAULT_VALUES`, `NTYP_DATA`, `NFOPT_DATA`, `FAILURE_MODES`, `TOOLTIPS`, dropdown generators |
| `project.py` | `ProjectManager` — creates/loads sandboxed project folders with `input/`, `output/`, `config/` subdirs |
| `security.py` | NIST-aligned: SHA-256 integrity checks, audit log writes |
| `utils.py` | Small helpers shared across modules |
| `parsers.py` | Generates FASTRAN `.txt` input files; reads `.fou` output files |
| `runners.py` | Threaded subprocess execution of FASTRAN/DKEFF EXEs; puts status into a `queue.Queue` |
| `plots.py` | All matplotlib logic: Paris law preview, real-time crack growth, batch design curve |
| `widgets.py` | Custom Tkinter widgets: `GeometryCanvas` (schematic diagrams), `ToolTip` |
| `materials.py` | `MaterialManager` — saves/loads JSON material library |
| `batch.py` | `BatchManager` — generates parametric job sets and extracts cycle counts |
| `importers.py` | Parses legacy FASTRAN `.txt` / `.in` input files for import |
| `exporters.py` | Exports `.fou` output to CSV |
| `postprocessor.py` | `ComparisonWindow` — multi-run overlay plots |
| `editors.py` | Toplevel editor windows: `SpectrumCreatorWindow`, `BlockEditorWindow`, `DkeffWindow`, `PostProcessingWindow`, `BatchInputDialog`, `DatasetSelectionDialog` |

**Archive/** holds all prior monolithic versions (v1 through v2.3.3) for reference.

## Current State (as of last session)

### Done
- Full module split complete; all 14 modules present and syntactically correct
- `config.py` significantly expanded: full NTYP/NFOPT tables, `FAILURE_MODES`, `TOOLTIPS`, spectrum/block loading flags added
- `runners.py` and `plots.py` updated (details in git diff vs last commit)
- `editors.py` contains all Toplevel editor classes ported from v2.3.3

### Still To Do
- **`editors.py` not imported in `fastran_gui_v2.3.4.py`** — the editor windows exist but aren't wired to any menu items or buttons yet. Need to add `import editors` and connect:
  - Spectrum file launcher → `SpectrumCreatorWindow`
  - Block loading editor (NFOPT=1) → `BlockEditorWindow`
  - DkEff tool → `DkeffWindow`
- **`_on_irate_change`** in main GUI is `pass` — needs to rebuild constants panel for IRATE=4 (small/large crack transition)
- **Help window** (`HelpWindow` from v2.3.3) not yet ported to a module
- **Progress window** (`ProgressWindow` from v2.3.3) not yet ported
- **Loading tab** is simplified vs v2.3.3 — spectrum file picker and block editor button not yet added

## How to Run
```
cd "FASTRAN Project"
python fastran_gui_v2.3.4.py
```
Requires: `tkinter`, `matplotlib`. FASTRAN/DKEFF EXE paths are set via `fastran_gui.cfg` (local only, not committed).

## Git Workflow
- `main` — stable releases
- `dev` — active development (default working branch)
- Branch is `MasonAnderson024/FASTRAN` on GitHub

## Key FASTRAN Concepts
- **NTYP**: Specimen geometry type (integer code maps to crack/specimen shape)
- **NFOPT**: Loading type (0=constant amplitude, 1=block, 2-10=spectrum files)
- **IRATE**: Crack growth law option (1=single Paris, 4=small/large crack transition)
- **CI/CF**: Initial and final crack sizes that bound the analysis
- **C1/C2**: Paris law constants (da/dN = C1 · ΔK^C2)
- **`.fou`**: FASTRAN output file format
