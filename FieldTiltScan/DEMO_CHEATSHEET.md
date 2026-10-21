# Demo cheat sheet

Every command in `demo_plots.m`, section by section. Click inside a section and press
Cmd+Enter to run just that one; run section 0 first.

## Before the demo

Terminal:

```
cd /Users/rochelle/FInal
git fetch origin claude/upbeat-planck-83lcp0
git checkout origin/claude/upbeat-planck-83lcp0 -- FieldTiltScan/demo_plots.m FieldPlots/compare_heatmaps.m
```

MATLAB:

```matlab
clear functions
cd /Users/rochelle/FInal/FieldTiltScan
edit demo_plots.m
```

## 0. Setup

```matlab
assert(isfile("scan_config.m") && isfolder("data"), "cd into FieldTiltScan first");
addpath("../FieldPlots")
close all
full = "data/full25-4z_corr-hybrid_under_combined_20261003.csv";
bg   = "data/full25-4z_corr-hybrid_none_20261004_155505.csv";
```

## 1. Full-volume field map (heat map + 3D map)

```matlab
close all
plot_field_layers(full, bg, "Figures", {"heat","3d"}, "TiltCorrect", true, "Labels", false)
```

## 1b. Field direction and side views (if asked)

```matlab
close all
plot_field_layers(full, bg, "Figures", {"direction","side"}, "TiltCorrect", true)
```

## 1c. 3D arrows, length = field strength (if asked)

```matlab
close all
plot_field_arrows3d(full, bg, "TiltCorrect", true)
```

## 2. Probe tilt, then the tilt-correction change

```matlab
close all
plot_tilt(full);
figure("Name", "Tilt correction change");
image(imread("figures/magnet_tilt_20261002_223300/correction_change.png")); axis image off
```

## 3. Repeatability: 5 runs, change between runs in mG

```matlab
close all
compare_repeat_heatmaps("Units", "mG", "Labels", false);
```

## 3b. Every run against run 1, the drift (if asked)

```matlab
close all
repeatability_heatmaps("Pairs", [1 2; 1 3; 1 4; 1 5]);
```

## 3c. Position repeatability (mm) per layer (if asked)

```matlab
close all
R = compare_runs("data/repeat_under-run*.csv", "data/repeat_none_20261006_192127.csv", "Plot", false);
plot_repeatability_layers(R, "Title", "5 runs, magnet fixed")
```

## 4. Dipole accuracy (saved joint-fit figure)

```matlab
close all
figure("Name", "Dipole joint fit");
image(imread("data/dipole_joint_fit.png")); axis image off
```

## 5. Live scan

First, in Terminal (delta app closed), about 2 min:

```
cd /Users/rochelle/FInal
python FieldTiltScan/field_scan_tilt.py --label demo_live --correction hybrid --x -50 50 3 --y -50 50 3 --z -650 -650 1
```

Then in MATLAB:

```matlab
close all
d = dir("data/demo_live_*.csv");
assert(~isempty(d), "No demo_live scan in data/ yet");
[~, i] = max([d.datenum]);
live = fullfile(d(i).folder, d(i).name);
plot_field_layers(live, "", "Figures", "heat")
plot_tilt(live);
```

Other scan sizes (swap in for the `--x --y --z` part; keep `--label demo_live`):

| Size | Grid options | Points | Time |
|---|---|---|---|
| Quickest | `--x -50 50 2 --y -50 50 2 --z -650 -650 1` | 4 | ~1 min |
| Small (demo) | `--x -50 50 3 --y -50 50 3 --z -650 -650 1` | 9 | ~2 min |
| Medium | `--x -50 50 3 --y -100 100 5 --z -650 -650 1` | 15 | ~3–4 min |
| Two layers | `--x -50 50 3 --y -50 50 3 --z -700 -600 2` | 18 | ~4 min |
| Large | `--x -50 50 5 --y -100 100 5 --z -700 -600 2` | 50 | ~11 min |

## 5b. Live repeatability: two runs back to back

First, in Terminal, magnet in place and not touched between runs, about 4 min. Labels
must be exactly `demo_rep1` and `demo_rep2`:

```
cd /Users/rochelle/FInal
python FieldTiltScan/field_scan_tilt.py --label demo_rep1 --correction hybrid --x -50 50 3 --y -50 50 3 --z -650 -650 1 && python FieldTiltScan/field_scan_tilt.py --label demo_rep2 --correction hybrid --x -50 50 3 --y -50 50 3 --z -650 -650 1
```

Check both files are there: `ls /Users/rochelle/FInal/FieldTiltScan/data/demo_rep*`

Then in MATLAB:

```matlab
close all
d1 = dir("data/demo_rep1_*.csv"); d2 = dir("data/demo_rep2_*.csv");
assert(~isempty(d1) && ~isempty(d2), "Need a demo_rep1 and a demo_rep2 scan in data/");
[~, i] = max([d1.datenum]); [~, j] = max([d2.datenum]);
runs = {fullfile(d1(i).folder, d1(i).name), fullfile(d2(j).folder, d2(j).name)}
plot_field_layers(runs{1}, "", "Figures", "heat")   % run 1
plot_field_layers(runs{2}, "", "Figures", "heat")   % run 2
compare_heatmaps(runs, "", "Units", "mG", "Title", "Live repeatability");   % run 2 - run 1
```
