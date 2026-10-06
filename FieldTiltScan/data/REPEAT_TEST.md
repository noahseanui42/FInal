# Repeatability test (6 Oct 2026)

How repeatable is the whole system (robot positioning, the 1044, drift in the room)?
The magnet stays in one place and the same grid is scanned five times back to back.
Any difference between runs is the system, not the magnet.

## Setup

- Script: `field_scan_tilt.py --repeat 5`, `--correction hybrid`, coils off.
- Grid 3 × 7 × 3 = 63 points, 50 mm spacing across the full box: x −50/0/+50,
  y −150 to +150, z −700/−650/−600 (probe coordinates, mm). About 15 min per run,
  about 75 min for all five.
- 5 s settle, 20 readings per point, speed 2.
- Magnet on the stand at the mark (0, 0), as `dipole_y0`. **Don't touch the magnet,
  the stand or the robot base until all five runs are done.**
- Background: the same grid with the magnet removed, taken straight after the five runs.
  Only needed for the dipole fit (the run-to-run differences don't depend on it).

## Commands (repo root)

```
python FieldTiltScan/field_scan_tilt.py --label repeat50_corr-hybrid --magnet stand-y0 --repeat 5 \
       --correction hybrid --x -50 50 3 --y -150 150 7 --z -700 -600 3 \
       --note "repeatability: magnet on stand at mark (0,0), not touched between runs"

# then lift the magnet away (leave the stand) and:
python FieldTiltScan/field_scan_tilt.py --label repeat50_corr-hybrid --magnet none \
       --correction hybrid --x -50 50 3 --y -150 150 7 --z -700 -600 3 \
       --note "background for repeat50, magnet removed, stand left in place"

python FieldPlots/plot_repeat_runs.py "FieldTiltScan/data/repeat50_corr-hybrid_run*_stand-y0_*.csv" \
       --bg FieldTiltScan/data/repeat50_corr-hybrid_none_<time>.csv
```

Files come out as `repeat50_corr-hybrid_run1_stand-y0_<time>.csv` … `run5`, each with a
`.meta.json` holding `"repeat": {"run": k, "of": 5}`. Ctrl+C stops the current run and
does not start the rest.

In MATLAB, raw vs tilt-corrected repeatability:

```matlab
cd FieldTiltScan; addpath ../FieldPlots
C = compare_tilt_runs("data/repeat50_corr-hybrid_run*_stand-y0_*.csv", "data/repeat50_corr-hybrid_none_<time>.csv");
```

## Results

(to fill in from `figures/repeat50_corr-hybrid_repeat/summary.txt`)
