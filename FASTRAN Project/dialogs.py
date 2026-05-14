"""
dialogs.py
----------
Top-level utility windows for the FASTRAN GUI:
  - HelpWindow      — searchable help text viewer
  - ProgressWindow  — modal indeterminate-progress dialog

HELP_CONTENT lives here so the help text is bundled with the viewer.
"""

import tkinter as tk
from tkinter import ttk, messagebox


HELP_CONTENT = """
================================
 FASTRAN GUI — Quick Help Guide
================================

This guide provides a detailed explanation of the input fields and workflow
for each tab in the GUI.  Based on FASTRAN Version 5.4 User Guide.

New users should work left-to-right through the five tabs in order:
  1. Geometry → 2. Material → 3. Loading → 4. Crack Growth → 5. Sensitivity

Then click "RUN ANALYSIS" at the bottom of the window.

FASTRAN uses an 18-section input format.  Each GUI tab collects the fields
for one or more sections, and the parser assembles the exact text file
that FASTRAN reads.

-----------------------------------------------------------------------------
  Project Management
-----------------------------------------------------------------------------

The FASTRAN GUI organises each analysis as a self-contained *project folder*
that holds all input files, output files, and settings in one place.

  File > New Project
  - Creates a fresh project folder (input/, output/, config/ sub-folders).
  - You must create or open a project before the RUN button is enabled.

  File > Open Project
  - Reopens an existing project folder and restores the last saved GUI state.

  File > Save Project State
  - Writes the current values of all GUI fields to config/settings.json so
    they are restored exactly the next time you open this project.

  File > Import Legacy .txt / .in
  - Reads an old-style FASTRAN text input file and populates the GUI fields
    so you can view and edit it using the modern interface.

  File > Configure Executable Paths...
  - Opens a dialog to browse for the FASTRAN, dkeff13, and dkeff21f EXE
    locations.  Paths are saved to fastran_gui.cfg (not committed to git).

  Tools > Export Results to CSV
  - Converts the most recent .fou output file to a comma-separated spreadsheet.

  Tools > Compare Runs / Post-Processor
  - Opens a multi-run overlay window to plot results from several .fou files
    on the same axes.

-----------------------------------------------------------------------------
  Material Library
-----------------------------------------------------------------------------

The Material Library stores frequently used sets of material properties as a
JSON file (materials_library.json) in the project folder.

  On the Material tab:
    "Load Material..."
    - Choose a saved material by name; all property fields are filled in,
      including crack-growth tables (CGR_TABLE), NALP, NEP, ALP, BETAT, BETAW.

    "Save Current to Library..."
    - Prompts for a name and writes every material field to the library for
      future reuse.  Per-equation crack-growth tables (CGR_TABLE through
      CGR_TABLE_4) are included.

  Tip: After running the dkeff Material Data Generator and clicking
  "Apply to Main Window", save the result to the library so you never have
  to re-run dkeff for the same dataset.

-----------------------------------------------------------------------------
  Tab 1 — Geometry  (FASTRAN Input Sections 10–11, 13–14)
-----------------------------------------------------------------------------

Select the specimen geometry that most closely matches your physical coupon or
structural detail.  The schematic updates in real time as you type.

[ Specimen Type (NTYP) — Section 10 ]

  NTYP sets the boundary-correction factor (beta function) used to compute
  the stress-intensity factor.  FASTRAN Version 5.4 includes 25 geometry types:

  Standard crack configurations (NTYP ≥ 0):
     0  — Surface crack in a plate (tension and/or bending).
            Requires GAMMA when LTYP=2 (combined loading).
     1  — Center-crack tension M(T) specimen.
     2  — Compact C(T) or ESE(T) specimen.
     3  — Single-edge crack tension SE(T).
     4  — Single-edge crack bend SE(B).
     5  — Through crack in a pressurized cylinder.
            Requires RADIUS (cylinder radius).
     6  — Corner crack (a=c) in a square bar (AGARD geometry).
     7  — Corner crack in a plate (tension and/or bending).
            Requires GAMMA when LTYP=2.
     8  — Double-edge crack tension D(T).
    99  — User-defined geometry (Fc vs. c/w table supplied by user).

  Cracks at holes and notches (NTYP < 0):
    -1  — One corner crack at a circular hole (tension/bending).
    -2  — Two corner cracks at a circular hole, symmetric (tension/bending).
    -3  — One through crack at a circular hole.
    -4  — Two through cracks at a circular hole, symmetric.
    -5  — One surface crack at the center of a circular hole.
    -6  — Two surface cracks at the center of a circular hole, symmetric.
    -7  — Surface crack at a semi-circular edge notch.
            Requires XKT (stress concentration factor) and NBCF (BCF type).
    -8  — Through crack at a semi-circular edge notch.
            Requires XKT and NBCF.
    -9  — Corner crack at a semi-circular edge notch.
            Requires XKT and NBCF.
   -10  — Through cracks at circular holes under pin load plus moment.
            Requires GAMMA (moment parameter).
   -11  — Periodic through cracks at circular holes.
   -12  — Lap-splice joint with through cracks (riveted structure).
            Requires RIVETS, RLF1, RLF2, NODKL, GAMMA, DELTA.
   -13  — Lap-splice joint with corner cracks (riveted structure).
            Requires RIVETS, RLF1, RLF2, NODKL, GAMMA, DELTA.
   -14  — Surface crack at an edge notch (bending).
   -15  — Through crack at an edge notch (bending).
   -99  — User-defined crack at a hole/notch (fct vs. crk/w table).

  Changing NTYP may reveal or hide "Special Inputs" fields that are required
  for that geometry (e.g., Hole Radius, Stress Concentration Factor, Rivet
  Pitch).  These correspond to Section 14 of the FASTRAN input file.

[ Special Inputs (Section 14) ]

  GAMMA  — Bending ratio γ = Sb/S.  Required when LTYP=2 (combined loading)
             for NTYP=0 or 7, or for any loading with NTYP=-10.
  XKT    — Elastic stress concentration factor Kt at the notch root.
             Required for NTYP=-7, -8, -9.
  NBCF   — Boundary correction factor type for notch geometries.
             0=Uniform stress (h/w=2); 1=Displacement h/w=1.5;
             2=Displacement h/w=2; 3=Displacement h/w=3.
             Required for NTYP=-7, -8, -9.
  RADIUS — Cylinder radius.  Required for NTYP=5.
  RIVETS — Rivet pitch (center-to-center spacing).
             Required for NTYP=-12, -13.
  RLF1   — Rivet load factor at the primary (cracked) fastener hole (0 to 1).
             RLF1 + RLF2 must equal 1.0.  Required for NTYP=-12, -13.
  RLF2   — By-pass load factor (complement of RLF1).  Required for NTYP=-12, -13.
  NODKL  — 0: rivet load stays constant as the crack grows.
             1: rivet load decays using the standard decay equation.
             Required for NTYP=-12, -13.
  DELTA  — Rivet interference (change in rivet radius due to installation).
             Required for NTYP=-12, -13.

[ Specimen Dimensions (Section 11) ]

  W    — Half-width for M(T) (NTYP=1); full width for C(T), SE(T), SE(B),
          D(T), and notch/hole types.  Same units as CI and CF.
  B    — Full plate or sheet thickness (GUI label for the FASTRAN T variable).
          For NTYP=-5, -6, -7, -14, T means one-half thickness.
  CI   — Initial crack length c_i (from hole/notch centerline for those types).
          Must be less than CF.
  AI   — Initial crack depth a_i.  For through cracks, set equal to T.
  CN   — Starter notch length c_n.  Set CN = CI if there is no pre-cracking
          stage (no notch separate from the initial crack).
  AN   — Starter notch depth a_n for surface or corner crack notches.
  HN   — Starter notch half-height h_n.
  RAD  — Radius of a circular hole (NTYP with holes) or of a semi-circular
          edge notch (NTYP=-7, -8, -9, -14, -15).
  RADF — Fastener radius.  0 = open hole.  Equal to RAD = tight-fitting fastener.
  CF   — Final crack length at which FASTRAN stops the analysis.
          Must be greater than CI and typically less than W.

  *Note:* All dimensions must use consistent units (all SI or all English).
  Use the Unit Conversion (LUNIT) field on the Loading tab to convert input
  values.  Set IUNIT to declare the unit system used in the input file.

[ Schematic Views ]

  The geometry schematic shows two stacked views:
    Plan View    — Looking down on the specimen from above (crack length axis).
    Section A–A  — Through-thickness cross-section (crack depth axis).

  Use the checkboxes above the schematic to show or hide each view.
  The "Save Image" button exports the current schematic as a PNG or PDF.
  "Copy" puts the schematic on the clipboard for pasting into reports.

-----------------------------------------------------------------------------
  Tab 2 — Material  (FASTRAN Input Sections 3–4)
-----------------------------------------------------------------------------

Enter the mechanical properties of the material being analysed.

[ Properties (Section 4) ]

  Material Name (MAT)
  - Free-text label (up to 60 characters) that appears in the FASTRAN output
    header for identification purposes.

  Yield Stress (SYIELD)
  - 0.2% offset yield strength in the selected stress units (MPa or ksi).

  Ultimate Strength (SULT)
  - Ultimate tensile strength.  Must be greater than SYIELD.  The GUI will
    prevent the analysis from starting if SYIELD ≥ SULT.

  Elastic Modulus (E)
  - Young's modulus (stiffness) in the selected stress units.

  Poisson's Ratio (ETA)
  - 0.0 selects a plane-stress effective Poisson's ratio (thin sheet/plate).
  - Set to the actual Poisson's ratio (e.g., 0.33 for aluminium) for a
    plane-strain correction to the stress-intensity factor.

  *Flow Stress:* FASTRAN computes Sflow = (SYIELD + SULT) / 2.
  When the maximum applied stress exceeds Sflow, FASTRAN flags net-section
  yielding (failure code 3) and terminates the analysis.

[ Constraint & Plasticity Options (Section 4) ]

  Constraint Factor (ALP)
  - Plastic constraint factor alpha at the crack tip.
  - 1.0  = plane stress (thin sheet, no out-of-plane constraint).
  - 1.73 = Irwin plane-strain estimate (sqrt(3)).
  - 3.0  = full plane strain (thick section, high constraint).
  - Typical starting value for a mixed-mode analysis is ALP=1.8.
  - When NALP=1, ALP is the initial value before the transition begins.

  Compressive Tip Constraint (BETAT)
  - Controls the extent of the compressive yield zone ahead of the crack tip
    in the intact (uncracked) material.  Typically 1.0.
  - Reduce slightly (0.5–0.9) only for very thin specimens where the
    compressive zone extends through the full thickness.

  Compressive Wake Constraint (BETAW)
  - Controls compressive yielding in the crack wake (the closure contact
    region behind the crack tip).  Typically 1.0.

  Constraint Option (NALP)
  - 0: Constant ALP — the constraint factor is fixed at the user-input value
       throughout the entire analysis.
  - 1: Variable ALP — FASTRAN adjusts ALP automatically based on crack-growth
       rate da/dN.  The transition is defined by RATE1/ALP1 and RATE2/ALP2 on
       the Crack Growth tab.  Use this option when the specimen undergoes a
       flat-to-slant fracture mode transition during the test.

  Plasticity Option (NEP)
  - 0: Elastic — no plasticity correction; ΔKeff = ΔK_elastic.
  - 1: Cyclic plastic zone correction (RECOMMENDED).  FASTRAN adds a fraction
       of the cyclic plastic zone radius to the physical crack length before
       computing ΔKeff.  This is Newman's standard FASTRAN method.
  - 2: Monotonic plastic zone correction.  Uses the larger monotonic (tensile)
       plastic zone instead of the cyclic zone.  Less commonly used.

[ Material Library ]

  Use "Load Material..." and "Save Current to Library..." to store and recall
  material property sets (including crack-growth tables and all constraint
  parameters).

-----------------------------------------------------------------------------
  Tab 3 — Loading  (FASTRAN Input Sections 10, 15–17)
-----------------------------------------------------------------------------

Choose how the fatigue load is applied to the specimen.

[ Loading Type (NFOPT) — Section 10 ]

  NFOPT controls the form of the fatigue load history:

   0  — Constant Amplitude: single Smax / R sine-wave cycling.
   1  — Block / Flight Loading: user-defined variable-amplitude block sequence
        (use "Edit Block Loading..." to build the sequence table).
   2  — TWIST transport aircraft spectrum (external spectrum file required).
   3  — Mini-TWIST shortened transport aircraft spectrum (spectrum file required).
   4  — FALSTAFF fighter aircraft manoeuvre spectrum (spectrum file required).
   5  — Space Shuttle Load Sequence (spectrum file required).
        INVERT: 0=full sequence, 1=short sequence.
   6  — Gaussian random spectrum (I=0.99).
        NOTE: Not available in the current version of FASTRAN; reserved.
   7  — Helicopter spectrum — Felix-28 or Helix-32 (spectrum file required).
        INVERT: 1=Felix-28, 2=Helix-32.
   8  — External spectrum file — list of stress points (max/min pairs).
        INVERT: 0=Max/Min order, 1=Min/Max order.
        Uses NREP and MARKER for repeat count and marker bands.
   9  — External spectrum file — flight-by-flight format.
        INVERT: 0=Max/Min order, 1=Min/Max order.
  10  — External spectrum file — flight schedule format.

  For NFOPT ≥ 2 you must provide a correctly formatted spectrum file in the
  project's input/ folder.  Use "Browse..." to locate it, or "Edit Spectrum..."
  to create one using the built-in Spectrum Creator.  A placeholder filename
  will cause the FASTRAN run to fail.

[ Pre-Cracking Stage (Section 15) ]

  Smax — Maximum applied stress for both the pre-cracking stage and, for
          NFOPT=0 (constant amplitude), for the main analysis as well.
  R    — Stress ratio R = Smin / Smax.  Smin is computed as Smax × R.
  FW   — Loading frequency in Hz.  Stored in the header for reference.
          Not used in crack-growth rate calculations.

  The INVERT / Clip field label updates automatically when NFOPT changes:
    NFOPT=0/1  → Invert (0=normal sign, 1=invert all stresses)
    NFOPT=2/3  → Clip Level (0=no clip; 2–5=TWIST Levels II–V)
    NFOPT=4    → Invert (0=normal, 1=inverted sequence)
    NFOPT=5    → Invert (0=full sequence, 1=short sequence)
    NFOPT=7    → Invert (1=Felix-28, 2=Helix-32)
    NFOPT=8/9  → Invert (0=Max/Min order, 1=Min/Max order)

  SPEAK — Peak scaling stress for spectrum loading (NFOPT 4–10).  All
           stress values in the spectrum file are multiplied by SPEAK.
  SMEAN — Mean stress offset added to TWIST / Mini-TWIST / Gaussian spectra
           (NFOPT=2, 3, 6 only).

[ Spectrum File ]

  Enter the filename of the spectrum file (relative to the project's input/
  folder) or use "Browse..." to locate it on disk.  "Edit Spectrum..." opens
  the Spectrum Creator to build a new spectrum from scratch.

[ Block Loading Table (NFOPT=1) — Section 17 ]

  "Edit Block Loading..." opens the Block Editor where you define the fatigue
  block sequence.  Each block/flight has a stress level and a repeat count.

  MAXSEQ — Total number of blocks or flights in the repeated load sequence.
  MAXBLK — Number of different block/flight types in the history.
  SCALE  — Scale factor applied uniformly to all block/flight stress levels.
  LPRINT — 0=No internal sequence print.  1=Print block/flight numbers.
            2=Print full block/flight details (debugging).
  MAXLPR — Maximum number of lines printed when LPRINT > 0.

  For NFOPT=8 only:
  NREP   — Number of times the external stress-point sequence repeats per
            simulated flight or block.
  MARKER — 0=No marker bands.  1=Insert a marker-load cycle every NREP repeats
            (useful for fractographic life tracking).

[ Specimen & Loading Options (Section 10) ]

  LTYP   — Loading sub-type (applies to NTYP=0, 2, 7, -1, -2):
             0: Remote tension — input applied stress S.
             1: Remote bending — input outer-fiber bending stress Sb.
             2: Combined tension + bending — input S and γ = Sb/S (GAMMA).

  LFAST  — Crack-closure model selection:
             0: Normal closure model — FASTRAN computes crack-opening stress
                S'o each cycle (most accurate; standard for all analyses).
             1: SOBAR equivalent — uses constant-amplitude S'o once crack
                exceeds cmax (faster for long spectrum runs with large cracks).
             2: Linear cumulative damage using the constant-amplitude S'o
                equation (simplified model).
             3: Constant S'o computed from the block or flight min/max
                stresses (conservative simplified model).
             4: Constant S'o from manual user input.  Set NRC=-1 and supply
                DVALUE = S'o / Smax in Section 16.

  KCONST — Loading quantity:
             0: Apply remote stress S as the driving load (normal).
             1: Apply stress-intensity factor K directly as the driving load.
                Valid only for NTYP=1 or 2, NFOPT ≤ 1, and LFAST=0.

  NS     — Number of notch elements modelling the notch geometry.
             Minimum 1 for a plain notch.  Minimum 2 for a notch at a hole.

  NTCMAX — 0: Normal notch constraint (default).
             1: First load cycle uses plane-stress (ALP=1) for negative-NTYP
                geometries to represent the initial notch-tip plasticity.

[ Proof Test / Constant S'o (Section 16) ]

  Section 16 supports two special pre- or post-cycling scenarios:

  Proof test overload (NRC > 0):
    NRC     — Number of proof-test load cycles (typically 1).
    DVALUE  — Proof-load amplitude (stress or K, consistent with KCONST).
    NCYCLE1 — Constant-amplitude pre-test cycles applied before the proof load.
    NCYCLE2 — Constant-amplitude post-test cycles applied after the proof load.

  Manual closure input (NRC = -1):
    NRC     — Set to -1 to activate.
    DVALUE  — Manual crack-opening stress ratio S'o / Smax.  Only valid with
               LFAST=4.

  For most standard crack-growth analyses, leave NRC=0 and all fields at 0.

-----------------------------------------------------------------------------
  Tab 4 — Crack Growth  (FASTRAN Input Sections 5–9)
-----------------------------------------------------------------------------

Define the material crack-growth behaviour.  Either use the Paris-law
equation (C1–C7) or supply tabular ΔKeff / da/dN data.

[ Model Option (IRATE) — Section 5 ]

  IRATE specifies how many crack-growth curves are used:
  1 — Single law: one da/dN = f(ΔKeff) curve for both c- and a-directions.
  2 — Two independent laws: separate curves for the crack length (c) and
       crack depth (a) directions.
  4 — Small/large crack transition: four curves — small-crack and large-crack
       laws for each of the c- and a-directions.

  NGC / CRKNGC (IRATE=4 only, Section 5):
  - NGC=0: original FASTRAN code (no explicit transition mechanism).
  - NGC=1: enables the small-to-large crack transition logic.
  - CRKNGC: transition crack size.  Cracks with c or a < CRKNGC use the
    small-crack growth law; cracks ≥ CRKNGC use the large-crack law.
    Typical value: 0.00025 m (0.01 in) for aluminium alloys.

[ Paris Law Constants (C1–C7) — Section 6 ]

  FASTRAN uses the following crack-growth rate equation for each curve:

    da/dN = C1 · ΔKeff^C2 · F_threshold · F_fracture

  where:
    F_threshold = [1 − (ΔKo / ΔKeff)^C7]
    F_fracture  = [1 − (Kmax / C5)^C6]   (if C5 < 9999)
                = [1 − (Kmax / KIe)^C6]  (if C5 ≥ 9999)

  Steady-state Paris regime:
    C1 — Scaling coefficient.  Sets the vertical position of the da/dN curve
          on a log-log plot.  Higher C1 = faster growth.
    C2 — Slope exponent (Paris exponent).  Typically 2–5 for metals.

  Threshold region (set C3=C4=0 and C7=0 to disable entirely):
    C3 — Baseline threshold ΔKo at R=0.  ΔKo formula:
          If C4 > 0:  ΔKo = C3 · (1 − R)^C4
          If C4 < 0:  ΔKo = C3 · (1 + C4·R)
    C4 — R-ratio sensitivity of the threshold.
    C7 — Sharpness of the threshold knee.  C7=1 gives a gradual transition;
          higher values create a sharper cut-off near ΔKo.

  Fracture region:
    C5 — Cyclic fracture toughness.  Set C5 ≥ 9999 to use the elastic-plastic
          toughness KIe (computed from KF and m) instead of a fixed C5 value.
    C6 — Power on the fracture term.  Controls how steeply da/dN accelerates
          as Kmax approaches the fracture toughness.

  Elastic-plastic fracture (when C5 ≥ 9999):
    KF — Elastic-plastic fracture toughness Kf (plane-stress or -strain value
          depending on thickness).
    m  — Constraint parameter: 0=brittle (pure LEFM, KIe=KF),
          1=fully ductile (KIe computed from flow stress and KF).

  Equation form (NEQN):
    0 — FASTRAN equation (standard, as above).
    1 — NASGRO equation (alternate form with NASGRO threshold term).

[ Tabular Data (NTAB > 0) — Section 7a / 7b ]

  When NTAB > 0, the table of (ΔKeff, da/dN) data pairs overrides the
  C1–C7 Paris constants for that equation.  The da/dN preview plot on Tab 4
  switches from the Paris curve to the tabular data points automatically.

  NTAB  — Number of tabular data points.  Set via the "Edit Table..." button
            on the Crack Growth tab.  Setting NTAB=0 reverts to C1–C7.
  NDKTH — Tabular interpolation / correction mode:
            0: Direct table lookup — da/dN interpolated from ΔKeff vs. da/dN.
            1: FASTRAN tabular form — applies threshold and fracture
               corrections on top of the table (Section 7b, standard mode).
            2: NASGRO tabular form — alternate correction scheme.
  KTAB  — 0: Table is in terms of ΔKeff.
            1: Table is in terms of ΔK (elastic range); FASTRAN converts to ΔKeff.

  *Tip:* Use Tools > Material Data Generator (dkeff) to convert raw ASTM E647
  lab data into a corrected ΔKeff table, then click "Apply to Main Window" to
  import it here.  The CGR_TABLE and NTAB fields update automatically.

[ Output Options (Section 9) ]

  NPRT  — Output print interval.
            Negative value: print a line every |NPRT| crack-growth increments
            (recommended — gives evenly spaced crack length output).
            Positive value: print every NPRT FASTRAN analysis time steps.
            0: use DCPR crack-increment criterion instead.
  DCPR  — Crack-growth increment size at which output is written when NPRT=0
            (e.g., 0.00005 m or 0.002 in).  Ignored when NPRT ≠ 0.
  NIPT  — 0: internal closure data log off (normal operation).
            > 0: write detailed internal closure data every NIPT increments
            (use only for debugging — produces very large output files).
  LSTEP — Number of load sub-steps from load minimum to maximum during each
            NIPT printout cycle.  Usually 1.
  NDKE  — 0: print elastic stress-intensity range ΔK in the output.
            1: print effective stress-intensity range ΔKeff in the output
            (ΔKeff = crack-opening-corrected range; recommended).

[ Variable Constraint Transition (Section 8, NALP=1 only) ]

  When NALP=1 is selected on the Material tab, you must define the two points
  that bracket the flat-to-slant fracture mode transition:

  RATE1 / ALP1 / BETAT1 / BETAW1
  - At da/dN = RATE1, the constraint factor begins transitioning toward ALP1.
  - BETAT1 and BETAW1 are the corresponding compressive constraint values.

  RATE2 / ALP2 / BETAT2 / BETAW2
  - At da/dN = RATE2, the transition is complete and ALP reaches ALP2.
  - RATE2 must be strictly greater than RATE1.
  - BETAT2 and BETAW2 are the compressive constraints at completion.

  Between RATE1 and RATE2, FASTRAN interpolates ALP, BETAT, and BETAW
  linearly on a log(da/dN) scale.

  Typical values for 2xxx or 7xxx aluminium alloys:
    RATE1=1.0e-7 m/cycle  ALP1=2.0  BETAT1=1.0  BETAW1=1.0
    RATE2=2.5e-6 m/cycle  ALP2=1.0  BETAT2=1.0  BETAW2=1.0

[ Threshold Test (Section 18) ]

  Section 18 enables FASTRAN to simulate an ASTM threshold determination test
  (valid only for NTYP=1, NFOPT=0, LFAST=0).

  KTH     — Test type:
              0: No threshold test (normal crack-growth analysis).
              1: ASTM E647 Appendix X3 Practice (load-shed procedure).
              2: Constant ΔK gradient test.
              3: Step-load reduction test.
              4: Constant Kmax test.
  SMAXTH  — Maximum stress applied during the threshold test.
  RTH     — Stress ratio used during the threshold test.
  CONST   — Test constant (meaning depends on KTH value; see user guide).
  PRT     — Crack-growth print interval for threshold test output.

  Leave KTH=0 for all standard crack-growth analyses.

-----------------------------------------------------------------------------
  Tab 5 — Sensitivity
-----------------------------------------------------------------------------

The Sensitivity tab runs FASTRAN repeatedly while sweeping one input variable
over a range.  The result is a parametric "design curve" showing how the
predicted fatigue life (cycles to failure) changes with that variable.

  Sweep Parameter — Choose which variable to vary (e.g., CI, CF, Smax, W).
  Min / Max / Steps — Define the sweep range and the number of evenly spaced
    evaluation points.

  Click "Run Sensitivity Analysis" to launch the batch run.  Progress is shown
  in the status bar.  Results appear as a line chart on the right side of the
  tab when the run completes.

  "Export Design Curve CSV" saves the (parameter value, predicted life) pairs
  to a comma-separated file.

  Tips:
  - A sweep over CI (initial crack size) shows how sensitive the predicted life
    is to the assumed initial flaw size — important for inspection planning and
    probabilistic damage tolerance assessments.
  - A sweep over Smax produces a stress-life (S–N) curve at a given flaw size.
  - A sweep over W shows the effect of structural width on residual life.
  - Run a single analysis on Tab 4 first to confirm the baseline case runs
    cleanly before launching a sensitivity sweep.

-----------------------------------------------------------------------------
  Output File Interpretation (.fou)
-----------------------------------------------------------------------------

FASTRAN writes results to a plain-text .fou file in the project's output/
folder.  Use Tools > Export Results to CSV to convert it to a spreadsheet.

  The .fou file contains:
  - A header with the job title, material name, date, and FASTRAN version.
  - A table of (cycles N, crack length c, crack depth a, ΔK, S'o/Smax, da/dN)
    printed at each output interval.
  - A final line showing total life in cycles and the failure mode code.

  Failure Mode Codes (NFCODE):
    0 — Kmax exceeded C5 (cyclic fracture toughness) — fracture.
    1 — Crack driving force exceeded the material da/dN resistance.
    2 — Kmax exceeded C5 (second fracture check).
    3 — Maximum applied stress exceeded 0.99 × Sflow — net-section yielding.
    4 — Kmax exceeded KIe (elastic-plastic fracture toughness).
    5 — Crack length c reached or exceeded specimen width W.
    6 — Crack length c plus plastic zone size reached or exceeded W.

  Use Tools > Compare Runs / Post-Processor to overlay .fou files from
  multiple runs on a single crack-growth or life plot.

-----------------------------------------------------------------------------
  Tools — Material Data Generator (dkeff)
-----------------------------------------------------------------------------

The dkeff tool converts raw fatigue crack-growth test data into the effective
stress-intensity-factor range (ΔKeff) vs. crack-growth-rate (da/dN) table that
FASTRAN uses in Section 7b.

Open it from the main window via  Tools > Material Data Generator (DkEff)...

[ Executable Versions ]

  dkeff13 (Legacy — DKEFF Version 1.3)
  - Input protocol: IKEFF (=1 for file input), test type, input filename,
    output filename — supplied to the EXE on stdin in that order.

  dkeff21f (Current — DKEFF Version 2.1f)
  - Updated protocol: test type, input filename, output filename — the IKEFF
    prompt is absent in this version.

  Configure the path to each EXE via  File > Configure Executable Paths...

[ Specimen Presets ]

  The "Specimen Preset" drop-down fills W, T, and ALP automatically for six
  standard ASTM E647 specimen geometries:
    M(T) 3"    — 76.2 mm wide middle-crack tension panel  (ALP=1.0)
    M(T) 4"    — 101.6 mm wide middle-crack tension panel (ALP=1.0)
    C(T) 0.5T  — 25.4 mm wide compact tension             (ALP=2.5)
    C(T) 1T    — 50.8 mm wide compact tension             (ALP=2.5)
    C(T) 2T    — 101.6 mm wide compact tension            (ALP=2.5)
    ESE(T) std — 50.8 mm wide extended single-edge crack  (ALP=2.0)

  Override individual fields after applying a preset if your specimen differs.

[ Input Parameters ]

  Specimen Type (NTYP) for dkeff:
  - 1: Middle-crack tension M(T)
  - 2: Compact tension C(T)
  - 3: Extended single-edge crack ESE(T)

  Test Type:
  - Constant R test: data collected at a fixed stress ratio R.
    Supply R and Smax for each data point.
  - Kmax test: data collected at constant Kmax.  Supply Kmax.

  Analysis Mode (NSOP):
  - NSOP=0: dkeff calculates crack length internally from ΔK and da/dN only.
    Use this when measured crack length is not available (e.g., database data).
  - NSOP=1: you supply measured crack length c alongside ΔK and da/dN.
    Most common mode for raw ASTM E647 compliance or optical measurements.
  - NSOP=2: you supply the crack-opening-stress ratio So/Smax instead of c.
    Used for advanced closure back-calculation from test data.

  Specimen Dimensions:
  - W:   Half-width for M(T); full width for C(T) and ESE(T) (mm or in).
  - T:   Specimen thickness (mm or in).
  - ALP: Constraint factor (1.0=plane stress, 2.5–3.0=near plane strain).

  Material Properties:
  - SYIELD, SULT, and E must be positive and in the same units as the test data.
    These are required before a dkeff run can proceed.

  Unit Conversion (LUNIT):
  - 0: Keep same units — no conversion applied.
  - 1: English → SI  (ksi → MPa; ksi√in → MPa√m; multiplies stresses by 6.895).
  - 2: SI → English  (MPa → ksi; MPa√m → ksi√in; divides stresses by 6.895).

[ Lab Data Table ]

  Each row represents one test data point.  Columns vary by NSOP:
    ΔK           — applied stress-intensity-factor range (input units)
    da/dN        — measured crack-growth rate (length/cycle)
    c (NSOP=1)   — measured physical crack length
    So/Smax (NSOP=2) — measured crack-opening stress ratio

  Data must be strictly ascending in both ΔK and da/dN.
  Use the "Validate Data" button to check for ordering violations before
  running dkeff — the EXE will fail silently on non-monotonic input.

[ Workflow ]

  ① Enter material properties (SYIELD, SULT, E) and analysis parameters.
  ② Enter lab data in the table, or load an existing .dkin file via
     File > Load dkeff Input File.
  ③ Click "Validate Data" to check for ordering errors.
  ④ Click "② Generate dKeff Data" to run the dkeff executable.
  ⑤ Review the raw output in the "dkeff Output" panel that appears below.
  ⑥ Click "③ Apply to Main Window" to copy the resulting ΔKeff table and
     material properties back into the FASTRAN GUI.  NTAB, CGR_TABLE, and
     the Paris-law preview on Tab 4 will update automatically.

[ Importing .lkpx Files (LK Pro-X) ]

  File > Import .lkpx Direct to Main Window
  - Parses a LK Pro-X material database XML file and lets you choose one
    R-ratio dataset.  The selected ΔK / da/dN pairs are written directly into
    CGR_TABLE on Tab 4 with NTAB set to the row count — no dkeff run required.

  File > Batch Convert .lkpx File
  - Converts a multi-R-ratio .lkpx file into a single multi-dataset .dkin
    file suitable for processing one dataset at a time through dkeff.
  1. Select the .lkpx source file.
  2. For each R-ratio found, enter Smax, W, and T.
  3. Choose an output .dkin filename.
  4. Load the result via File > Load dkeff Input File, then select a dataset
     from the list and proceed with the normal dkeff workflow.
"""


class HelpWindow(tk.Toplevel):
    """A separate window for displaying help content with incremental search."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("FASTRAN GUI - Help")
        self.geometry("800x650")

        self.last_search_query = ""
        self.last_match_end = "1.0"

        search_frame = ttk.Frame(self, padding="5")
        search_frame.pack(fill='x', side='bottom')

        ttk.Label(search_frame, text="Search:").pack(side='left', padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side='left', fill='x', expand=True)
        ttk.Button(search_frame, text="Find Next", command=self.find_next).pack(side='left', padx=5)
        ttk.Button(search_frame, text="Reset", command=self.reset_search).pack(side='left', padx=5)

        text_container = ttk.Frame(self)
        text_container.pack(fill='both', expand=True)
        self.text_widget = tk.Text(text_container, wrap='word', undo=False, font=("tahoma", 9))
        scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)

        self.text_widget.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)

        self.text_widget.insert('1.0', HELP_CONTENT)
        self.text_widget.config(state='disabled')

        self.text_widget.tag_configure("highlight", background="yellow", foreground="black")

        self.bind('<Control-f>', self.focus_search)
        self.bind('<Command-f>', self.focus_search)
        self.search_entry.bind('<Return>', self.find_next)

        self.focus_set()

    def focus_search(self, event=None):
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)
        return "break"

    def reset_search(self, event=None):
        self.text_widget.tag_remove("highlight", '1.0', tk.END)
        self.search_var.set("")
        self.last_search_query = ""
        self.last_match_end = "1.0"

    def find_next(self, event=None):
        self.text_widget.config(state='normal')
        query = self.search_var.get()
        if not query:
            self.text_widget.config(state='disabled')
            return

        if query != self.last_search_query:
            self.last_search_query = query
            self.last_match_end = "1.0"

        self.text_widget.tag_remove("highlight", "1.0", tk.END)
        pos = self.text_widget.search(query, self.last_match_end, stopindex=tk.END, nocase=True)

        if not pos:
            if messagebox.askyesno("Find", "End of document reached.\nContinue search from beginning?", parent=self):
                self.last_match_end = "1.0"
                pos = self.text_widget.search(query, self.last_match_end, stopindex=tk.END, nocase=True)
            else:
                self.last_search_query = ""
                self.last_match_end = "1.0"
                self.text_widget.config(state='disabled')
                return

        if pos:
            end_pos = f"{pos}+{len(query)}c"
            self.text_widget.tag_add("highlight", pos, end_pos)
            self.text_widget.see(pos)
            self.last_match_end = end_pos
            self.search_entry.focus_set()
        else:
            messagebox.showinfo("Find", f"Text '{query}' not found.", parent=self)
            self.last_search_query = ""
            self.last_match_end = "1.0"

        self.text_widget.config(state='disabled')


class ProgressWindow(tk.Toplevel):
    """Modal indeterminate-progress dialog used during long-running operations."""

    def __init__(self, parent, title="Processing...", message="Please wait..."):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x100")
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        ttk.Label(self, text=message, padding=(20, 10)).pack()
        self.progress = ttk.Progressbar(self, mode='indeterminate', length=260)
        self.progress.pack(pady=10)

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def start(self):
        self.progress.start(10)

    def stop(self):
        self.progress.stop()
        self.destroy()
