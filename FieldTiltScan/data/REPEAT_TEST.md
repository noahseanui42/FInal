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
whole grid:

| Run | Start | Mean change from run 1 (Bx, By, Bz) G |
|---|---|---|
| 2 | 18:19 | (+0.0024, −0.0013, +0.0016) |
| 3 | 18:34 | (+0.0041, −0.0028, +0.0024) |
| 4 | 18:48 | (+0.0065, −0.0039, +0.0030) |
| 5 | 19:03 | (+0.0093, −0.0049, +0.0011) |

About 0.01 G over the hour, the same at every point, so it is an offset drift (sensor
warm-up or the room), not the magnet moving. Practical consequence: take the no-magnet
reference close in time to the scan it is subtracted from, or alternate them.

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

The magnet's exact position isn't needed for this test: only that it stayed put, which the
fitted positions confirm. Its distance below the grid matters for sensitivity (a closer magnet
gives a stronger gradient, so a position error shows up as a larger field change); at
1.16 mG/mm median gradient and 0.2 mG sensor noise, the test resolves about 0.2 mm, well
below the 2.2 mm measured.
