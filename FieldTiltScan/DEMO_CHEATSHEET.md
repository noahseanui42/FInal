# Demo cheat sheet

Terminal commands for the live robot demo. Run them from the repo folder; close the
delta app before any scan (only one program can use the Arduino's port).

## Get the latest files

```
cd /Users/rochelle/FInal
git fetch origin claude/upbeat-planck-83lcp0
git checkout origin/claude/upbeat-planck-83lcp0 -- FieldTiltScan/demo_plots.m FieldPlots/compare_heatmaps.m
```

## Before the examiner arrives

Check the Arduino's port (the scan expects `/dev/cu.usbmodem14101`; if yours differs,
add `--port /dev/cu.usbmodemXXXX` to the scan commands):

```
ls /dev/cu.usbmodem*
```

Clear out old test scans so the demo plots the right ones:

```
rm /Users/rochelle/FInal/FieldTiltScan/data/demo_live_* /Users/rochelle/FInal/FieldTiltScan/data/demo_rep*
```

## Move the robot by hand (delta app)

```
cd /Users/rochelle/FInal
python DeltaAppCalibrated/delta_app/main.py
```

Connect → Online → support the arms, servo power on → Enable → speed 10 % → Home → jog.
Close it before scanning.

## Live scan (section 5)

About 2 min, 9 points:

```
cd /Users/rochelle/FInal
python FieldTiltScan/field_scan_tilt.py --label demo_live --correction hybrid --x -50 50 3 --y -50 50 3 --z -650 -650 1
```

Other sizes (swap in for the `--x --y --z` part; keep `--label demo_live`):

| Size | Grid options | Points | Time |
|---|---|---|---|
| Quickest | `--x -50 50 2 --y -50 50 2 --z -650 -650 1` | 4 | ~1 min |
| Small (demo) | `--x -50 50 3 --y -50 50 3 --z -650 -650 1` | 9 | ~2 min |
| Medium | `--x -50 50 3 --y -100 100 5 --z -650 -650 1` | 15 | ~3–4 min |
| Two layers | `--x -50 50 3 --y -50 50 3 --z -700 -600 2` | 18 | ~4 min |
| Large | `--x -50 50 5 --y -100 100 5 --z -700 -600 2` | 50 | ~11 min |

## Live repeatability, two runs back to back (section 5b)

Magnet in place and not touched between runs; about 4 min. Labels must be exactly
`demo_rep1` and `demo_rep2`:

```
cd /Users/rochelle/FInal
python FieldTiltScan/field_scan_tilt.py --label demo_rep1 --correction hybrid --x -50 50 3 --y -50 50 3 --z -650 -650 1 && python FieldTiltScan/field_scan_tilt.py --label demo_rep2 --correction hybrid --x -50 50 3 --y -50 50 3 --z -650 -650 1
```

Check both scans saved:

```
ls /Users/rochelle/FInal/FieldTiltScan/data/demo_rep*
```

## Dry run without hardware

```
cd /Users/rochelle/FInal
python FieldTiltScan/field_scan_tilt.py --simulate --label demo_test
rm /Users/rochelle/FInal/FieldTiltScan/data/demo_test_*
```

## During a scan

- It parks at (0, 0, −650) and zeroes the gyro: keep the table still.
- Ctrl+C stops it and keeps the points so far.
- The robot stays enabled at the end, because disabling drops the arms.
