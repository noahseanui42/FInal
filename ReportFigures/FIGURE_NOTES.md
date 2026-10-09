# Report figures and notes

Twelve figures covering every test with data in this repo, in test order. Each one has a
note saying what the test was, what it was testing, how it was done, and what the figure
shows, plus a suggested caption. Every number below comes from the data files and is
printed when you run the script.

```
python -m pip install numpy pandas scipy matplotlib openpyxl
python ReportFigures/make_report_figures.py        # from the repo root; rewrites all 12 PNGs
```

The PNGs are 200 dpi and sized for an A4 text column. Fields are in gauss as logged
(1 mG = 0.1 µT; the background field in the lab is about 720 mG). "Magnet alone" always
means the scan minus a no-magnet scan of the same grid, point by point.

| # | File | Test | Date |
|---|---|---|---|
| 1 | `fig01_servo_protractor_sweep.png` | Servo calibration, assembled robot | 30 Sep |
| 2 | `fig02_arm2_ruler_sweep.png` | Servo calibration, arm 2 on its own | 29 Sep |
| 3 | `fig03_field_map_magnet_xpos.png` | First field map (magnet on the +x side) | 2 Oct |
| 4 | `fig04_full_box_magnet_under.png` | Full scan volume (magnet under the grid) | 3 Oct |
| 5 | `fig05_settle_time.png` | Settle time, 0.5 s vs 5 s | 2 Oct |
| 6 | `fig06_repeat_pairs_2oct.png` | Repeat scans; correction off vs hybrid | 2 Oct |
| 7 | `fig07_tilt_correction.png` | Probe tilt and tilt correction | 2 Oct |
| 8 | `fig08_dipole_field_maps.png` | Dipole known-position test: field maps | 4 Oct |
| 9 | `fig09_dipole_positions.png` | Dipole known-position test: fitted positions | 4 Oct |
| 10 | `fig10_repeat_drift.png` | Five-run repeatability: drift | 6 Oct |
| 11 | `fig11_repeat_sigma_pos.png` | Five-run repeatability: position repeatability | 6 Oct |
| 12 | `fig12_repeat_change_maps.png` | Five-run repeatability: change between runs | 6 Oct |

---

## Test A: Servo calibration (29–30 Sep)

### Figure 1: Assembled protractor sweep

**What the test was.** With all three arms connected, the robot was stepped straight up its
own axis from z = −730 to −590 mm in 10 mm steps, always moving up. At each step a digital
protractor on each bicep measured its actual angle, which was compared with the angle the
inverse kinematics commanded. Data: `DeltaAppCalibrated/tools/servo_sweep/sweep_2026-09-30_up.csv`.

**What was being tested.** Whether each servo turns to the angle it is told to. The firmware
turns an angle into a pulse width with two numbers per servo (`centre_us`, the pulse at 0°,
and `us_per_deg`). If those are wrong the arms disagree, the platform tilts and the probe ends
up in the wrong place. Near the bottom of the volume, 1° of bicep error moves the probe about
3 mm in z.

**What the figure shows.** (a) The error with the calibration that was flashed at the time.
It was large and grew with depth: at z = −730 mm, D9 was +7.2° off, D11 +4.9° and D10 −2.4°,
so the arms disagreed by nearly 10°. (b) What is left after fitting a straight line
(measured = s × commanded + o) to each arm. All three now sit within ±1.3° (D9 1.0°,
D10 1.2°, D11 0.5° at worst). The slopes were 1.203, 0.974 and 1.092, which gave the new
`us_per_deg` values (9.83, 9.77, 9.67 µs/°). They now agree with each other, which is
expected for three servos of the same model. D10 has the most scatter, which fits with the
~5 mm of play found in that arm.

**Caption.** *Bicep angle error for each arm during an on-axis sweep (30 Sep). (a) Measured
minus commanded angle with the original calibration; (b) residual after a straight-line refit
of each servo, which was used to update `config.h`.*

**Caveat.** This was the up pass only. The down pass (backlash) and repeat measurements in
`joint_angle_calibration_test.xlsx` haven't been filled in yet, so there is no figure for
them.

### Figure 2: Arm 2 (D10) ruler sweep

**What the test was.** Arm 2 was disconnected from its forearm rods and stepped through
1200–1950 µs in 10 µs steps (76 points). At each step the height of the bicep's corner was
measured with a ruler and converted to an angle (R = 185 mm from the shaft, shaft 100 mm
below the top plate). Data: `servo2_angles.xlsx`.

**What was being tested.** Whether that servo's angle is a straight line in pulse width, and
what its true `centre_us` and `us_per_deg` are. Arm 2 was suspected after the effector was
seen drifting sideways while it moved down.

**What the figure shows.** The servo is close to linear: the straight-line fit is
9.51 µs/° with θ = 0 at 1349 µs, and no point is more than 1.4° off it. The old values
(10.05 µs/°, centre 1385 µs) were up to 8° wrong. The residual (lower panel) curves gently
and has a step between 1690 and 1700 µs, which is the "possible hitch or misread" noted in
`CALIBRATION_LOG.md`.

**Caption.** *Arm 2 servo angle against pulse width, unloaded (29 Sep), with the
straight-line fit and the original `config.h` calibration. Lower panel: distance of each
point from the fit.*

---

## Test B: Field maps (2–3 Oct)

### Figure 3: First field map, magnet on the +x side

**What the test was.** A 5 × 5 × 3 grid (x, y ±50 mm, z −675/−650/−625 mm, 75 points) scanned
with a permanent magnet fixed on the +x side of the grid, coils off, hybrid position
correction, 5 s settle, 20 readings per point. The same grid was scanned with no magnet as the
background. Files: `FieldScan/data/magnet-xpos_corr-hybrid_run1_20261002_182828.csv` minus
`nomagnet_corr-off_run1_20261002_172221.csv`.

**What was being tested.** That the whole chain works: the robot reaches every point, the
1044 reads the field there, and the map shows a sensible field.

**What the figure shows.** All 75 points were reached. The magnet's field is 49–272 mG
(about 7–38 % of the 720 mG background). It is strongest at x = +50 on the bottom layer and
falls off away from the magnet and with height. The arrows (in-plane direction, length scaled
to the largest in each layer) point in −x across most of the grid, swinging towards ±y near the
y edges. This is the smooth dipole-like pattern expected from a magnet off to one side.

**Caption.** *Field of the magnet alone (scan minus no-magnet background) on three heights,
magnet on the +x side of the grid. Colour: |B|; arrows: direction of the in-plane (x-y)
component.*

### Figure 4: Full scan volume, magnet under the grid

**What the test was.** The full working box: x ±50 mm and y ±150 mm in 25 mm steps, at four
heights from z = −700 to −600 mm (5 × 13 × 4 = 260 points), with the magnet under the grid
pole-up, hybrid correction. Layer 1 and layers 2–4 were run separately (a move timeout on the
layer change, since fixed) and joined. Background: the no-magnet full-box scan from 4 Oct.
Files in `FieldTiltScan/data/full25-4z_*`.

**What was being tested.** That the robot can cover the whole validated box, and what the
field of a magnet below it looks like.

**What the figure shows.** All 260 points were reached. The magnet's field is 93–535 mG and
peaks on the bottom layer around (0, −30) mm. The in-plane arrows point outwards from that
spot on every layer, which is exactly the pattern of a vertical dipole below the grid. The
dipole test (Test E) puts the magnet at y ≈ −33 mm, the same offset. Two points on the
z = −667 mm layer are blank because the background scan has no reading there (the sensor
returned no samples).

**Caption.** *Field of the magnet alone over the full scan volume (260 points, four heights),
magnet under the grid. Arrows show the in-plane field direction, which radiates from the
point above the magnet.*

**Caveat.** The background was taken the next day. Any drift between the two days (see
Figure 10) is in the map as a small uniform offset.

---

## Test C: Settle time, 0.5 s vs 5 s (2 Oct)

### Figure 5

**What the test was.** The same 75-point grid, with the magnet in the same place on the −x
side, scanned twice with correction off: once waiting 0.5 s after each move before reading
and once waiting 5 s. Files: `magnet-xneg_corr-off_settle0p5s_run1_20261002_022713.csv` and
`magnet-xneg_corr-off_run1_20261002_024004.csv`.

**What was being tested.** Whether the arms are still swinging when a short wait ends, and so
whether the shorter (faster) scan gives the same field.

**What the figure shows.** (a) The two scans differ by 8.2 mG per point (median, up to
17 mG). Two scans with the same settings (the +x magnet pair, Test D) differ by only 2.9 mG,
so the 0.5 s scan really is different. Most of it (about 8 mG) is the same at every point, an
offset rather than a pattern. (b) The scatter within the 20 readings at a point is higher
after 0.5 s (median 1.58 mG, up to 4.2 mG) than after 5 s (1.28 mG, up to 2.3 mG). That fits
with the probe still moving at the 0.5 s points. The 5 s scan took 13.8 min, against 8.2 min.

**Caption.** *Effect of the settle time after each move. (a) Size of the field difference
between scans with 0.5 s and 5 s settle, against the difference between two identical scans;
(b) scatter of the 20 readings taken at each point.*

**Caveat.** The scans were 13 minutes apart, so some of the uniform offset could be drift
(Figure 10 shows about 3 mG per 14 min on 6 Oct). It's one pair of scans. The decision it
supports, using 5 s for every later scan, still holds.

---

## Test D: Repeat scans and the position correction (2 Oct)

### Figure 6

**What the test was.** Three setups, each scanned twice with nothing touched in between:
the +x magnet with correction off, the same magnet with the hybrid correction, and a stronger
magnet under the grid centre. As a comparison, the magnet under the centre was also taken away
and put back between scans. Files: `FieldScan/data/magnet-*`, background
`nomagnet_corr-off_run1_20261002_172221.csv`.

**What was being tested.** (1) How well the system repeats a scan. (2) Whether the hybrid
position correction, which aims each move slightly past the target to make up for the servos
giving way under load, makes repeatability any worse. (3) How much a small change in the
magnet's placement shows up, compared with that.

**How it is turned into a position.** σ_pos = σ_B / |∇B| at each point: the spread of |B|
between runs (with the sensor noise of about 0.2 mG removed) divided by how fast |B| changes
with position there. It is the probe movement that would explain the spread. This is the same
calculation as `FieldPlots/compare_runs.m`.

**What the figure shows.** (a) Repeat scans differ by 2.9 mG per point (median) with
correction off, 2.9 mG with hybrid and 4.8 mG with the stronger magnet. Taking the magnet
away and putting it back changes the field by 60 mG, more than 10 times as much. The system
can easily see a re-placed magnet. (b) As a position, repeatability is 1.2 mm (off) and
1.0 mm (hybrid) median, so the correction doesn't harm repeatability. It is 0.3 mm with the
stronger magnet, because its steeper gradient (4.75 against about 1.1 mG/mm) makes the
same field change worth less movement.

**Caption.** *Two scans of the same setup. (a) Field difference per point (log scale) for
three repeated setups and for a magnet removed and replaced; (b) the repeated setups expressed
as position repeatability σ_B / |∇B|. Bars mark the medians.*

**Caveat.** The hybrid correction is for accuracy (where the probe lands), not
repeatability. Its accuracy (corner error 19 → 2.3 mm rms) was measured with the
pen-and-ruler tests, which are recorded in the separate report repo, not here.

---

## Test E: Probe tilt and tilt correction (2 Oct, 22:33)

### Figure 7

**What the test was.** The 75-point grid with the magnet under the grid and hybrid
correction, scanned with `field_scan_tilt.py`, which also logs the 1044's accelerometer and
gyro at every point. From the accelerometer, `tilt_correct.m` works out how far the probe is
tilted at each point relative to the grid centre and rotates the measured field back to that
orientation. Files: `FieldTiltScan/data/magnet_tilt_20261002_223300*.csv`.

**What was being tested.** Whether the probe tilts as the robot moves around the grid (a
delta robot's platform is meant to stay level), and whether that tilt matters for the field.
A tilted sensor measures a rotated field even if the field itself hasn't changed.

**What the figure shows.** (Top) The probe is tilted 0.87° from its orientation at the grid
centre (median), up to 1.9°. The tilt is largest at the −x, −y corner and similar on all three
heights, so it is set by the x-y position. (Bottom) Correcting for it changes the field by
16 mG (median), up to 42 mG (3.3 % of |B| at most). That is 5–10 times the repeatability in
Figure 6, so tilt is the larger error and is worth correcting. The correction only rotates the
field, so |B| itself is unchanged. The gyro read 0.30 °/s rms during the readings, so the
probe was still.

**Caption.** *Probe tilt relative to the grid centre at each point (top) and the resulting
change in the field when the tilt is corrected (bottom), on three heights.*

---

## Test F: Dipole known-position test (4 Oct)

### Figures 8 and 9

**What the test was.** A magnet on a stand under the grid was scanned (42 points: x −50/0/+50,
y −150 to +150 in 50 mm steps, z −700 and −600 mm), then moved by a measured amount with a
ruler and scanned again: +100 and −100 mm in y, −50 and +50 mm in x, five positions in all.
Background: the no-magnet full-box scan from the same day. A magnetic dipole model was fitted
to all five scans together: one magnetic moment shared by all runs (the magnet was never
rotated) and one position per run (`FieldPlots/fit_dipole_joint.py`). Files:
`FieldTiltScan/data/dipole_*.csv`; details in `DIPOLE_TEST.md`.

**What was being tested.** The accuracy of the whole system end to end (robot positions, the
sensor and the analysis), against something measured independently. If the system is
accurate, the fitted magnet should move by the same amount as the ruler. Shifts are used
rather than absolute positions because they don't depend on how well the floor mark lines up
with the robot's (0, 0).

**What Figure 8 shows.** The magnet's field on the bottom layer for each position: the bright
spot follows the magnet. The fitted positions (×) land close to the ruler positions (○). The
ruler positions are drawn relative to the fitted y0 position.

**What Figure 9 shows.** (a) Top view of all five fitted positions with their 1σ error bars,
against the ruler. (b) The error in each move. Moves along y are within 1.3 mm of the ruler
over 100 and 200 mm (+1.0, +0.3, +1.3 mm). Moves along x are worse (−10.1, +5.8 and −4.4 mm),
but their uncertainty is larger too (±5.5 mm), because the grid is only 100 mm wide in x
against 300 mm in y. They are within 1–2σ. The fit itself is good: one moment of 2.71 A·m²,
7.8° from vertical, with a residual of 12.5 mG rms over 210 points. All five fitted heights
agree within 5 mm (−977 to −982 mm), as they should, since the stand height never changed.

**Captions.**
*Figure 8: Field of the magnet alone on the bottom layer (z = −700 mm) for the five magnet
positions, with the fitted (×) and ruler (○) positions.*
*Figure 9: (a) Fitted magnet positions (±1σ) and ruler positions, top view; (b) fitted minus
ruler length for each move along y (blue) and x (orange).*

**Caveats.** The magnet at the floor mark fits at (5, −33) mm, not (0, 0): either the mark
is off the robot's axis or there is a fixed offset in the system. This test can't tell which.
Both sets of moves come out turned 3–6° clockwise seen from above, which points to the ruler's
axes on the floor (or the sensor in its holder) being turned about 4° from the robot's axes.
A wider x grid (it can go to ±150 mm) would tighten the x results.

---

## Test G: Five-run repeatability (6 Oct)

Five back-to-back scans of 70 points (x ±50 mm in 25 mm steps, y ±150 mm in 50 mm steps,
z −700 and −600 mm) with a magnet fixed under the grid and nothing touched, 18:05 to 19:18,
then one scan with the magnet removed. Hybrid correction, 5 s settle, 20 readings per point,
about 14 min per run. Files: `FieldTiltScan/data/repeat_*.csv`; details in `REPEAT_TEST.md`.

**What was being tested.** How repeatable the system is over more than two runs, and whether
anything drifts over an hour of scanning.

### Figure 10: Drift

**What the figure shows.** (a) Averaged over all 70 points, each run reads a little higher in
Bx and lower in By than the one before, steadily. By run 5 the field has moved 10.6 mG from
run 1. The change is the same at every point, so it's an offset drift, not the magnet or the
robot moving. (b) Over the same hour the probe's mean tilt creeps by about +0.12° in pitch and
+0.06° in roll, likely the printed parts and servos warming up. Rotating the field by that
tilt only accounts for about 17 % of the drift. The rest is most likely the sensor's offset or
the servo motors' magnets changing as they warm up.

**Caption.** *Drift over five back-to-back scans. (a) Mean change in each field component
(and its size) relative to run 1; (b) mean change in the probe's pitch and roll, including the
no-magnet scan that followed.*

**Why it matters.** At the median gradient of 1.16 mG/mm, 11 mG is worth about 9 mm of
apparent position. So the no-magnet reference has to be taken close in time to the scan, the
rig should warm up first, or a per-run offset has to be fitted.

### Figure 11: Position repeatability

**What the figure shows.** σ_pos = σ_B / |∇B| at each point over the five runs (as in
Figure 6). Median 2.1 mm, 75th percentile 2.8 mm, 95th percentile 4.9 mm; the run-to-run
spread of |B| is 2.0 mG median, about 10 times the 0.2 mG sensor noise. So the spread comes
from the system (positioning, settling, drift), not from the sensor. This agrees with the
2–2.5 mm repeatability found in the pen-and-ruler tests. The worst point (7.9 mm) is on the top layer
at y = +100, where the magnet's field is weak and flat, so a small field change is worth a lot of
movement.

**Caption.** *Position repeatability σ_B / |∇B| over five runs: map on each height (left)
and distribution over all 70 points (right).*

**Note.** This includes the drift in Figure 10. `REPEAT_TEST.md` gives 1.7 mm median once
a uniform offset per run is removed.

### Figure 12: Change between consecutive runs

**What the figure shows.** The percentage change in the magnet's |B| at each point from one
run to the next (each run minus the no-magnet scan). The mean change is 1.5–1.9 % per pair; the
largest single point is 9.2 %. In every pair the largest change is on the top layer
(z = −600 mm). The magnet's field there is less than half as strong as on the bottom layer
(88 against 192 mG on average), so the same change in mG is a bigger percentage. Runs 1→2 and 2→3 are mostly red (rising) on the bottom layer and run 4→5 is
mostly blue (falling) on the top layer, which is the drift in Figure 10 showing through.

**Caption.** *Percentage change in the magnet's field |B| between consecutive runs, on the
two heights. Red: field higher in the later run; blue: lower.*

---

## What isn't plotted

- `FieldScan/data/checks/` and `FieldTiltScan/data/checks/`: simulated, aborted and
  two-point check runs, not test data.
- `dipole_floor-y0`: the first dipole attempt with the magnet on the floor. It was too far away
  to locate, and `DIPOLE_TEST.md` excludes it from the results.
- `magnet-xpos-close_corr-off_run1`: a single scan with the magnet moved in close, which has no
  partner to compare with.
- The calibration sheets `servo_calibration_sheet.xlsx` and
  `joint_angle_calibration_test.xlsx`: their data cells are still empty templates.
