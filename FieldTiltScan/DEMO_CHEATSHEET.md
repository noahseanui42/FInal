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
root in a terminal, 9 points at z −650, about 1–2 min:

```
python FieldTiltScan/field_scan_tilt.py --label demo_live --correction hybrid --x -50 50 3 --y -50 50 3 --z -650 -650 1
```

Then in MATLAB (from `FieldTiltScan`), plot the newest `demo_live` scan:

```matlab
d = dir("data/demo_live_*.csv"); [~, i] = max([d.datenum]);
f = fullfile(d(i).folder, d(i).name);
plot_field_layers(f, "", "Figures", "heat")
plot_tilt(f)
```

No background is subtracted here, so |B| includes Earth's field (about 0.5 G).

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
