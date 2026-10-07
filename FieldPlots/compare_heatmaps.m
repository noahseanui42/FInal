function D = compare_heatmaps(files, baselineFile, varargin)
% compare_heatmaps — percentage change in the |B| heat map from one run to the next.
%
%   compare_heatmaps()                       % pick the runs in a file dialog (Ctrl+click
%                                            % for several), then the no-magnet background
%                                            % (Cancel = none); runs sorted by time stamp
%   compare_heatmaps(files)                  % runs compared in the order given, e.g.
%                                            % {"run1.csv", "run2.csv", "run3.csv"}
%   compare_heatmaps("C:\scans\run*.csv")   % wildcard: runs sorted by their time stamp
%   compare_heatmaps(files, baselineFile)    % subtract a background scan from every run
%   compare_heatmaps(files, "")              % raw field (includes Earth's field)
%   compare_heatmaps([], baselineFile)       % pick the runs, background given
%   compare_heatmaps("Save", true)           % pick the files, with options
%
% File names can be full paths or relative to MATLAB's current folder. This file is
% all it needs; apply_tilt.m and tilt_correct.m only with "TiltCorrect".
%   compare_heatmaps(..., "Save", true)      % also save PNGs next to the first CSV
%   compare_heatmaps(..., "Labels", false)   % no values printed on the maps
%   compare_heatmaps(..., "Floor", 0.02)     % leave out points where the earlier run's
%                                            % |B| is below 0.02 G (% blows up there)
%   compare_heatmaps(..., "CLim", 100)       % colour scale fixed at -100..+100 %
%   compare_heatmaps(..., "TiltCorrect", true)   % remove the probe's tilt first
%   compare_heatmaps(..., "R", R)            % sensor -> robot rotation
%   compare_heatmaps(..., "Pairs", [1 2; 3 4])   % compare these runs instead of 1->2, 2->3, ...
%   compare_heatmaps(..., "Title", "Repeatability")  % prefix for the figure titles
%   compare_heatmaps(..., "Name", "repeat")  % PNG names with "Save" (default heatmap_change)
%   D = compare_heatmaps(..., "Plot", false) % numbers only
%
% Run k is compared with run k+1 (1 -> 2, 2 -> 3, ...) at every grid point, or each
% row [a b] of "Pairs" compares run a with run b:
%
%   change (%) = 100 * (|B|_b - |B|_a) / |B|_a
%
% so +50 % means the field at that point got 50 % stronger in the later run.
% |B| is the same quantity plot_field_layers shows in its heat map (figure 1),
% with the same baseline subtraction, so the maps line up with those.
% Points are matched between runs by position (to 0.1 mm), not by row.
%
% Figure 1: one column per pair of runs, one row per z layer. Red = the field got
%           stronger, blue = weaker, white = no change; one colour scale for all.
% Figure 2: summary per pair: mean change, mean size of the change (mean |%|),
%           and the change in the total field over the grid.
% Command window: the same summary as a table.
%
% D is a struct: files, names, P (points, mm), Bmag (N x nRun, G), pct (N x nPair, %),
% pairs (labels) and the summary columns (one value per pair).

optNames = {'Save', 'Labels', 'Plot', 'Floor', 'CLim', 'R', 'TiltCorrect', 'Pairs', 'Title', 'Name'};
if nargin < 1, files = []; end
haveBase = nargin >= 2 && ~(isnumeric(baselineFile) && isempty(baselineFile));
if (ischar(files) || isstring(files)) && any(strcmpi(char(files), optNames))
    % compare_heatmaps("Save", true, ...): options only, so pick the files
    if nargin >= 2, varargin = [{files, baselineFile}, varargin]; else, varargin = {files}; end
    files = [];
    haveBase = false;
elseif haveBase && (ischar(baselineFile) || isstring(baselineFile)) && ...
        any(strcmpi(char(baselineFile), optNames))
    % compare_heatmaps(files, "Save", true): no background, options start here
    varargin = [{baselineFile}, varargin];
    haveBase = false;
end

p = inputParser;
p.addParameter("Save", false);
p.addParameter("Labels", true);
p.addParameter("Plot", true);
p.addParameter("Floor", 0);          % G; earlier-run |B| below this -> left out
p.addParameter("CLim", []);          % %; [] = largest change in the data
p.addParameter("R", []);
p.addParameter("TiltCorrect", false);
p.addParameter("Pairs", []);         % nPair x 2 run numbers; [] = consecutive
p.addParameter("Title", "");
p.addParameter("Name", "heatmap_change");
p.parse(varargin{:});
opt = p.Results;

if isempty(files)
    [files, folder] = pick_runs();
    if ~haveBase, baselineFile = pick_background(folder); end
else
    files = list_files(files);
    if ~haveBase, baselineFile = ''; end
end
baselineFile = char(baselineFile);
nRun = numel(files);
if nRun < 2, error("Need at least 2 runs to compare, got %d.", nRun); end

R = opt.R;
if isempty(R)
    R = eye(3);
    if exist("scan_config", "file")
        cfg = scan_config();
        if isfield(cfg, "R_sensor_to_robot"), R = cfg.R_sensor_to_robot; end
    end
end

% --- |B| of every run on the first run's grid ---
names = cell(nRun, 1);
for r = 1:nRun
    [~, n] = fileparts(files{r});
    names{r} = regexprep(n, '_\d{8}_\d{6}$', '');   % drop the time stamp
    [Pr, Br] = load_field(files{r}, baselineFile, R, opt.TiltCorrect);
    if r == 1
        P = Pr;
        Bmag = nan(size(P, 1), nRun);
    end
    [found, loc] = ismember(round(10 * P), round(10 * Pr), "rows");   % to 0.1 mm
    if ~any(found)
        error("%s has no points in common with %s.", files{r}, files{1});
    elseif ~all(found)
        warning("%s: %d of %d points of the first run are missing and left out.", ...
            names{r}, nnz(~found), numel(found));
    end
    Bmag(found, r) = sqrt(sum(Br(loc(found), :).^2, 2));
end

% --- percentage change, run a -> run b of each pair ---
ab = opt.Pairs;
if isempty(ab), ab = [(1:nRun - 1).' (2:nRun).']; end
if size(ab, 2) ~= 2 || any(ab(:) < 1 | ab(:) > nRun | ab(:) ~= round(ab(:)))
    error("Pairs must be rows [a b] of run numbers 1..%d.", nRun);
end
nPair = size(ab, 1);
pct = nan(size(P, 1), nPair);
pairs = cell(nPair, 1);
for k = 1:nPair
    a = Bmag(:, ab(k, 1)); b = Bmag(:, ab(k, 2));
    ok = isfinite(a) & isfinite(b) & a > max(opt.Floor, eps);
    pct(ok, k) = 100 * (b(ok) - a(ok)) ./ a(ok);
    pairs{k} = sprintf("%d -> %d", ab(k, 1), ab(k, 2));
end

% --- summary per pair ---
meanPct = nan(nPair, 1); meanAbs = meanPct; medAbs = meanPct; largest = meanPct;
totalPct = meanPct; nPts = zeros(nPair, 1); largestAt = nan(nPair, 3);
for k = 1:nPair
    v = pct(:, k); ok = isfinite(v);
    nPts(k) = nnz(ok);
    if ~any(ok), continue; end
    meanPct(k) = mean(v(ok));
    meanAbs(k) = mean(abs(v(ok)));
    medAbs(k) = median(abs(v(ok)));
    av = abs(v); av(~ok) = -Inf;
    [~, i] = max(av);
    largest(k) = v(i);
    largestAt(k, :) = P(i, :);
    a = Bmag(ok, ab(k, 1)); b = Bmag(ok, ab(k, 2));
    totalPct(k) = 100 * (sum(b) - sum(a)) / sum(a);
end

what = 'Raw |B|';
if ~isempty(baselineFile)
    [~, n0] = fileparts(baselineFile);
    what = ['|B| minus ' n0];
end
if ~isempty(opt.Title), what = [char(opt.Title) ', ' what]; end
fprintf('\nChange in %s between runs, %% of the earlier run\n\n', what);
for r = 1:nRun, fprintf('  run %d  %s\n', r, names{r}); end
runs = cell(nPair, 1);
for k = 1:nPair, runs{k} = [names{ab(k, 1)} ' -> ' names{ab(k, 2)}]; end
w = max(cellfun(@numel, runs));
fprintf(['\n  %-7s %-' num2str(w) 's %8s %8s %8s %9s  %-18s %8s %4s\n'], 'pair', 'runs', 'mean', ...
    'mean|%|', 'med|%|', 'largest', 'at (x, y, z) mm', 'total', 'pts');
for k = 1:nPair
    fprintf(['  %-7s %-' num2str(w) 's %+7.1f%% %7.1f%% %7.1f%% %+8.1f%%  %-18s %+7.1f%% %4d\n'], ...
        pairs{k}, runs{k}, meanPct(k), meanAbs(k), medAbs(k), ...
        largest(k), sprintf('(%.0f, %.0f, %.0f)', largestAt(k, :)), totalPct(k), nPts(k));
end
fprintf(['\n  mean: average change (+ stronger, - weaker)   mean|%%| / med|%%|: average / median\n' ...
    '  size of the change   largest: biggest change, at the point given   total: change in\n' ...
    '  |B| summed over the grid   pts: points compared\n\n']);

D = struct("files", {files}, "names", {names}, "P", P, "Bmag", Bmag, "pct", pct, ...
    "pairs", {pairs}, "pair_runs", ab, "mean_pct", meanPct, "mean_abs_pct", meanAbs, ...
    "median_abs_pct", medAbs, "largest_pct", largest, "largest_at_mm", largestAt, ...
    "total_pct", totalPct, "n_points", nPts);
if ~opt.Plot, return; end

% --- 1: percentage-change maps, one column per pair, one row per z layer ---
xs = unique(P(:, 1)); ys = unique(P(:, 2)); zs = sort(unique(P(:, 3)), "descend");
nz = numel(zs);
if numel(xs) < 2 || numel(ys) < 2
    error("Need at least 2 points along x and y for a map.");
end
dx = min(diff(xs)); dy = min(diff(ys));
pad = [-0.5 0.5];
cl = opt.CLim;
if isempty(cl), cl = max(abs(pct(isfinite(pct)))); end
if isempty(cl) || ~isfinite(cl(end)) || cl(end) == 0, cl = 1; end
cl = [-1 1] * abs(cl(end));
[X, Y] = meshgrid(xs, ys);
[xf, yf] = meshgrid(linspace(xs(1), xs(end), 101), linspace(ys(1), ys(end), 101));

f1 = figure("Name", "Heat map change between runs", "Color", "w", ...
    "Position", [60 60 max(700, 300 * nPair + 150) 450 * nz + 60]);
for iz = 1:nz
    for k = 1:nPair
        subplot(nz, nPair, (iz - 1) * nPair + k);
        M = to_grid(P, pct(:, k), xs, ys, zs(iz));
        Mf = interp2(xs, ys, M, xf, yf, "linear");
        imagesc(xf(1, :), yf(:, 1), Mf, "AlphaData", double(~isnan(Mf))); hold on
        set(gca, "YDir", "normal");
        plot(X(:), Y(:), "k.", "MarkerSize", 8);
        if opt.Labels
            for i = find(~isnan(M(:)))'
                text(X(i), Y(i) + 0.22 * dy, sprintf("%+.0f%%", M(i)), "FontSize", 7, ...
                    "HorizontalAlignment", "center", "Color", [0.1 0.1 0.1]);
            end
        end
        hold off
        caxis(cl); colormap(gca, redblue(256));
        axis equal tight
        set(gca, "XTick", xs, "YTick", ys);
        xlim([xs(1) xs(end)] + pad * dx); ylim([ys(1) ys(end)] + pad * dy);
        xlabel("x (mm)"); ylabel("y (mm)");
        v = M(isfinite(M));
        title({names{ab(k, 1)}, ['->  ' names{ab(k, 2)}], ...
            sprintf("z = %.0f mm, mean %+.1f %%", zs(iz), mean(v))}, ...
            "Interpreter", "none", "FontSize", 9);
        if k == nPair
            cb = colorbar; ylabel(cb, "change in |B| (%)");
        end
    end
end
suptitle_compat(f1, sprintf("%s: change between runs, %% of the earlier run", what));

% --- 2: summary per pair ---
f2 = figure("Name", "Heat map change summary", "Color", "w", "Position", [100 100 760 420]);
bar(1:nPair, [meanPct meanAbs totalPct]);
hold on; plot([0.5 nPair + 0.5], [0 0], "k-"); hold off
set(gca, "XTick", 1:nPair, "XTickLabel", pairs);
xlim([0.5 nPair + 0.5]);
xlabel("runs compared"); ylabel("change (%)");
legend({"mean change (signed)", "mean size of change |%|", "total field over the grid"}, ...
    "Location", "best");
grid on
title(sprintf("%s: change between runs", what), "Interpreter", "none");

if opt.Save
    d = fileparts(files{1});
    n = char(opt.Name);
    print(f1, fullfile(d, [n '.png']), '-dpng', '-r150');
    print(f2, fullfile(d, [n '_summary.png']), '-dpng', '-r150');
    fprintf("Saved %s.png and %s_summary.png in %s\n", n, n, d);
end
end


function [files, folder] = pick_runs()
% file dialog for the runs; sorted by the time stamp in their names when they all have one
[f, folder] = uigetfile({'*.csv', 'Scan CSVs (*.csv)'}, ...
    'Pick the runs to compare (Ctrl+click or Shift+click for several)', 'MultiSelect', 'on');
if isequal(f, 0), error("No runs picked."); end
files = fullfile(folder, cellstr(f));
files = sort_by_stamp(files(:));
end


function baselineFile = pick_background(folder)
[f, d] = uigetfile({'*.csv', 'Scan CSVs (*.csv)'}, ...
    'Pick the no-magnet background scan (Cancel = no background)', folder);
if isequal(f, 0)
    baselineFile = '';
    fprintf('No background picked: comparing the raw field (includes Earth''s field).\n');
else
    baselineFile = fullfile(d, f);
end
end


function files = sort_by_stamp(files)
stamp = regexp(files, '\d{8}_\d{6}', 'match', 'once');
if all(~cellfun(@isempty, stamp))
    [~, order] = sort(stamp);
else
    [~, order] = sort(files);
end
files = files(order);
end


function files = list_files(files)
% cell of CSV paths, from a string array / cell, or one wildcard pattern (sorted by
% the time stamp in the names, i.e. the order the runs were taken)
files = cellstr(files);
if numel(files) == 1 && any(files{1} == '*' | files{1} == '?')
    d = dir(files{1});
    if isempty(d)
        error(['No files match %s in %s.\nGo to the folder with the CSVs (cd, or the ' ...
            'Current Folder panel), give the full path, or run compare_heatmaps() to ' ...
            'pick the files.'], files{1}, pwd);
    end
    files = sort_by_stamp(fullfile({d.folder}, {d.name}).');
end
files = files(:);
for r = 1:numel(files)
    if ~isfile(files{r})
        error("Cannot find %s (looked in %s). Give the full path, or run compare_heatmaps() to pick the files.", ...
            files{r}, pwd);
    end
end
end


function [P, B] = load_field(file, baselineFile, R, tc)
% positions and field (robot axes, background subtracted) of one scan
T = read_scan(file);
P = [T.x_mm T.y_mm T.z_mm];
B = [T.Bx_G T.By_G T.Bz_G];
if tilt_on(tc), B = apply_tilt(B, file, tc, baselineFile); end
if ~isempty(baselineFile)
    T0 = read_scan(baselineFile);
    [found, loc] = ismember(round(10 * P), round(10 * [T0.x_mm T0.y_mm T0.z_mm]), "rows");
    if ~any(found)
        error("Baseline has no points in common with %s.", file);
    elseif ~all(found)
        warning("%d of %d points of %s have no baseline at the same position and are left out.", ...
            nnz(~found), numel(found), file);
    end
    B0all = [T0.Bx_G T0.By_G T0.Bz_G];
    if tilt_on(tc), B0all = apply_tilt(B0all, baselineFile, tc, baselineFile); end
    B0 = nan(size(B));
    B0(found, :) = B0all(loc(found), :);
    B = B - B0;
end
B = (R * B.').';                     % sensor axes -> robot axes
end


function on = tilt_on(tc)
% the "TiltCorrect" option is set (true or a reference), so apply_tilt is needed
on = ~(isempty(tc) || ((islogical(tc) || isnumeric(tc)) && isscalar(tc) && ~tc));
end


function M = to_grid(P, v, xs, ys, z)
M = nan(numel(ys), numel(xs));
on = abs(P(:, 3) - z) < 0.05 & isfinite(v);
[~, ix] = min(abs(P(on, 1) - xs.'), [], 2);
[~, iy] = min(abs(P(on, 2) - ys.'), [], 2);
M(sub2ind(size(M), iy, ix)) = v(on);
end


function T = read_scan(file)
% CSV -> struct of columns by header name. textscan, so it runs in MATLAB and Octave.
fid = fopen(file);
if fid < 0, error('Cannot open %s', file); end
names = strsplit(strtrim(fgetl(fid)), ',');
C = textscan(fid, repmat('%f', 1, numel(names)), 'Delimiter', ',');
fclose(fid);
T = struct();
for i = 1:numel(names)
    T.(names{i}) = C{i};
end
end


function cmap = redblue(n)
% blue (negative) -> white -> red (positive)
t = linspace(-1, 1, n).';
cmap = [min(1, 1 + t) min(1, 1 - abs(t)) min(1, 1 - t)];
cmap = 0.15 + 0.85 * cmap;
end


function suptitle_compat(fig, s)
figure(fig);
if exist("sgtitle", "file") || exist("sgtitle", "builtin")
    sgtitle(s, "FontSize", 12, "Interpreter", "none");
else
    annotation("textbox", [0 0.94 1 0.05], "String", s, "EdgeColor", "none", ...
        "HorizontalAlignment", "center", "FontSize", 12, "Interpreter", "none");
end
end
