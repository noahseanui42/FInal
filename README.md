# ENGR489: Delta robot field mapping

Code and data for the ENGR489 capstone (VUW): a delta robot that moves a
Phidget 1044 magnetometer probe through a grid to map the magnetic field inside
a Helmholtz coil.

## Folders

| Folder | What it is |
|---|---|
| [`DeltaApp/`](DeltaApp) | The original delta robot software: Python GUI and scan runner (`delta_app/`), Arduino servo firmware (`delta_servo/`) and host tests (`tests/`). Pre-calibration geometry. |
| [`DeltaAppCalibrated/`](DeltaAppCalibrated) | The same software with the calibrated servo firmware. **Use this one on the robot.** |
| [`FieldPlots/`](FieldPlots) | MATLAB plots and analysis for the scans: field maps, repeatability, tilt correction, dipole fit. |
| [`FieldScan/`](FieldScan) | Field-mapping scan: MATLAB link to the robot and the 1044, and all the scans from 2 Oct 2026. |
| [`FieldTiltScan/`](FieldTiltScan) | FieldScan plus the probe's tilt (pitch/roll) and gyro logged at every point, and the first tilt run. |
| [`ReportFigures/`](ReportFigures) | Report-ready figures for every test, with a note on each test in [`FIGURE_NOTES.md`](ReportFigures/FIGURE_NOTES.md). Rebuilt by `python ReportFigures/make_report_figures.py`. |

### DeltaApp and DeltaAppCalibrated

Both have the same layout:

- `delta_app/`: the Python GUI (`main.py`) for connecting, enabling, jogging and
  checking reach. It also holds `field_scan.py`, which runs a scan and writes a
  CSV to `FieldScan/data/`, and `pose_correction.py`, the `--correction hybrid`
  position correction.
- `delta_servo/`: Arduino UNO R4 firmware for the 3 servos (inverse
  kinematics, motion, serial protocol).
- `tests/`: host tests for the firmware and the Python side.

The calibrated version differs in:

- The measured geometry (SP 75 mm, L_UP 177 mm, arm remap `GEOM_TO_PHYS`).
- The servo calibration refitted from the 2026-09-30 protractor sweep.
- Backlash take-up: every point is approached moving up.
- `tools/servo_sweep/`, which holds the sweep sketch, sweep data, calibration
  sheets and log.

Its `config.h` and `robot_config.py` match the geometry the hybrid position
correction was fitted with. `DeltaApp/` is kept for comparison.

Each folder's README covers geometry, licences (GPL-3.0, derived from
`grzesiek2201/Delta-Robot`) and setup.

### FieldScan

Scans are run with `DeltaAppCalibrated/delta_app/field_scan.py`. This folder
holds the MATLAB side and the data:

- `data/`: every scan as a `.csv` with a matching `.meta.json`. Covers the
  no-magnet background, the magnet at x+, x− and under the centre, with
  correction off and hybrid, plus repeat runs. Aborted and check runs are in
  `data/checks/`. File naming is explained in `data/INDEX.md`.
- `run_field_scan.m` and `scan_config.m`: a MATLAB-only fallback scan, plus the
  grid and sensor settings the plots use.
- `delta_*.m` and `mag_*.m`: the serial link to the robot, and reads from the
  1044.

### FieldTiltScan

Uses the 1044's Spatial channel so each row also has acceleration, gyro and
pitch/roll. That lets the field be corrected for the probe tilting as the robot
moves.

- `field_scan_tilt.py`: the scan. It uses `DeltaAppCalibrated/delta_app/` for
  the robot link and the position correction.
- `data/` and `figures/`: the first tilt run (magnet underneath, hybrid
  correction), raw and tilt-corrected.
- The MATLAB fallback scan and the 1044 helpers, as in FieldScan.

### FieldPlots

Run the plots from inside a scan folder, so they find `data/` and that
folder's `scan_config.m`:

```matlab
cd FieldScan            % or FieldTiltScan
addpath ../FieldPlots
plot_field_layers("data/magnet-xpos_corr-hybrid_run1_20261002_182828.csv", ...
                  "data/nomagnet_corr-off_run1_20261002_172221.csv")
```

See [`FieldPlots/README.md`](FieldPlots/README.md) for every script.

## Quick start

```
cd DeltaAppCalibrated/delta_app
python -m pip install -r requirements.txt numpy
python main.py                                    # GUI: connect, enable, jog
cd ../..
python DeltaAppCalibrated/delta_app/field_scan.py --simulate --label demo   # scan without hardware
python FieldTiltScan/field_scan_tilt.py --simulate --label demo             # tilt scan without hardware
```

Close the GUI before a scan: only one program can use the Arduino's serial
port at a time. Full scan instructions are in
[`FieldScan/README.md`](FieldScan/README.md) and
[`FieldTiltScan/README.md`](FieldTiltScan/README.md).

## Tests

```
python -m pytest DeltaAppCalibrated/tests FieldTiltScan
```

The MATLAB checks are `FieldPlots/test_tilt_correct.m`, `test_fit_dipole.m`
and `test_compare_tilt_runs.m`. They need no hardware.
