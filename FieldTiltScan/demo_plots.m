% demo_plots — the artefact demo, one section per plot (see DEMO_CHEATSHEET.md).
% Open this file, cd into FieldTiltScan, click in a section and press Ctrl+Enter
% (Cmd+Enter on a Mac) to run just that section.

%% 0. Setup
assert(isfile("scan_config.m") && isfolder("data"), "cd into FieldTiltScan first");
addpath("../FieldPlots")
close all
full = "data/full25-4z_corr-hybrid_under_combined_20261003.csv";
bg   = "data/full25-4z_corr-hybrid_none_20261004_155505.csv";

%% 1. Full-volume field map: magnet only, 260 points, 4 layers (rotate the 3D figure)
close all
plot_field_layers(full, bg, "Figures", {"heat","3d"}, "TiltCorrect", true, "Labels", false)

%% 1b. If asked: field direction and side views
close all
plot_field_layers(full, bg, "Figures", {"direction","side"}, "TiltCorrect", true)

%% 1c. If asked: 3D arrows, length = field strength
close all
plot_field_arrows3d(full, bg, "TiltCorrect", true)

%% 2. Probe tilt per point (show figure 1), then what the tilt correction changes
close all
plot_tilt(full);
figure("Name", "Tilt correction change");
image(imread("figures/magnet_tilt_20261002_223300/correction_change.png")); axis image off

%% 3. Repeatability: 5 runs with the magnet fixed, change between runs in mG
close all
compare_repeat_heatmaps("Units", "mG", "Labels", false);

%% 3b. If asked: every run against run 1 (the drift)
close all
repeatability_heatmaps("Pairs", [1 2; 1 3; 1 4; 1 5]);

%% 3c. If asked: position repeatability (mm) per layer
close all
R = compare_runs("data/repeat_under-run*.csv", "data/repeat_none_20261006_192127.csv", "Plot", false);
plot_repeatability_layers(R, "Title", "5 runs, magnet fixed")

%% 4. Dipole accuracy: the saved joint-fit figure
close all
figure("Name", "Dipole joint fit");
image(imread("data/dipole_joint_fit.png")); axis image off

%% 5. Optional: plot the newest live scan
% First, in a terminal from the repo root, with the delta app closed:
%   python FieldTiltScan/field_scan_tilt.py --label demo_live --correction hybrid --x -50 50 3 --y -50 50 3 --z -650 -650 1
close all
d = dir("data/demo_live_*.csv");
assert(~isempty(d), "No demo_live scan in data/ yet");
[~, i] = max([d.datenum]);
live = fullfile(d(i).folder, d(i).name);
plot_field_layers(live, "", "Figures", "heat")
plot_tilt(live);

%% 5b. Live repeatability: two scans back to back, magnet fixed
% First, in a terminal from the repo root, magnet in place and not touched between runs:
%   python FieldTiltScan/field_scan_tilt.py --label demo_rep1 --correction hybrid --x -50 50 3 --y -50 50 3 --z -650 -650 1 && python FieldTiltScan/field_scan_tilt.py --label demo_rep2 --correction hybrid --x -50 50 3 --y -50 50 3 --z -650 -650 1
close all
d1 = dir("data/demo_rep1_*.csv"); d2 = dir("data/demo_rep2_*.csv");
assert(~isempty(d1) && ~isempty(d2), "Need a demo_rep1 and a demo_rep2 scan in data/");
[~, i] = max([d1.datenum]); [~, j] = max([d2.datenum]);
runs = {fullfile(d1(i).folder, d1(i).name), fullfile(d2(j).folder, d2(j).name)}
plot_field_layers(runs{1}, "", "Figures", "heat")   % run 1
plot_field_layers(runs{2}, "", "Figures", "heat")   % run 2
compare_heatmaps(runs, "", "Units", "mG", "Title", "Live repeatability");   % run 2 - run 1
