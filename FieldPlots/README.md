# FieldPlots

MATLAB plots and analysis for the field scans in `../FieldScan/data` and
`../FieldTiltScan/data`. Every script reads the scan CSVs written by
`field_scan.py`, `field_scan_tilt.py` or `run_field_scan.m`.

## How to run

Work from inside the scan folder and put this folder on the path. The scripts
then find `data/...` and that folder's `scan_config.m` (sensor → robot rotation,
TCP offset).

```matlab
cd FieldScan                 % or FieldTiltScan
addpath ../FieldPlots
```

## Field maps

| Script | What it shows |
|---|---|
| `plot_field_layers.m` | Heat map and direction map per z layer, side views, stacked 3D layers |
| `plot_field_arrows3d.m` | 3D field arrows, one colour per z layer |
| `plot_field_map.m` | Field map plus the Helmholtz % uniformity plot on the middle z plane |
| `plot_correction_map.m` | What the position correction did: where each point was aimed vs the target |

```matlab
plot_field_layers("data/magnet-xpos_corr-hybrid_run1_20261002_182828.csv", ...
                  "data/nomagnet_corr-off_run1_20261002_172221.csv")
plot_field_arrows3d("data/magnet-under_corr-hybrid_run1_20261002_205751.csv")
plot_correction_map("data/magnet-xpos_corr-hybrid_run1_20261002_182828.csv")
```

The second argument is optional: a baseline scan (no magnet / coils off) that is
subtracted point by point. `plot_field_layers`, `plot_field_arrows3d`,
`plot_correction_map` and `plot_tilt` take `"Save", true` to write PNGs next to
the CSV.

## Repeatability

| Script | What it does |
|---|---|
| `compare_runs.m` | Spread of a fixed magnet across repeated scans (`"Plot", false` for numbers only) |
| `compare_repeatability.m` | Two `compare_runs` results side by side, e.g. correction off vs hybrid |
| `plot_repeatability_layers.m` | A `compare_runs` result as maps, one panel per z layer |
| `compare_positions.m` | Repeatability at several magnet positions |

```matlab
off = compare_runs("data/magnet-xpos_corr-off_run*.csv", "data/nomagnet_corr-off_run1_20261002_172221.csv");
hyb = compare_runs("data/magnet-xpos_corr-hybrid_run*.csv", "data/nomagnet_corr-off_run1_20261002_172221.csv");
compare_repeatability(off, hyb)
plot_repeatability_layers(hyb)
```

## Tilt (FieldTiltScan scans)

| Script | What it does |
|---|---|
| `plot_tilt.m` | Tilt map per z layer, gyro settling, pitch/roll maps, board vs accelerometer check |
| `tilt_correct.m` | Tilt per point from the accelerometer; field rotated back to a reference orientation; optional `_tiltcorr.csv` |
| `apply_tilt.m` | What the plots' `"TiltCorrect"` option runs |
| `fit_dipole.m` | Point-dipole fit (moment + position) with residuals |
| `compare_tilt_runs.m` | Repeated tilt scans: repeatability and dipole-fit accuracy, raw vs tilt-corrected |
| `compare_heatmaps.m` | % change in the \|B\| heat map from each run to the next (1→2, 2→3, …), per point and per z layer |

```matlab
cd FieldTiltScan
addpath ../FieldPlots
plot_tilt("data/magnet_tilt_20261002_223300.csv")
plot_field_layers("data/magnet_tilt_20261002_223300.csv", "", "TiltCorrect", true)
fit_dipole("data/magnet_tilt_20261002_223300_tiltcorr.csv")
```

`compare_heatmaps()` with no arguments compares the five dipole runs
(`DIPOLE_TEST.md`) in the order they were taken, each minus the no-magnet
background: change = 100 × (|B| of run k+1 − |B| of run k) / |B| of run k.
Give it your own files (or a wildcard, sorted by time stamp) for other runs:

```matlab
compare_heatmaps()                                         % the five dipole runs
compare_heatmaps("data/dipole_*.csv", "data/full25-4z_corr-hybrid_none_20261004_155505.csv")
D = compare_heatmaps([], [], "Save", true);                % + heatmap_change*.png in data/
```

`plot_field_layers`, `plot_field_arrows3d` and `plot_field_map` take
`"TiltCorrect", true` only for scans with accelerometer columns (from
`field_scan_tilt.py`). Without the option they behave as before and work on
every scan.

## Tests (no hardware)

`test_tilt_correct.m`, `test_fit_dipole.m` and `test_compare_tilt_runs.m` check
the tilt correction, dipole fit and tilt-run comparison on synthetic scans.
`scan_grid.m` is the serpentine grid generator they use.
