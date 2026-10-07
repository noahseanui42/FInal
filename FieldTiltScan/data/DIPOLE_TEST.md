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
| `dipole_x-50_20261004_185954` | On the stand, moved −50 mm in x (from the mark) | Known move in x. |
| `dipole_x+50_20261004_191247` | On the stand, moved +50 mm in x (from the mark) | Known move in x, opposite direction. Started with `--magnet x-50` by mistake; the note and the fit both put it at +50, so it was renamed. |
| `checks/ABORTED-0pts_dipole_x-50_20261004_185916` | (x −50) | Stopped before the first point; no data. |

Each is a `.csv` with a matching `.meta.json`. They were renamed from the script's longer
names; each `.meta.json` keeps the original name in `renamed_from`.

## Results

Magnet field with the background subtracted: 0.04–0.25 G per point (median about 0.1 G),
about 250 × the sensor noise. All 210 points reached (`err` 0), 20 readings each, no
saturation, no sensor reconnects.

### Joint fit (the result to quote)

One magnetic moment shared by all five runs (the magnet wasn't rotated), one position per run:

```
cd FieldTiltScan
python ../FieldPlots/fit_dipole_joint.py --plot data/full25-4z_corr-hybrid_none_20261004_155505.csv \
  data/dipole_y0_20261004_181805.csv data/dipole_y+100_20261004_183221.csv \
  data/dipole_y-100_20261004_184523.csv data/dipole_x-50_20261004_185954.csv \
  data/dipole_x+50_20261004_191247.csv
```

Add `--plot` to also draw the comparison figure, saved as
[`dipole_joint_fit.png`](dipole_joint_fit.png): the magnet's field on the bottom layer for each
run with the fitted (×) and ruler (○) positions, a top view of all five, and the shift table.

| Run | Fitted position (mm) | ± (1σ, mm) |
|---|---|---|
| y0 | (4.6, −32.7, −981.2) | (3.9, 2.7, 2.0) |
| y+100 | (12.3, 68.0, −978.5) | (3.9, 2.7, 1.9) |
| y−100 | (1.6, −133.0, −981.9) | (4.0, 2.9, 2.0) |
| x−50 | (−35.1, −29.2, −980.3) | (3.9, 2.7, 2.0) |
| x+50 | (60.1, −38.8, −977.1) | (3.9, 2.7, 2.0) |

Shared moment 2.71 A·m², 7.8° from vertical. Residual RMS 0.0125 G over 210 points.

| Move | Ruler | Fitted shift (x, y, z) mm | Fitted length | Error |
|---|---|---|---|---|
| y0 → y+100 | 100 | (7.7, 100.8, 2.7) | 101.1 mm | +1.1 mm |
| y0 → y−100 | 100 | (−3.0, −100.2, −0.7) | 100.3 mm | +0.3 mm |
| y−100 → y+100 | 200 | (10.7, 201.0, 3.4) | 201.3 mm | +1.3 mm |
| y0 → x−50 | 50 | (−39.7, 3.5, 0.9) | 39.9 mm | −10.1 mm |
| y0 → x+50 | 50 | (55.4, −6.1, 4.1) | 55.9 mm | +5.9 mm |
| x−50 → x+50 | 100 | (95.2, −9.6, 3.2) | 95.7 mm | −4.3 mm |

- **y moves:** within 1.3 mm of the ruler, over 100 and 200 mm.
- **x moves:** the 100 mm span fits at 95.7 mm (−4.3 mm). The single 50 mm moves are off by
  −10 and +6 mm. The grid is only 100 mm wide in x (300 mm in y), so x is pinned less well:
  1σ is about 4 mm per position, about 5.5 mm on a difference, so these errors are 1–2σ.
  A wider x grid (it can go to ±150) would tighten it.
- **Direction:** both sets of moves come out turned the same way: the y moves 3.0° and the
  x moves 5.8°, both clockwise seen from above. A consistent turn like this means the
  ruler's axes on the floor were about 4° off the robot's axes, or the sensor is turned by
  about that much in its holder. This test can't separate the two; squaring the floor line
  to the robot frame (jog along x and mark two points) would.
- **Height:** the fitted z agrees across all five runs to 5 mm (−977 to −982), as it should
  with the same stand.
- **Absolute position:** the magnet at the mark fits at (5, −33) mm, not (0, 0). Either the
  mark is about 33 mm off the robot's (0, 0) in y, or there is a fixed offset in the system.
  The 3 Oct magnet-under scan also fitted at y ≈ −31 mm. Checking the mark with the probe
  (jog to (0, 0) at the lowest z and drop a plumb line) would separate the two.
- **Magnet depth:** about 280 mm below the bottom layer (z −700), deeper than the planned
  150 mm. The magnet sat 260 mm above the floor, so the fit puts the floor at about
  z −1240 in robot coordinates (−980 − 260). The floor run (`dipole_floor-y0`) fitted at
  z −1165 to −1270, which agrees within its large error.

### One fit per run (`fit_dipole.m`)

Fitting each run on its own gives positions about ±7 mm (1σ), but the moment direction
changes from run to run (10–28° from vertical, in different directions) even though the
magnet wasn't rotated. At this depth the moment's tilt and the magnet's position trade off,
so the single-run shifts come out 114 and 117 mm for the 100 mm y moves (14–17 mm off).
The joint fit removes that by sharing the moment, which is why it is the one to quote.

## Still to record

- **Floor height in robot coordinates**, to check the fitted z. Jog the probe to
  (0, 0, −780) and measure from the tip to the floor. A gap of about 460 mm (floor at −1240)
  means the fitted magnet height is right; any difference is the z error (plus any offset
  between the probe tip and the 1044's chip).
- **The magnet's size**, to work out its remanence (`fit_dipole(..., 'Volume', V)`).
