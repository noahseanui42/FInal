function D = compare_repeat_heatmaps(folder, varargin)
% compare_repeat_heatmaps — the 6 Oct repeatability test: five scans with the magnet
% fixed under the grid (repeat_under-run1 ... run5) and the no-magnet reference scan
% (repeat_none), as heat maps and as the % change from one run to the next.
%
%   compare_repeat_heatmaps()                  % finds the files itself (see below)
%   compare_repeat_heatmaps("C:\scans\data")   % or in this folder
%   compare_repeat_heatmaps(..., "Units", "mG")    % change in milligauss instead of %
%   compare_repeat_heatmaps(..., "Save", true) % also save PNGs next to the CSVs
%   compare_repeat_heatmaps(..., "Labels", false)  % no values printed on the maps
%   D = compare_repeat_heatmaps(..., "Plot", false)  % numbers only
%
% The files are found by name, repeat_under-run*.csv and repeat_none_*.csv, in: the
% folder given, MATLAB's current folder, this file's folder, its data/ subfolder, or
% ../FieldTiltScan/data. If they aren't in any of those, a dialog asks for the folder.
% This file is all it needs.
%
% The no-magnet scan is the reference: it is subtracted from every run point by point,
% leaving the magnet's field only (the Earth's field, the servos' magnets and the
% sensor's offset are in both and cancel). Then at every grid point:
%
%   change (%)  = 100 * (|B| of run k+1 - |B| of run k) / |B| of run k
%   change (mG) = 1000 * (|B| of run k+1 - |B| of run k)       ("Units", "mG")
%
% The % is relative to the magnet's field, which is weakest on the top layer, so the
% same change in mG is a bigger % there. The mG maps show the change itself, the same
% size wherever the field is weak or strong (1 mG = 0.1 uT).
%
% Nothing was touched between the runs, so the change is the system's repeatability
% (plus any drift over the hour).
%
% Figure 1: heat maps of |B|, one row per z layer: the no-magnet reference (raw field,
%           its own colour scale), then runs 1-5 (magnet only, one shared scale).
% Figure 2: change (% or mG), run 1 -> 2, 2 -> 3, 3 -> 4, 4 -> 5, one row per z layer.
%           Red = stronger in the later run, blue = weaker, white = no change.
% Figure 3: summary per pair: mean change, mean size of the change, and the total over
%           the grid (%) or the RMS change (mG).
% Command window: the same numbers as a table.
%
% D: files, reference, P (points, mm), Bmag (N x 5, magnet only, G), Bref (N x 1, raw
% no-magnet |B|, G), pct (N x 4, %), dmG (N x 4, mG), units, and the summary numbers per
% pair in those units.

p = inputParser;
p.addParameter("Save", false);
p.addParameter("Labels", true);
p.addParameter("Plot", true);
p.addParameter("Units", "%");        % "%" or "mG"
if nargin >= 1 && any(strcmpi(char(folder), {'Save', 'Labels', 'Plot', 'Units'}))
    varargin = [{folder}, varargin];
    folder = '';
end
if nargin < 1, folder = ''; end
p.parse(varargin{:});
opt = p.Results;
units = char(opt.Units);
if any(strcmpi(units, {'mG', 'milligauss'}))
    units = 'mG';
elseif any(strcmpi(units, {'%', 'pct', 'percent'}))
    units = '%';
else
    error('"Units" must be "%%" or "mG", not "%s".', units);
end

% --- find the files ---
[runs, ref] = find_files(char(folder));
nRun = numel(runs);
fprintf('\nReference (no magnet): %s\n', ref);
for r = 1:nRun, fprintf('Run %d: %s\n', r, runs{r}); end

% --- |B| of each run minus the reference, matched by position ---
T0 = read_scan(ref);
P0 = [T0.x_mm T0.y_mm T0.z_mm];
B0 = [T0.Bx_G T0.By_G T0.Bz_G];
for r = 1:nRun
    T = read_scan(runs{r});
    Pr = [T.x_mm T.y_mm T.z_mm];
    if r == 1
        P = Pr;
        Bmag = nan(size(P, 1), nRun);
        [found0, loc0] = ismember(round(10 * P), round(10 * P0), "rows");   % to 0.1 mm
        if ~any(found0), error("The reference has no points in common with run 1."); end
        if ~all(found0)
            warning("%d of %d points have no reference at the same position and are left out.", ...
                nnz(~found0), numel(found0));
        end
        Bref = nan(size(P, 1), 1);
        Bref(found0) = sqrt(sum(B0(loc0(found0), :).^2, 2));
    end
    [found, loc] = ismember(round(10 * P), round(10 * Pr), "rows");
    if ~all(found)
        warning("Run %d is missing %d of run 1's points; they are left out.", r, nnz(~found));
    end
    ok = found & found0;
    Br = [T.Bx_G T.By_G T.Bz_G];
    Bmag(ok, r) = sqrt(sum((Br(loc(ok), :) - B0(loc0(ok), :)).^2, 2));
end

% --- change, run k -> run k+1, in % and in mG ---
nPair = nRun - 1;
dmG = 1000 * (Bmag(:, 2:end) - Bmag(:, 1:end-1));
pct = 100 * (Bmag(:, 2:end) - Bmag(:, 1:end-1)) ./ Bmag(:, 1:end-1);
pct(~isfinite(pct)) = NaN;
pairs = arrayfun(@(k) sprintf('%d -> %d', k, k + 1), (1:nPair).', 'UniformOutput', false);
if strcmp(units, 'mG')
    chg = dmG; uLabel = 'mG'; uFmt = '%+.1f'; uName = 'in mG';
    lastName = 'rms';                 % RMS change over the grid, mG
else
    chg = pct; uLabel = '%'; uFmt = '%+.1f%%'; uName = '% of the earlier run';
    lastName = 'total';               % change in |B| summed over the grid, %
end

meanChg = nan(nPair, 1); meanAbs = meanChg; medAbs = meanChg; largest = meanChg;
lastCol = meanChg; largestAt = nan(nPair, 3);
for k = 1:nPair
    v = chg(:, k); ok = isfinite(v);
    if ~any(ok), continue; end
    meanChg(k) = mean(v(ok));
    meanAbs(k) = mean(abs(v(ok)));
    medAbs(k) = median(abs(v(ok)));
    av = abs(v); av(~ok) = -Inf;
    [~, i] = max(av);
    largest(k) = v(i);
    largestAt(k, :) = P(i, :);
    if strcmp(units, 'mG')
        lastCol(k) = sqrt(mean(v(ok).^2));
    else
        lastCol(k) = 100 * (sum(Bmag(ok, k + 1)) - sum(Bmag(ok, k))) / sum(Bmag(ok, k));
    end
end

fprintf('\nMagnet field (run minus no-magnet reference): median |B| per run, G\n');
fprintf('  run %d: %.4f\n', [1:nRun; arrayfun(@(r) med_ok(Bmag(:, r)), 1:nRun)]);
fprintf('No-magnet reference (raw): median |B| %.4f G\n', med_ok(Bref));
u = strrep(uLabel, '%', '%%');
fprintf(['\nChange from one run to the next, ' strrep(uName, '%', '%%') '\n\n']);
fprintf('  %-7s %9s %9s %9s %9s  %-18s %9s\n', 'runs', 'mean', ['mean|' uLabel '|'], ...
    ['med|' uLabel '|'], 'largest', 'at (x, y, z) mm', lastName);
w = num2str(9 - numel(uLabel));      % number width, so the unit fits the column
sgn = '+';
if strcmp(units, 'mG'), sgn = ''; end   % rms is never negative
for k = 1:nPair
    fprintf(['  %-7s %+' w '.1f' u ' %' w '.1f' u ' %' w '.1f' u ' %+' w '.1f' u ...
        '  %-18s %' sgn w '.1f' u '\n'], ...
        pairs{k}, meanChg(k), meanAbs(k), medAbs(k), largest(k), ...
        sprintf('(%.0f, %.0f, %.0f)', largestAt(k, :)), lastCol(k));
end
fprintf(['\n  mean: average change (+ stronger, - weaker)   mean|.| / med|.|: average / median\n' ...
    '  size of the change   largest: biggest change, at that point\n']);
if strcmp(units, 'mG')
    fprintf('  rms: root-mean-square change over the grid   (1 mG = 0.1 uT)\n\n');
else
    fprintf('  total: change in |B| summed over the grid\n\n');
end

D = struct("files", {runs}, "reference", ref, "P", P, "Bmag", Bmag, "Bref", Bref, ...
    "pct", pct, "dmG", dmG, "units", units, "pairs", {pairs}, "mean", meanChg, ...
    "mean_abs", meanAbs, "median_abs", medAbs, "largest", largest, ...
    "largest_at_mm", largestAt, "total_or_rms", lastCol);
if ~opt.Plot, return; end

% --- grid ---
xs = unique(P(:, 1)); ys = unique(P(:, 2)); zs = sort(unique(P(:, 3)), "descend");
nz = numel(zs);
if numel(xs) < 2 || numel(ys) < 2, error("Need at least 2 points along x and y for a map."); end
dx = min(diff(xs)); dy = min(diff(ys));
[X, Y] = meshgrid(xs, ys);
[xf, yf] = meshgrid(linspace(xs(1), xs(end), 101), linspace(ys(1), ys(end), 101));
fmt = struct("xs", xs, "ys", ys, "dx", dx, "dy", dy, "X", X, "Y", Y, "xf", xf, "yf", yf, ...
    "labels", opt.Labels);

% --- 1: heat maps, reference then runs ---
f1 = figure("Name", "Repeatability: heat maps", "Color", "w", ...
    "Position", [40 40 230 * (nRun + 1) + 120 430 * nz + 60]);
limRef = [min(Bref) max(Bref)];
limRun = [min(Bmag(:)) max(Bmag(:))];
if diff(limRef) == 0, limRef = limRef + [-1 1] * 1e-3; end
if diff(limRun) == 0, limRun = limRun + [-1 1] * 1e-3; end
for iz = 1:nz
    subplot(nz, nRun + 1, (iz - 1) * (nRun + 1) + 1);
    map_panel(to_grid(P, Bref, xs, ys, zs(iz)), fmt, limRef, seq_map(), "%.3f");
    title({"No magnet (reference)", sprintf("raw, z = %.0f mm", zs(iz))}, "FontSize", 9);
    cb = colorbar; ylabel(cb, "|B| (G)");
    for r = 1:nRun
        subplot(nz, nRun + 1, (iz - 1) * (nRun + 1) + 1 + r);
        map_panel(to_grid(P, Bmag(:, r), xs, ys, zs(iz)), fmt, limRun, seq_map(), "%.3f");
        ylabel("");                    % same y axis as the reference panel
        title({sprintf("Run %d", r), sprintf("magnet only, z = %.0f mm", zs(iz))}, "FontSize", 9);
        if r == nRun, cb = colorbar; ylabel(cb, "|B| (G)"); end
    end
end
suptitle_compat(f1, "Repeatability: no-magnet reference (raw) and runs 1-5 (minus the reference), |B|");

% --- 2: change maps ---
cl = max(abs(chg(isfinite(chg))));
if isempty(cl) || cl == 0, cl = 1; end
f2 = figure("Name", ['Repeatability: change (' uLabel ')'], "Color", "w", ...
    "Position", [60 60 260 * nPair + 140 430 * nz + 60]);
for iz = 1:nz
    for k = 1:nPair
        subplot(nz, nPair, (iz - 1) * nPair + k);
        M = to_grid(P, chg(:, k), xs, ys, zs(iz));
        map_panel(M, fmt, [-cl cl], redblue(256), uFmt);
        v = M(isfinite(M));
        title({sprintf("Run %d -> run %d", k, k + 1), ...
            sprintf(['z = %.0f mm, mean |change| %.1f ' u], zs(iz), mean(abs(v)))}, "FontSize", 9);
        if k == nPair, cb = colorbar; ylabel(cb, ['change in |B| (' uLabel ')']); end
    end
end
suptitle_compat(f2, ['Repeatability: change in |B| (magnet only) from one run to the next, ' uName]);

% --- 3: summary ---
f3 = figure("Name", "Repeatability: summary", "Color", "w", "Position", [100 100 700 420]);
bar(1:nPair, [meanChg meanAbs lastCol]);
hold on; plot([0.5 nPair + 0.5], [0 0], "k-"); hold off
set(gca, "XTick", 1:nPair, "XTickLabel", pairs);
xlim([0.5 nPair + 0.5]);
xlabel("runs compared"); ylabel(['change (' uLabel ')']);
if strcmp(units, 'mG'), third = 'RMS change over the grid'; else, third = 'total field over the grid'; end
legend({'mean change (signed)', 'mean size of change', third}, "Location", "northeast");
grid on
title("Repeatability: change from one run to the next");

if opt.Save
    d = fileparts(runs{1});
    print(f1, fullfile(d, 'repeat_heatmaps.png'), '-dpng', '-r150');
    tag = '';
    if strcmp(units, 'mG'), tag = '_mG'; end
    print(f2, fullfile(d, ['repeat_change' tag '.png']), '-dpng', '-r150');
    print(f3, fullfile(d, ['repeat_change' tag '_summary.png']), '-dpng', '-r150');
    fprintf("Saved repeat_heatmaps.png, repeat_change%s.png and repeat_change%s_summary.png in %s\n", ...
        tag, tag, d);
end
end


function [runs, ref] = find_files(folder)
% the five runs (sorted by name: run1 ... run5) and the no-magnet scan
here = fileparts(mfilename("fullpath"));
places = {folder, pwd, here, fullfile(here, 'data'), fullfile(here, '..', 'FieldTiltScan', 'data')};
places = places(~cellfun(@isempty, places));
for i = 1:numel(places)
    [runs, ref] = files_in(places{i});
    if ~isempty(runs), return; end
end
d = uigetdir(pwd, 'Pick the folder with repeat_under-run*.csv and repeat_none_*.csv');
if isequal(d, 0), error("No folder picked."); end
[runs, ref] = files_in(d);
if isempty(runs)
    error("No repeat_under-run*.csv and repeat_none_*.csv files in %s.", d);
end
end


function [runs, ref] = files_in(d)
runs = {}; ref = '';
r = dir(fullfile(d, 'repeat_under-run*.csv'));
n = dir(fullfile(d, 'repeat_none_*.csv'));
n = n(cellfun(@isempty, regexp({n.name}, '_tiltcorr', 'once')));
r = r(cellfun(@isempty, regexp({r.name}, '_tiltcorr', 'once')));
if numel(r) < 2 || isempty(n), return; end
names = sort({r.name});
runs = fullfile(d, names(:));
ref = fullfile(d, n(1).name);
if numel(n) > 1
    warning("%d repeat_none files in %s; using %s.", numel(n), d, n(1).name);
end
if numel(runs) ~= 5
    warning("Found %d repeat_under-run files in %s (expected 5); using all of them.", numel(runs), d);
end
end


function map_panel(M, g, lim, cmap, labelFmt)
Mf = interp2(g.xs, g.ys, M, g.xf, g.yf, "linear");
imagesc(g.xf(1, :), g.yf(:, 1), Mf, "AlphaData", double(~isnan(Mf))); hold on
set(gca, "YDir", "normal");
plot(g.X(:), g.Y(:), "k.", "MarkerSize", 8);
if g.labels
    for i = find(~isnan(M(:)))'
        text(g.X(i), g.Y(i) + 0.22 * g.dy, sprintf(labelFmt, M(i)), "FontSize", 6, ...
            "HorizontalAlignment", "center", "Color", [0.1 0.1 0.1]);
    end
end
hold off
caxis(lim); colormap(gca, cmap);
axis equal tight
set(gca, "XTick", g.xs, "YTick", g.ys);
xlim([g.xs(1) g.xs(end)] + [-0.5 0.5] * g.dx); ylim([g.ys(1) g.ys(end)] + [-0.5 0.5] * g.dy);
xlabel("x (mm)"); ylabel("y (mm)");
end


function m = med_ok(v)
% median of the finite values (median's "omitnan" isn't in Octave)
m = median(v(isfinite(v)));
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


function cmap = seq_map()
% parula in MATLAB, viridis in Octave (no parula there)
if exist("parula", "file") || exist("parula", "builtin")
    cmap = parula(256);
else
    cmap = viridis(256);
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
