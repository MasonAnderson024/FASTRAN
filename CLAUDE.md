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

## Current State (as of 2026-04-29)

`dev` and `main` are both at `58b12ba` and synced with origin. The 2026-04-28 modular-refactor work was promoted to `main` together with today's three follow-ups.

### Latest Session Summary (2026-04-29)
Three commits landed on `dev` and were fast-forward merged into `main`:

| Commit | Title |
|---|---|
| `052f786` | Show ProgressWindow during FASTRAN runs |
| `1340f12` | Per-equation crack-growth rate table editor (Section 7b) |
| `58b12ba` | Pre-run validation hooks before `run_analysis` |

This session cleared the top three Next Steps from the prior session. The crack-growth-table commit also fixed a quietly-broken eq-1 case: nothing populated `CGR_TABLE`, so even single-equation tables were writing zero rows.

### Prior Session Summary (2026-04-28)

| Commit | Title |
|---|---|
| `fdb683c` | Rewrite config/parsers/importers per FASTRAN 5.4/5.78f spec |
| `b0978e6` | Wire editors.py into main GUI |
| `57eaa3b` | Implement IRATE=4 multi-equation crack-growth panel |
| `93828dc` | Expose Section 9/10/11/16 input fields in GUI |
| `b0589ca` | Port HelpWindow and ProgressWindow to dialogs.py |
| `58be3c9` / `e511749` | CLAUDE.md updates |

### Done
- Full module split complete; all 15 modules present and syntactically correct
- **`config.py` fully corrected** per FASTRAN 5.4/5.78f User Guide:
  - `NTYP_DATA`: 26 entries covering all valid NTYP codes (0–8, 99, -1 through -15, -99) with correct names and special-input lists
  - `NFOPT_DATA`: All 11 options (0–10) with correct names and invert/clip labels; NFOPT 6 and 7 added
  - `FAILURE_MODES`: Correct NFCODE 0–6 descriptions from the spec
  - `DEFAULT_VALUES`: ~96 keys including all new FASTRAN parameters (LFAST, KCONST, NS, LTYP, NTCMAX, T, HN, RAD, RADF, NDKE, LSTEP, NRC, DVALUE, GAMMA, XKT, NBCF, etc.)
  - `LFAST_DATA`, `LTYP_DATA`, `KCONST_DATA` dropdown tables added
  - `TOOLTIPS`: ~65 entries, C4 tooltip corrected
- **`parsers.py` rewritten**: `generate_fastran_input()` follows the exact 18-section FASTRAN input file format; verified against real test files
- **`importers.py` rewritten**: `parse_fastran_input()` follows the 18-section format; correctly parses real test files (iTest14.txt validated)
- **`editors.py` wired into main GUI**: Tools menu (Spectrum/Block/DkEff); Loading tab gained dynamic Spectrum-File and Block-Loading sub-frames driven by `NFOPT_DATA` flags; block editor persists to `<project>/config/block_loading.json`
- **IRATE=4 multi-equation panel**: per-equation suffixed vars (`C1_2..NDKTH_4`); `_build_constants_panel` renders `ttk.Notebook` with N tabs (inline panel for IRATE=1); parser/importer use `eq_key()` helper; round-trip verified for all 4 equations
- **Section 9/10/11/16 input fields exposed**: AI/AN/HN/RAD/RADF on Geometry tab; LTYP/LFAST/NS/KCONST/NTCMAX on Loading tab (Section 10); NRC/DVALUE/NCYCLE1/NCYCLE2 on Loading tab (Section 16); NIPT/NPRT/LSTEP/NDKE/DCPR on Crack Growth tab (Section 9). `_add_entry` falls back to `config.TOOLTIPS` for automatic contextual help.
- **`dialogs.py` ported from v2.3.3**: `HelpWindow` (Ctrl+F search, find-next, wrap prompt) wired to a Help menu via `_show_help` singleton; `ProgressWindow` now opens during FASTRAN runs (modal, closes on success/error)
- **Per-equation Section 7b crack-growth tables**: `editors.CrackGrowthTableDialog` opens from each equation tab via "Edit Table…"; data stored as JSON in `CGR_TABLE` / `CGR_TABLE_2..4` StringVars; parser writes rows for all eqs; importer captures rows (round-trip verified)
- **Pre-run validation**: `_validate_run_inputs` returns `(errors, warnings)`. Errors block (Cf≤Ci, Cn>Ci, unparseable critical fields, missing spectrum file). Warnings prompt Yes/No (Smax ≥ flow stress, non-positive W/B/E)

### Next Steps
Two items remain from the prior backlog. Both are small / polish.

1. **Convert LFAST / LTYP / KCONST to comboboxes** — _small effort, polish._ The `LFAST_DATA` / `LTYP_DATA` / `KCONST_DATA` dicts already exist in `config.py`. Plain Entries currently stand in. Upgrading would require parser/importer to handle a `:` prefix split (matching the NTYP/NFOPT convention) — see the Known Convention note below for the gotcha.

2. **Add IRATE=2 to the IRATE combobox** — _trivial._ Combobox values are `['1', '4']`; IRATE=2 (independent c- and a-direction laws) is already supported by the per-equation panel and parser/importer round-trip. Just add `'2'` to the values list.

### Known Convention
LFAST/LTYP/KCONST are exposed as plain Entry widgets, not dropdowns. Keeps parser/importer simple — they read the var as a raw integer string. Upgrading these to comboboxes (Next Step #4) would require a `:`-prefix split for normalization, matching the existing NTYP/NFOPT convention (`int(s.split(':')[0])`).

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
