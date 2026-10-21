# Demo cheat sheet

Commands for every plot in the artefact demo, in the order to show them.
Everything runs from `FieldTiltScan` in MATLAB unless it says otherwise.

## 0. Setup (once)

```matlab
cd FieldTiltScan
addpath ../FieldPlots
close all
```

## 1. Full-volume field map (magnet only, 260 points, 4 layers)

```matlab
plot_field_layers("data/full25-4z_corr-hybrid_under_combined_20261003.csv", ...
    "data/full25-4z_corr-hybrid_none_20261004_155505.csv", ...
    "Figures", {"heat","3d"}, "TiltCorrect", true, "Labels", false)
```

- Heat map per layer plus the 3D stack. Rotate the 3D figure with the mouse.
- Background (no magnet) subtracted, so it's the magnet's field only.
- Say: the background was taken the next day, and drift is about 11 mG/h.

Other views of the same scan, if asked:

```matlab
% field direction per layer, and side views
plot_field_layers("data/full25-4z_corr-hybrid_under_combined_20261003.csv", ...
    "data/full25-4z_corr-hybrid_none_20261004_155505.csv", ...
    "Figures", {"direction","side"}, "TiltCorrect", true)

% 3D arrows, length = field strength
plot_field_arrows3d("data/full25-4z_corr-hybrid_under_combined_20261003.csv", ...
    "data/full25-4z_corr-hybrid_none_20261004_155505.csv", "TiltCorrect", true)
```

## 2. Probe tilt (why FieldTiltScan exists)

```matlab
plot_tilt("data/full25-4z_corr-hybrid_under_combined_20261003.csv")
```

- Show figure 1 (tilt map per layer), close the rest.
- Then open the saved image of what the correction changes (up to about 40 mG):
  `figures/magnet_tilt_20261002_223300/correction_change.png`
- Say: tilt up to about 2°, the field change from it is about 20 × the 2 mG
  run-to-run spread, so it has to be logged and corrected.

## 3. Repeatability (5 runs, magnet fixed, 6 Oct)

```matlab
compare_repeat_heatmaps("Units", "mG", "Labels", false)
```

- Finds the files itself. Figure 1: runs 1–5 look the same. Figure 2: change
  between runs, 1.4–1.9 mG median per point.
- Say: 2.2 mm median position repeatability, matching the pen-and-ruler tests:

  $$\sigma_{pos} = \frac{\sigma_B}{|\nabla B|}$$

Extra views, if asked:

```matlab
% every run against run 1 (shows the drift growing, 1.7 % -> 3.1 %)
repeatability_heatmaps("Pairs", [1 2; 1 3; 1 4; 1 5])

% position repeatability (mm) per layer
R = compare_runs("data/repeat_under-run*.csv", "data/repeat_none_20261006_192127.csv", "Plot", false);
plot_repeatability_layers(R, "Title", "5 runs, magnet fixed")
```

## 4. Dipole accuracy (open the saved image, don't run live)

Open `data/dipole_joint_fit.png`.

- y moves within 1.3 mm of the ruler (100 and 200 mm).
- x moves off by −10 / +6 mm: the grid is only 100 mm wide in x, so x is about
  5.5 mm 1σ on a shift; these are 1–2σ.

To regenerate it (Python, needs numpy, pandas, scipy, matplotlib; slow), from
`FieldTiltScan` in a terminal:

```
python ../FieldPlots/fit_dipole_joint.py --plot data/full25-4z_corr-hybrid_none_20261004_155505.csv \
  data/dipole_y0_20261004_181805.csv data/dipole_y+100_20261004_183221.csv \
  data/dipole_y-100_20261004_184523.csv data/dipole_x-50_20261004_185954.csv \
  data/dipole_x+50_20261004_191247.csv
```

## 5. Optional: live scan (only after 1–4 have gone well)

Close the delta app first (only one program can use the serial port). From the repo
root in a terminal, 9 points at z −650, about 2 min:

```
cd /Users/rochelle/FInal
python FieldTiltScan/field_scan_tilt.py --label demo_live --correction hybrid --x -50 50 3 --y -50 50 3 --z -650 -650 1
```

It parks at (0, 0, −650) and zeroes the gyro (keep the table still), then prints a
line per point. Ctrl+C stops it and keeps the points so far. At the end the robot
stays enabled (disabling drops the arms).

### Choosing the size

```
python FieldTiltScan/field_scan_tilt.py --label demo_live --correction hybrid --x XMIN XMAX NX --y YMIN YMAX NY --z ZMIN ZMAX NZ
```

Each axis is min, max, number of points (evenly spaced, mm, probe tip, robot frame).
One value on an axis: min = max and 1 point. Keep inside x ±50, y ±150, z −700 to
−600 (where the hybrid correction was validated; outside it the script warns).
Past scans took about 12–14 s per point, so time ≈ points × 13 s.

| Size | Grid options | Points | Time |
|---|---|---|---|
| Quickest | `--x -50 50 2 --y -50 50 2 --z -650 -650 1` | 4 | ~1 min |
| Small (demo) | `--x -50 50 3 --y -50 50 3 --z -650 -650 1` | 9 | ~2 min |
| Medium | `--x -50 50 3 --y -100 100 5 --z -650 -650 1` | 15 | ~3–4 min |
| Two layers | `--x -50 50 3 --y -50 50 3 --z -700 -600 2` | 18 | ~4 min |
| Large | `--x -50 50 5 --y -100 100 5 --z -700 -600 2` | 50 | ~11 min |

- At least 2 points in x and y, or the heat map has nothing to fill in.
- Keep `--label demo_live` so section 5 of `demo_plots.m` finds it.
- `--correction hybrid` is a real setting (not part of the name): it adjusts each
  move to cancel the robot's known positioning errors, as in all the saved results.
  Needs numpy; leave it out only if numpy is missing (the scan then runs uncorrected).
- `--settle 2` saves about 3 s per point, but the probe may still be swaying.
- Port: the script uses `/dev/cu.usbmodem14101`. Check with `ls /dev/cu.usbmodem*`
  and add `--port /dev/cu.usbmodemXXXX` if it differs.
- Dry run without hardware: `python FieldTiltScan/field_scan_tilt.py --simulate --label demo_test`
  (then delete the `demo_test` files from `data/`).

Then in MATLAB (from `FieldTiltScan`), plot the newest `demo_live` scan:

```matlab
d = dir("data/demo_live_*.csv"); [~, i] = max([d.datenum]);
f = fullfile(d(i).folder, d(i).name);
plot_field_layers(f, "", "Figures", "heat")
plot_tilt(f)
```

No background is subtracted here, so |B| is the raw field: Earth's field plus the
robot's own (about 0.7 G with no magnet).

## Saving PNG backups beforehand

Add `"Save", true` to any command above (plots 1–3) to write PNGs next to the CSV.
Do this the day before, so you can show the images if MATLAB is slow on the day.

## Likely questions

| Question | Answer |
|---|---|
| Why are the x moves off in the dipole test? | x grid only 100 mm wide (y is 300 mm), so x is pinned less well; errors are 1–2σ. A wider x grid (±150) would fix it. |
| What's the drift? | About 11 mG over the hour, uniform over the grid. ~17 % from the probe tilting as it warms, the rest most likely thermal (sensor offset, servo magnets). Take the background close in time, or fit a per-run offset. |
| Where's the Helmholtz field? | All scans so far are coils off; the magnet stands in for a known field source. |
| Is the noise from the sensor? | No: one point's sensor noise is about 0.2 mG, the run-to-run spread is about 2 mG, so the spread comes from positioning and settling. |

## Running it from one file

`demo_plots.m` (this folder) has every command above as a section. Open it, `cd`
into `FieldTiltScan`, click in a section and press Ctrl+Enter (Cmd+Enter on a Mac)
to run just that one. Run section 0 first.
