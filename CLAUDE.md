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
| `dialogs.py` | Top-level utility windows: `HelpWindow` (searchable help viewer + bundled `HELP_CONTENT`), `ProgressWindow` (modal indeterminate-progress dialog) |

**Archive/** holds all prior monolithic versions (v1 through v2.3.3) for reference.

## Current State (as of 2026-05-08)

### Latest Session Summary (2026-05-08)
Full DKEFF GUI extension across three commits merged to `main` via PR #1:

| Commit | Title |
|---|---|
| `ad4a375` | Fix DKEFF GUI gaps and extend functionality |
| `a0f3310` | DKEFF: specimen presets, NSOP guidance, and direct .lkpx import |
| `676d73f` | Fix material data flow bugs and add validation |

**DKEFF gap fixes (`ad4a375`):**
- `dkeff_exe_path` split into `dkeff13_exe_path` + `dkeff21_exe_path`; `_load_external_config` reads both `dkeff13_path`/`dkeff_path` and `dkeff21_path` from `fastran_gui.cfg`
- Added `_save_external_config()` and File → **Configure Executable Paths…** dialog with Browse buttons for FASTRAN, dkeff13, dkeff21
- `_batch_convert_lkpx` implemented on `DkeffWindow` (was called but missing); backed by new `parsers.parse_lkpx_for_batch()` for XML extraction from LK Pro-X `.lkpx` files
- `6.895` unit conversion factor replaced with `config.KSI_TO_MPA`
- Pre-run input validation (`_validate_dkeff_inputs`): SYIELD/SULT/E/W/T/ALP must be present and positive; empty table blocks run
- Raw `.dkout` output viewer panel (scrollable Courier text) appears below the paned window after each run
- DKEFF section added to `HELP_CONTENT` in `dialogs.py`

**AFMAT / no-geometry workarounds (`a0f3310`):**
- `config.DKEFF_SPECIMEN_PRESETS`: six standard ASTM E647 geometries (M(T) 3"/4", C(T) 0.5T/1T/2T, ESE(T)) with W, T, ALP
- "Specimen Preset" combobox + Apply button added to DkeffWindow analysis parameters; fills W/T/ALP from lookup
- NSOP combobox tooltip explains NSOP=0 is correct for database-sourced data (no crack length available)
- File → **Import .lkpx Direct to Main Window…**: parses `.lkpx`, shows R-ratio selection, pushes ΔK/da/dN rows straight into `CGR_TABLE` + NTAB — no dkeff run needed

**Material data flow bug fixes (`676d73f`):**
- `_apply_to_main` and `_import_lkpx_direct` were calling non-existent `self.parent.table_data` / `self.parent._redraw_table()` — fixed to write JSON into `vars['CGR_TABLE']` and call `_update_growth_plot()`
- `_apply_to_main` now also transfers ALP back to the main window
- `MaterialManager.allowed_keys` expanded: adds `CGR_TABLE`, per-equation `CGR_TABLE_2/3/4`, all `C1_2…NDKTH_4` variants, `KF`, `M`, `NDKTH`, `NALP`, `NEP` — previously tabular data was silently dropped on material save
- `_validate_run_inputs`: SYIELD ≥ SULT is now a hard error
- `_add_eq_entry` now checks `config.TOOLTIPS` (NTAB, NDKTH, KF, M, NEQN all have hover help)
- NTAB tooltip updated to explicitly warn it overrides Paris law constants when > 0

### Prior Session Summary (2026-04-30)
Cleared the last two Next Steps from the prior backlog, tidied up tracked cache files, and added image export for the specimen schematic:

| Commit | Title |
|---|---|
| `0c222e4` | Untrack `__pycache__` files (already in .gitignore) |
| `5ae47c8` | LFAST/LTYP/KCONST → comboboxes; add IRATE=2 option |
| `a784d87` | Save Image / Copy buttons on the specimen schematic |
| `446d106` | Add cross-section view to GeometryCanvas alongside plan view |
| `0ddac60` | Add view-toggle checkboxes and per-view export target to GeometryCanvas |

### Prior Session Summary (2026-04-29)

| Commit | Title |
|---|---|
| `052f786` | Show ProgressWindow during FASTRAN runs |
| `1340f12` | Per-equation crack-growth rate table editor (Section 7b) |
| `58b12ba` | Pre-run validation hooks before `run_analysis` |

### Prior Session Summary (2026-04-28)

| Commit | Title |
|---|---|
| `fdb683c` | Rewrite config/parsers/importers per FASTRAN 5.4/5.78f spec |
| `b0978e6` | Wire editors.py into main GUI |
| `57eaa3b` | Implement IRATE=4 multi-equation crack-growth panel |
| `93828dc` | Expose Section 9/10/11/16 input fields in GUI |
| `b0589ca` | Port HelpWindow and ProgressWindow to dialogs.py |

### Done
- Full module split complete; all 15 modules present and syntactically correct
- **`config.py`** fully corrected per FASTRAN 5.4/5.78f spec; `KSI_TO_MPA` and `DKEFF_SPECIMEN_PRESETS` added; TOOLTIPS covers ~70 entries including NTAB/NDKTH/KF/M
- **`parsers.py`**: `generate_fastran_input()` follows exact 18-section format; `parse_lkpx_for_batch()` extracts multi-R-ratio data from LK Pro-X XML files
- **`importers.py`**: `parse_fastran_input()` follows 18-section format; round-trip verified
- **`editors.py`**: full DkeffWindow with version selection, specimen presets, pre-run validation, output viewer, batch `.lkpx` conversion, direct `.lkpx` import; `_apply_to_main` correctly uses `CGR_TABLE` JSON StringVar; `BatchInputDialog`, `DatasetSelectionDialog`, `CrackGrowthTableDialog`
- **`materials.py`**: `MaterialManager.allowed_keys` covers all material data including per-equation CGR tables
- **`dialogs.py`**: `HelpWindow` with Ctrl+F search; `ProgressWindow`; full DKEFF workflow section in `HELP_CONTENT`
- **`fastran_gui_v2.3.4.py`**: Configure Executable Paths dialog; `_validate_run_inputs` covers Cf≤Ci, Cn>Ci, SYIELD≥SULT, flow stress, spectrum file presence; `_add_eq_entry` shows TOOLTIPS hover help; LFAST/LTYP/KCONST as comboboxes
- **`widgets.py`**: `GeometryCanvas` with plan + cross-section views, view-toggle checkboxes, Save Image / Copy buttons

### Next Steps

- **`.fou` output viewer.** `parsers.read_fastran_output` and `exporters.export_to_csv` exist, but there is no in-app way to read a `.fou` directly. A read-only viewer in `dialogs.py` (like the dkeff output panel but for FASTRAN output) would close that gap.
- **Validation: extend coverage.** Worth adding: NTYP-specific special-input checks (e.g., RIVETS=0 for NTYP=-12,-13), warning when IRATE>1 and eq>1 constants are still at defaults, C5 (DKth) > 0 sanity check when NTAB=0.
- **Material library versioning.** `MaterialManager` JSON has no version field; a `"version": 1` key would guard against silent failures if the schema changes.
- **Tests.** No automated test suite exists. A small `pytest` module covering parser/importer round-trips and the `parse_lkpx_for_batch` XML extraction would lock in format guarantees.

### Known Conventions
- **LFAST/LTYP/KCONST** use `N: label` comboboxes (same convention as NTYP/NFOPT). Parser strips the integer prefix on write (`int_prefix()`); importer remaps bare integers to full labels on read (`label_for_int()`); `_load_gui_state` migrates old bare-integer project saves automatically.
- **CGR_TABLE / CGR_TABLE_2..4** store per-equation tabular data as JSON strings in `tk.StringVar`. Any code that reads or writes them must use `json.loads` / `json.dumps`. Never store raw Python lists on ad-hoc parent attributes — the correct path is `vars['CGR_TABLE'].set(json.dumps(rows))` + `vars['NTAB'].set(str(len(rows)))`.
- **DkeffWindow** accesses the main GUI as `self.parent` and must only write to `self.parent.vars[...]` (StringVars). After pushing data, call `self.parent._update_growth_plot()` to refresh the Paris law preview.

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
