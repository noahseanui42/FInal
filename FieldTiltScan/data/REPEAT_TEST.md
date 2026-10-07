# Repeatability test (6 Oct 2026)

Five scans of the full volume back to back with the magnet fixed under the grid, then one
scan with the magnet removed. Nothing was touched between the five runs, so any difference
between them is the system's repeatability (robot positioning, sensor, settling) plus drift.

## Setup

- Script: `field_scan_tilt.py`, `--correction hybrid`, coils off, run in a shell loop.
- Grid 5 × 7 × 2 = 70 points: x −50 to +50 in 25 mm steps, y −150 to +150 in 50 mm steps,
  z −700 and −600 (probe coordinates, mm). A subset of the full-box grid.
- 5 s settle, 20 readings per point, speed 2. About 14 min per run, 18:05 to 19:18.
- Magnet under the grid, 270 mm above the floor; its fitted depth is about z −975 to −990,
  roughly 280 mm below the bottom layer. Magnet-only field 0.07–0.25 G per point.
- Height cross-check: the dipole test (magnet 260 mm above the floor, fitted z ≈ −980) puts
  the floor at about z −1240, so this magnet should be at about −970. The fit with a per-run
  offset gives −974 to −976 (about 5 mm off); without offsets −987 to −989.

## Files

| File | What it is |
|---|---|
| `repeat_under-run1_20261006_180203` … `run5_20261006_190323` | The five repeats, magnet fixed. |
| `repeat_none_20261006_192127` | Same grid, magnet removed (reference / noise floor). |

All 70 points reached in every run (`err` 0), 20 readings each, no gaps. The 1044 reconnected
over USB twice (run 4 before point 1, run 5 before point 54); the script restored the data
rate and both are listed in `sensor_reconnected_at_points`. Run 4's gyro columns read about
1.2 °/s high because the reconnect came after the gyro was zeroed; field and tilt are unaffected.

## Results

### Field at each point

| | Value |
|---|---|
| Spread of \|B\| across the 5 runs, per point (1σ) | 2.0 mG median, 4.8 mG at the 95th percentile |
| Same, after removing a uniform offset per run | 1.9 mG median, 4.0 mG at the 95th percentile |
| Sensor noise of one point (20 readings) | about 0.2 mG per axis |

The run-to-run spread is about 10 × the sensor noise, so it comes from the system
(positioning and settling), not from the sensor's own noise.

### Drift

Each run reads slightly higher in Bx and lower in By than the one before, evenly across the
whole grid. The probe also tilts slowly over the hour (accelerometer pitch and roll, mean over
the 70 points):

| Run | Start | Mean pitch (°) | Mean roll (°) | Δpitch vs run 1 (°) | Δroll vs run 1 (°) | Drift vs run 1 (Bx, By, Bz) mG | Drift size (mG) | Tilt alone would give (mG) | Share from tilt |
|---|---|---|---|---|---|---|---|---|---|
| run 1 | 18:05 | 1.04 | −0.50 | 0 | 0 | (0, 0, 0) | 0 | 0 | n/a |
| run 2 | 18:19 | 1.04 | −0.46 | +0.006 | +0.042 | (+2.4, −1.3, +1.6) | 3.2 | 0.6 | 19% |
| run 3 | 18:34 | 1.07 | −0.44 | +0.038 | +0.057 | (+4.1, −2.8, +2.4) | 5.5 | 1.0 | 17% |
| run 4 | 18:48 | 1.12 | −0.43 | +0.080 | +0.074 | (+6.5, −3.9, +3.0) | 8.2 | 1.5 | 19% |
| run 5 | 19:03 | 1.13 | −0.43 | +0.094 | +0.074 | (+9.3, −4.9, +1.1) | 10.6 | 1.7 | 16% |
| no magnet | 19:21 | 1.15 | −0.44 | +0.118 | +0.059 | n/a | n/a | n/a | n/a |

"Tilt alone would give" is the field change from rotating run 1's measured field by that
run's change in pitch and roll (|ω × B|, averaged over the points).

- **About 11 mG (1.1 µT) over the hour**, the same at every point: an offset drift, not the
  magnet moving (the fitted magnet position stays put once each run gets its own offset).
- **The probe tilt keeps changing** (+0.12° pitch, +0.06° roll by the end), steadily: likely
  mechanical creep as the servos and printed parts warm. It explains about 17% of the drift.
- **The other ~83%** is most likely thermal: the 1044's magnetometer offset warming up, or the
  servo motors' magnets weakening as they warm (the robot adds about 0.15 G at the probe, and
  magnets lose about 0.1% per °C). Room disturbances can't be ruled out. A 30 min fixed-point
  log with the servos powered and unpowered would separate these.
- **Effect:** at the 1.16 mG/mm median gradient, 11 mG is worth about 8 mm of apparent
  position, so it has to be handled: take the no-magnet reference close in time to the scan,
  let the rig warm up before scanning, or fit a per-run offset.

### Position repeatability

- **Per point, sigma_pos = sigma_B / |grad B|** (what `compare_runs` reports): **2.2 mm
  median** (2.8 mm at the 75th percentile, 4.9 mm at the 95th). With the uniform drift removed:
  1.7 mm median. This matches the 2–2.5 mm repeatability from the pen-and-ruler tests.
- **Fitted magnet position across the 5 runs** (joint fit, one shared moment): with a
  separate constant offset per run to absorb the drift, the five positions agree to
  0.7 mm (x), 0.2 mm (y), 1.1 mm (z) 1σ, all within 2.1 mm of their mean. Without the
  offsets, the drift is mistaken for movement and the fitted x walks 10.6 mm across the
  five runs, steadily in one direction.
- **Absolute position is not pinned by this test.** At this depth a constant offset and the
  magnet position trade off: fitting with and without offsets puts the magnet at about
  (53, 7, −975) and (8, −19, −989) mm respectively, with the same run-to-run spread. Use the
  dipole test for position accuracy; this test is for repeatability.

## Plots (MATLAB, from `FieldTiltScan`)

```matlab
addpath ../FieldPlots
R = compare_runs("data/repeat_under-run*.csv", "data/repeat_none_20261006_192127.csv", "Plot", false);
plot_repeatability_layers(R, "Title", "5 runs, magnet fixed")
plot_field_layers("data/repeat_under-run1_20261006_180203.csv", "data/repeat_none_20261006_192127.csv", "Figures", "3d")
```

% difference in the |B| heat map from each run to the next (1→2 … 4→5, magnet field only):

```matlab
compare_repeat_heatmaps()                                  % standalone: reference + runs, % change
compare_repeat_heatmaps("Units", "mG")                     % same, change in mG
repeatability_heatmaps()                                   % maps, bar chart and table
repeatability_heatmaps("Pairs", [1 2; 1 3; 1 4; 1 5])     % every run against run 1
```

Mean size of the difference between consecutive runs: 1.5–1.9 % per point (largest
9.2 %, all the largest on the top layer, z −600, where the field is weakest). Against
run 1 it grows from 1.7 % (run 2) to 3.1 % (run 5): the drift above.

In mG the change between consecutive runs is 1.4–1.9 mG median per point (2.3–3.1 mG
RMS, largest 11.7 mG), about the same on both layers. The % is bigger on the top layer
only because the magnet's field there is weaker (≈0.09 G against ≈0.2 G at z −700).

The magnet's exact position isn't needed for this test: only that it stayed put, which the
fitted positions confirm. Its distance below the grid matters for sensitivity (a closer magnet
gives a stronger gradient, so a position error shows up as a larger field change); at
1.16 mG/mm median gradient and 0.2 mG sensor noise, the test resolves about 0.2 mm, well
below the 2.2 mm measured.
