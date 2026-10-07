# Comparing heat maps between runs

How to use the MATLAB scripts that compare the |B| heat map from one scan to the next,
in percent or in milligauss (mG).

| Script | Use it for |
|---|---|
| `compare_repeat_heatmaps.m` | The 6 Oct repeatability test: five runs with the magnet fixed (`repeat_under-run1` … `run5`) and the no-magnet run (`repeat_none`). Finds the files itself. |
| `compare_heatmaps.m` | Any runs you choose, picked in a file dialog or typed in. |
| `repeatability_heatmaps.m` | Shortcut for the repeat runs kept in this repo (6 Oct, or the 2 Oct pairs). |

`compare_repeat_heatmaps.m` and `compare_heatmaps.m` each work on their own: copy the one
`.m` file anywhere, no other scripts needed.

## Setup

1. Get the scripts, either by pulling `main` (`git pull`) or by downloading the `.m` file
   from GitHub (open it, then the **Download raw file** button). Save it as `.m`, not
   `.m.txt`.
2. In MATLAB, go to the folder the `.m` file is in, using the **Current Folder** panel
   or `cd`:
   ```matlab
   cd 'C:\path\to\FInal\FieldTiltScan\data'
   ```
   Or add its folder to the path: `addpath('C:\path\to\FInal\FieldPlots')`.

## The repeatability test: `compare_repeat_heatmaps`

Type in the Command Window:

```matlab
compare_repeat_heatmaps()                  % change in percent
compare_repeat_heatmaps("Units", "mG")     % change in milligauss
```

It looks for `repeat_under-run*.csv` and `repeat_none_*.csv` in these places, in order:
MATLAB's current folder, the script's own folder, its `data` subfolder, and
`../FieldTiltScan/data`. If it can't find them, a window opens: pick the folder that holds
the CSVs. You can also give the folder:

```matlab
compare_repeat_heatmaps('C:\path\to\data')
compare_repeat_heatmaps('C:\path\to\data', "Units", "mG")
```

The no-magnet run is the reference. It is subtracted from every run point by point, which
removes the Earth's field and the robot's own field and leaves only the magnet. Runs are
compared 1 → 2, 2 → 3, 3 → 4, 4 → 5.

### Options

Add any of these inside the brackets, in any order:

| Option | What it does |
|---|---|
| `"Units", "mG"` | Show the change in milligauss instead of percent. Leave it out for percent. |
| `"Save", true` | Also save the figures as PNGs next to the CSVs. |
| `"Labels", false` | Don't print the values on the maps. |
| `"Plot", false` | Table only, no figures. |

Example with several: `compare_repeat_heatmaps("Units", "mG", "Save", true)`.

### What you get

- **Figure 1, heat maps:** the no-magnet reference (raw field, its own colour scale), then
  runs 1–5 (magnet only, one shared scale). One row per z layer.
- **Figure 2, change maps:** run 1 → 2 … 4 → 5, in % or mG. Red means the field got
  stronger in the later run, blue weaker, white no change. Values are labelled to 1 decimal
  place.
- **Figure 3, summary:** bar chart per pair of runs.
- **Table in the Command Window:**

| Column | Meaning |
|---|---|
| `mean` | Average change (+ stronger, − weaker). Increases and decreases cancel, so it can be near 0 even when the maps differ. |
| `mean\|%\|` or `mean\|mG\|` | Average size of the change. The best single number for how different two runs are. |
| `med\|%\|` or `med\|mG\|` | Median size of the change. |
| `largest`, `at (x, y, z) mm` | The biggest change and where it was. |
| `total` (%) | Change in \|B\| summed over the whole grid. |
| `rms` (mG) | Root-mean-square change over the grid. |

With `"Save", true` the files are `repeat_heatmaps.png`, `repeat_change.png` and
`repeat_change_summary.png`. In mG the change figures are `repeat_change_mG.png` and
`repeat_change_mG_summary.png`, so they don't overwrite the percent ones.

## Any runs: `compare_heatmaps`

```matlab
compare_heatmaps()                    % percent
compare_heatmaps("Units", "mG")       % milligauss
```

Two windows open:

1. **Pick the runs.** Ctrl+click to pick several, or click the first and Shift+click the
   last, then **Open**. They are sorted by the time stamp in their names
   (`..._YYYYMMDD_HHMMSS.csv`), so they are compared in the order they were taken.
2. **Pick the background** (the no-magnet scan) to subtract from every run, or click
   **Cancel** to compare the raw field.

Or type the files instead of picking them:

```matlab
% every file matching a pattern, sorted by time stamp, minus a background
compare_heatmaps("repeat_under-run*.csv", "repeat_none_20261006_192127.csv")

% your own list, compared in the order given
compare_heatmaps({'C:\scans\run1.csv', 'C:\scans\run2.csv', 'C:\scans\run3.csv'}, 'C:\scans\background.csv')

% raw field, no background
compare_heatmaps({'run1.csv', 'run2.csv'}, "")
```

File names can be full paths, or just names if MATLAB is in the folder with the CSVs.

### Options

All the options of `compare_repeat_heatmaps`, plus:

| Option | What it does |
|---|---|
| `"Pairs", [1 2; 1 3; 1 4; 1 5]` | Compare these runs instead of 1 → 2, 2 → 3, …. Each row is [earlier later]; this example compares every run with run 1. |
| `"CLim", 10` | Fix the colour scale at −10 … +10 (in % or mG). |
| `"Floor", 0.02` | Percent only: leave out points where the earlier run's \|B\| is below 0.02 G, where the % blows up. |
| `"Title", "My test"` | Text added to the start of the figure titles. |
| `"Name", "mytest"` | File names with `"Save", true` (default `heatmap_change`; `_mG` is added in mG). |
| `"TiltCorrect", true` | Remove the probe's tilt first. Needs scans with accelerometer columns, and `apply_tilt.m` and `tilt_correct.m` on the path. |

Example: `compare_heatmaps("Units", "mG", "Pairs", [1 2; 1 3; 1 4; 1 5], "Save", true)`.

## The repo's repeat runs: `repeatability_heatmaps`

Run from a clone of the repo (it uses the CSVs in `FieldTiltScan/data` and `FieldScan/data`):

```matlab
repeatability_heatmaps()                   % 6 Oct: the five repeat runs
repeatability_heatmaps("2oct")             % 2 Oct: correction off, hybrid and magnet-under pairs
repeatability_heatmaps("Units", "mG")      % takes every compare_heatmaps option
```

## Zooming in

Click any map (in either script) to open it on its own in a big window, with larger
labels and zoom switched on:

- **Click** to zoom in, **Shift+click** to zoom out, **double-click** to go back.
- Scroll the mouse wheel or trackpad to zoom in and out.
- The window can be resized or made full screen.

To click another map afterwards, go back to the original figure. If zoom or pan is
switched on there, turn it off first (click the magnifier icon again), or clicks won't
open the zoom window.

You can also zoom the original figures directly: hover over a map and use the magnifier
and hand icons that appear at its top-right corner.

## Percent or mG?

- **Percent** is the change relative to the field at that point. With the no-magnet run
  subtracted, that's relative to the magnet's field only.
- **mG** is the change itself (1 mG = 0.1 µT), the same size wherever the field is weak
  or strong.

The same change is a bigger percentage where the field is weak. In the 6 Oct test the
magnet's field is about 0.09 G on the top layer (z −600) and about 0.2 G on the bottom
layer (z −700). So a ~2 mG wobble shows as about 2–3 % on top and under 1 % at the bottom.
In mG both layers change by about the same amount.

Subtracting the no-magnet run makes the percentages bigger, but not the change itself. The
same reference is taken off both runs, so it cancels:
(run 2 − ref) − (run 1 − ref) = run 2 − run 1. Without it, the ~0.7 G of Earth's field and
robot field sits in the denominator and makes the % look about 7× smaller.

For a report, quote the change in mG (or µT), and give the % with the background
subtracted, stating that it's relative to the magnet's field.

## Troubleshooting

| Message | Fix |
|---|---|
| `Undefined function 'compare_heatmaps'` (or `compare_repeat_heatmaps`) | MATLAB can't see the `.m` file. Go to its folder in the Current Folder panel, or `addpath` its folder. Check it isn't saved as `.m.txt`. |
| `No files match ... in <folder>` | MATLAB is in a different folder from the CSVs. Go to the CSV folder, give full paths, or run `compare_heatmaps()` to pick the files. |
| `No repeat_under-run*.csv and repeat_none_*.csv files in ...` | The folder you picked doesn't hold the repeat files, or they've been renamed. |
| `"Units" must be "%" or "mG"` | Typo in the unit. Use `"mG"` or `"%"`. |
| `Undefined function 'apply_tilt'` | Only with `"TiltCorrect", true`: put `apply_tilt.m` and `tilt_correct.m` from `FieldPlots` on the path too. |
| Odd values | If a CSV was opened and saved in Excel, it may have been reformatted. Use the original file. |
