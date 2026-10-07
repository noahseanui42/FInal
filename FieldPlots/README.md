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
the CSV. `plot_field_layers` draws four figures; `"Figures"` picks some of them:
`{"heat", "direction", "side", "3d"}` or the numbers 1–4, e.g.
`plot_field_layers(file, bg, "Figures", {"heat", "3d"})`.

## Repeatability

| Script | What it does |
|---|---|
| `compare_runs.m` | Spread of a fixed magnet across repeated scans (`"Plot", false` for numbers only) |
| `compare_repeatability.m` | Two `compare_runs` results side by side, e.g. correction off vs hybrid |
| `plot_repeatability_layers.m` | A `compare_runs` result as maps, one panel per z layer |
| `compare_positions.m` | Repeatability at several magnet positions |
| `compare_repeat_heatmaps.m` | The 6 Oct repeat test on its own: heat maps of the no-magnet reference and runs 1–5, and the % change 1→2 … 4→5. Finds the files itself; needs no other file |
| `repeatability_heatmaps.m` | % difference in the \|B\| heat map between repeated scans of the same setup (6 Oct five-run test, or the 2 Oct pairs) |

```matlab
off = compare_runs("data/magnet-xpos_corr-off_run*.csv", "data/nomagnet_corr-off_run1_20261002_172221.csv");
hyb = compare_runs("data/magnet-xpos_corr-hybrid_run*.csv", "data/nomagnet_corr-off_run1_20261002_172221.csv");
compare_repeatability(off, hyb)
plot_repeatability_layers(hyb)
```

`repeatability_heatmaps()` maps repeat runs as a % difference per point, each run
minus its no-magnet scan. By default it uses the 6 Oct repeat test
(`FieldTiltScan/data/REPEAT_TEST.md`, five runs, 1→2 … 4→5);
`repeatability_heatmaps("2oct")` uses the 2 Oct pairs above (correction off,
hybrid, magnet-under). It uses `compare_heatmaps` (below), so it takes the same
options, e.g. `"Save", true` or `"Pairs", [1 2; 1 3; 1 4; 1 5]` for every run
against run 1.

## Tilt (FieldTiltScan scans)

| Script | What it does |
|---|---|
| `plot_tilt.m` | Tilt map per z layer, gyro settling, pitch/roll maps, board vs accelerometer check |
| `tilt_correct.m` | Tilt per point from the accelerometer; field rotated back to a reference orientation; optional `_tiltcorr.csv` |
| `apply_tilt.m` | What the plots' `"TiltCorrect"` option runs |
| `fit_dipole.m` | Point-dipole fit (moment + position) with residuals |
| `compare_tilt_runs.m` | Repeated tilt scans: repeatability and dipole-fit accuracy, raw vs tilt-corrected |
| `compare_heatmaps.m` | % change in the \|B\| heat map from each run to the next (1→2, 2→3, …, or chosen `"Pairs"`), per point and per z layer |

```matlab
cd FieldTiltScan
addpath ../FieldPlots
plot_tilt("data/magnet_tilt_20261002_223300.csv")
plot_field_layers("data/magnet_tilt_20261002_223300.csv", "", "TiltCorrect", true)
fit_dipole("data/magnet_tilt_20261002_223300_tiltcorr.csv")
```

`compare_heatmaps` works on any runs: change = 100 × (|B| of run k+1 − |B| of
run k) / |B| of run k at every point, each run minus a background scan if you give
one. With no file names it opens a file dialog: pick the runs (Ctrl+click for
several; they're sorted by the time stamp in their names), then the no-magnet
scan (Cancel for none). It needs only `compare_heatmaps.m` itself, so it can be
copied into any folder of CSVs.

```matlab
compare_heatmaps()                                         % pick the files
compare_heatmaps("Save", true)                             % pick, and save PNGs next to them
compare_heatmaps("data/dipole_*.csv", "data/full25-4z_corr-hybrid_none_20261004_155505.csv")
compare_heatmaps({"run1.csv", "run2.csv", "run3.csv"}, "background.csv")   % in this order
```

`plot_field_layers`, `plot_field_arrows3d` and `plot_field_map` take
`"TiltCorrect", true` only for scans with accelerometer columns (from
`field_scan_tilt.py`). Without the option they behave as before and work on
every scan.

## Tests (no hardware)

`test_tilt_correct.m`, `test_fit_dipole.m` and `test_compare_tilt_runs.m` check
the tilt correction, dipole fit and tilt-run comparison on synthetic scans.
`scan_grid.m` is the serpentine grid generator they use.
