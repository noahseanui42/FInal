function D = repeatability_heatmaps(varargin)
% repeatability_heatmaps — % difference in the |B| heat map between repeated scans of
% the same setup (the 2 Oct repeatability runs, FieldScan/data/INDEX.md).
%
%   repeatability_heatmaps()                   % the three repeat pairs below
%   repeatability_heatmaps("Save", true)       % also save repeatability.png and
%                                              % repeatability_summary.png in FieldScan/data
%   D = repeatability_heatmaps("Plot", false)  % numbers only
%   repeatability_heatmaps("Pairs", [1 3; 3 2; 2 4])   % time order: off1, hyb1, off2, hyb2
%
% Takes every option of compare_heatmaps ("Labels", "Floor", "CLim", "R", "Pairs"...).
%
% Every run minus the no-magnet background (nomagnet_corr-off_run1), so |B| is the
% magnet's field only, then for each pair at every grid point:
%
%   difference (%) = 100 * (|B| of the repeat - |B| of the first run) / |B| of the first run
%
% Runs (all on the 5 x 5 x 3 grid, x, y +-50, z -675/-650/-625):
%   1  magnet-xpos_corr-off_run1               magnet fixed on the +x side, correction off
%   2  magnet-xpos_corr-off_run2               ... repeat
%   3  magnet-xpos_corr-hybrid_run1            same magnet, hybrid correction
%   4  magnet-xpos_corr-hybrid_run2            ... repeat
%   5  magnet-under-replaced_corr-hybrid_run1  magnet under the centre (taken away, put back)
%   6  magnet-under-replaced_corr-hybrid_run2  ... back-to-back repeat
%
% Default pairs: 1 -> 2 (off repeat), 3 -> 4 (hybrid repeat), 5 -> 6 (under repeat).
% With nothing changed between the two runs of a pair, the map should be white
% (0 %); what's left is the scan's repeatability.

dataDir = fullfile(fileparts(mfilename("fullpath")), "..", "FieldScan", "data");
files = fullfile(dataDir, {'magnet-xpos_corr-off_run1_20261002_180000.csv'
                           'magnet-xpos_corr-off_run2_20261002_184415.csv'
                           'magnet-xpos_corr-hybrid_run1_20261002_182828.csv'
                           'magnet-xpos_corr-hybrid_run2_20261002_185818.csv'
                           'magnet-under-replaced_corr-hybrid_run1_20261002_212800.csv'
                           'magnet-under-replaced_corr-hybrid_run2_20261002_214238.csv'});
bg = fullfile(dataDir, "nomagnet_corr-off_run1_20261002_172221.csv");

D = compare_heatmaps(files, bg, "Pairs", [1 2; 3 4; 5 6], "Title", "Repeatability", ...
    "Name", "repeatability", varargin{:});
end
