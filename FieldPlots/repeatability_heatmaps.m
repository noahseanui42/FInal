function D = repeatability_heatmaps(varargin)
% repeatability_heatmaps — % difference in the |B| heat map between repeated scans of
% the same setup.
%
%   repeatability_heatmaps()                   % 6 Oct: the five repeat runs, 1->2 ... 4->5
%   repeatability_heatmaps("2oct")             % 2 Oct: off, hybrid and magnet-under pairs
%   repeatability_heatmaps("Save", true)       % also save repeatability.png and
%                                              % repeatability_summary.png next to the data
%   D = repeatability_heatmaps("Plot", false)  % numbers only
%   repeatability_heatmaps("Pairs", [1 2; 1 3; 1 4; 1 5])   % every run against run 1
%
% Takes every option of compare_heatmaps ("Labels", "Floor", "CLim", "R", "Pairs"...).
%
% Every run minus the no-magnet scan, so |B| is the magnet's field only, then for each
% pair at every grid point:
%
%   difference (%) = 100 * (|B| of the later run - |B| of the earlier) / |B| of the earlier
%
% 6 Oct (FieldTiltScan/data/REPEAT_TEST.md): magnet fixed under the grid, five scans back
% to back (5 x 7 x 2 grid), background repeat_none. Default pairs 1->2, 2->3, 3->4, 4->5.
%
% 2 Oct (FieldScan/data/INDEX.md), 5 x 5 x 3 grid, background nomagnet_corr-off_run1:
%   1  magnet-xpos_corr-off_run1               magnet fixed on the +x side, correction off
%   2  magnet-xpos_corr-off_run2               ... repeat
%   3  magnet-xpos_corr-hybrid_run1            same magnet, hybrid correction
%   4  magnet-xpos_corr-hybrid_run2            ... repeat
%   5  magnet-under-replaced_corr-hybrid_run1  magnet under the centre (taken away, put back)
%   6  magnet-under-replaced_corr-hybrid_run2  ... back-to-back repeat
% Default pairs 1->2 (off repeat), 3->4 (hybrid repeat), 5->6 (under repeat).
%
% With nothing changed between two runs the map should be white (0 %); what's left
% is the scan's repeatability (plus any drift between the runs).

scanSet = '6oct';
if ~isempty(varargin) && any(strcmpi(varargin{1}, {'6oct', '2oct'}))
    scanSet = lower(char(varargin{1}));
    varargin(1) = [];
end
root = fullfile(fileparts(mfilename("fullpath")), "..");

if strcmp(scanSet, '2oct')
    dataDir = fullfile(root, "FieldScan", "data");
    files = fullfile(dataDir, {'magnet-xpos_corr-off_run1_20261002_180000.csv'
                               'magnet-xpos_corr-off_run2_20261002_184415.csv'
                               'magnet-xpos_corr-hybrid_run1_20261002_182828.csv'
                               'magnet-xpos_corr-hybrid_run2_20261002_185818.csv'
                               'magnet-under-replaced_corr-hybrid_run1_20261002_212800.csv'
                               'magnet-under-replaced_corr-hybrid_run2_20261002_214238.csv'});
    bg = fullfile(dataDir, "nomagnet_corr-off_run1_20261002_172221.csv");
    pairs = [1 2; 3 4; 5 6];
else
    dataDir = fullfile(root, "FieldTiltScan", "data");
    files = fullfile(dataDir, {'repeat_under-run1_20261006_180203.csv'
                               'repeat_under-run2_20261006_181927.csv'
                               'repeat_under-run3_20261006_183402.csv'
                               'repeat_under-run4_20261006_184837.csv'
                               'repeat_under-run5_20261006_190323.csv'});
    bg = fullfile(dataDir, "repeat_none_20261006_192127.csv");
    pairs = [];
end

D = compare_heatmaps(files, bg, "Pairs", pairs, "Title", "Repeatability", ...
    "Name", "repeatability", varargin{:});
end
