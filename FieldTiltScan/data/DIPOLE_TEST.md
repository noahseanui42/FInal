# Dipole known-position test (4 Oct 2026)

End-to-end accuracy check of the whole system (robot positioning, the 1044, and the
analysis). A permanent magnet is placed at a marked spot, scanned, then moved by a
measured amount and scanned again. The dipole fit should find the magnet, and the
fitted shift between runs should match the ruler shift. The shift doesn't depend on
how well the mark lines up with the robot's (0, 0), so it is the cleaner number.

## Setup

- Script: `field_scan_tilt.py`, `--correction hybrid`, coils off.
- Grid 3 × 7 × 2 = 42 points: x −50/0/+50, y −150 to +150 in 50 mm steps,
  z −700 and −600 (probe coordinates, mm). These are a subset of the full-box grid, so the
  full-box background pairs with them point for point.
- 5 s settle, 20 readings per point, speed 2. About 10 min per run.
- The magnet keeps the same orientation (pole up) in every run; only its position changes.
- Background: `full25-4z_corr-hybrid_none_20261004_155505.csv` (no magnet, same day, taken
  before these runs).

## Files

| File | Magnet position | What it is |
|---|---|---|
| `dipole_floor-y0_20261004_173137` | On the floor at the mark (0, 0) | First attempt. The magnet is about 500 mm below the bottom layer, so its field (~0.025 G) barely changes across the grid and the fit can't locate it (±40–110 mm). Kept as a record; not used in the results. |
| `dipole_y0_20261004_181805` | On a stand at the mark (0, 0) | Reference position. |
| `dipole_y+100_20261004_183221` | On the stand, moved +100 mm in y | First known move. |
| `dipole_y-100_20261004_184523` | On the stand, moved −100 mm in y (from the mark) | Second known move, opposite direction. |

Each is a `.csv` with a matching `.meta.json`. They were renamed from the script's longer
names; each `.meta.json` keeps the original name in `renamed_from`.

Still to record: the magnet centre height (floor + stand + half the magnet) and the magnet's
size. The y0 run's note has blanks for these.

## Results

Magnet field with the background subtracted: 0.04–0.25 G per point (median about 0.1 G),
about 250 × the sensor noise. All 126 points reached (`err` 0), 20 readings each, no
saturation, no sensor reconnects.

### Joint fit (the result to quote)

One magnetic moment shared by all three runs (the magnet wasn't rotated), one position per run:

```
python FieldPlots/fit_dipole_joint.py \
  FieldTiltScan/data/full25-4z_corr-hybrid_none_20261004_155505.csv \
  FieldTiltScan/data/dipole_y0_20261004_181805.csv \
  FieldTiltScan/data/dipole_y+100_20261004_183221.csv \
  FieldTiltScan/data/dipole_y-100_20261004_184523.csv
```

| Run | Fitted position (mm) | ± (1σ, mm) |
|---|---|---|
| y0 | (7.3, −34.2, −976.7) | (4.6, 3.2, 2.4) |
| y+100 | (14.9, 65.8, −974.2) | (4.6, 3.2, 2.4) |
| y−100 | (4.4, −133.6, −977.4) | (4.7, 3.5, 2.4) |

| Move | Ruler | Fitted shift (x, y, z) mm | Fitted length | Error |
|---|---|---|---|---|
| y0 → y+100 | 100 | (7.5, 99.9, 2.5) | 100.2 mm | +0.2 mm |
| y0 → y−100 | 100 | (−2.9, −99.4, −0.7) | 99.5 mm | −0.5 mm |
| y−100 → y+100 | 200 | (10.5, 199.3, 3.2) | 199.6 mm | −0.4 mm |

Shared moment 2.60 A·m², 9.5° from vertical. Residual RMS 0.012 G.

- **Shift length:** within 0.5 mm of the ruler for all three moves.
- **Height:** the fitted z agrees across the runs to 3 mm, as it should with the same stand.
- **Direction:** the moves come out 2–4° off the robot's y axis (about 10 mm of x over the
  200 mm move). That is within what a ruler placement along a floor line can give, so it
  doesn't show a sensor rotation on its own.
- **Absolute position:** the magnet at the mark fits at (7, −34) mm, not (0, 0). Either the
  mark is about 34 mm off the robot's (0, 0) in y, or there is a fixed offset in the system.
  The 3 Oct magnet-under scan also fitted at y ≈ −31 mm. Checking the mark with the probe
  (jog to (0, 0) at the lowest z and drop a plumb line) would separate the two.
- **Magnet depth:** about 275 mm below the bottom layer (z −700), deeper than the planned
  150 mm. Compare with the measured stand height once it's recorded.

### One fit per run (`fit_dipole.m`)

Fitting each run on its own gives positions about ±7 mm (1σ), but the moment direction
changes from run to run (10–28° from vertical, in different directions) even though the
magnet wasn't rotated. At this depth the moment's tilt and the magnet's position trade off,
so the single-run shifts come out 114 and 117 mm for the 100 mm moves (14–17 mm off). The joint fit removes that by sharing the
moment, which is why it is the one to quote.

## Next

- `dipole_x-50_…`: the magnet moved −50 mm in x from the mark, to test the x direction (running).
