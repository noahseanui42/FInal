"""Repeatability: several scans of the SAME grid with the magnet left where it is,
plotted all together against each other.

    python FieldPlots/plot_repeat_runs.py RUN1.csv RUN2.csv ...           # or a wildcard
    python FieldPlots/plot_repeat_runs.py "FieldTiltScan/data/repeat50_run*.csv" --bg BACKGROUND.csv
    python FieldPlots/plot_repeat_runs.py ... --out FieldTiltScan/figures/repeat50 --show

Runs are matched point by point by target position (x_mm, y_mm, z_mm); points that
are NaN in any run are left out. Fields are as logged: gauss, sensor axes.

Figures (PNG, written to --out, default figures/<first run's label> next to data/):
  1_overlay      Bx, By, Bz and |B| at every point, every run on top of each other
  2_deviation    each run minus the mean of all runs, per component, with the sensor
                 noise of one point's mean as a grey band: what "repeatable" looks like
  3_run_vs_run   RMS difference between every pair of runs (G): drift shows up as
                 runs further apart in time being further apart in field
  4_spread_map   spread over runs of the field vector at each point, one panel per z layer
  5_per_run      each run's mean offset from the all-run mean, per component: a steady
                 trend is drift (Earth field, temperature), scatter is the robot
  6_dipole       (only with --bg) joint dipole fit, one moment shared by every run and
                 one magnet position per run: the scatter of the fitted position is the
                 whole system's repeatability in mm

A summary is printed and saved as summary.txt in the same folder.
Needs numpy, pandas, matplotlib (scipy too for the dipole fit).
"""
import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

POS = ["x_mm", "y_mm", "z_mm"]
FIELD = ["Bx_G", "By_G", "Bz_G"]
STD = ["Bx_std_G", "By_std_G", "Bz_std_G"]

# run colours: one ordinal blue ramp, run 1 lightest -> last run darkest, so a
# drift over the session reads as a gradient
RAMP = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]
COMP = ["#2a78d6", "#eb6834", "#1baf7a"]          # Bx, By, Bz (categorical slots 1-3)
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
NOISE = "#d6d5ce"


def run_colours(n):
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("r", RAMP)
    return [cmap(i / max(n - 1, 1)) for i in range(n)]


def style():
    plt.rcParams.update({
        "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb",
        "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2, "text.color": INK,
        "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID,
        "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
        "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold", "legend.frameon": False,
        "lines.linewidth": 1.5,
    })


def expand(patterns):
    files = []
    for p in patterns:
        hits = sorted(glob.glob(p)) if any(c in p for c in "*?[") else [p]
        files += [h for h in hits if not h.endswith("_tiltcorr.csv")]
    return files


def load_runs(files):
    """Runs on a shared set of points: P (N x 3, mm), B (R x N x 3), noise (R x N x 3),
    t0 (R start times from the meta, or None), and the layer index of each point."""
    tabs = []
    for f in files:
        d = pd.read_csv(f)
        d[POS] = d[POS].round(2)
        d = d.dropna(subset=FIELD).drop_duplicates(subset=POS, keep="last")
        tabs.append(d.set_index(POS))
    common = tabs[0].index
    for d in tabs[1:]:
        common = common.intersection(d.index)
    if len(common) == 0:
        sys.exit("The runs have no valid points in common: were they on the same grid?")
    order = tabs[0].index[tabs[0].index.isin(common)]          # scan order of the first run
    B = np.stack([d.loc[order, FIELD].to_numpy() for d in tabs])
    noise = np.stack([d.loc[order, STD].to_numpy() / np.sqrt(
        np.maximum(d.loc[order, "n_samples"].to_numpy(), 1) if "n_samples" in d else 20)[:, None]
        for d in tabs])
    for f, d in zip(files, tabs):
        if len(d) != len(order):
            print(f"note: {Path(f).name}: {len(d) - len(order)} point(s) not in every run, left out")
    P = np.array(list(order))
    return P, B, noise


def start_times(files):
    import json
    out = []
    for f in files:
        m = Path(f).with_suffix(".meta.json")
        try:
            out.append(pd.Timestamp(json.loads(m.read_text())["started"]))
        except Exception:
            return None
    return out


def layer_marks(ax, P, label=True):
    """Hairlines between z layers on a point-index axis, with the layer's z on top."""
    z = P[:, 2]
    edges = [0] + [i for i in range(1, len(z)) if z[i] != z[i - 1]] + [len(z)]
    for e in edges[1:-1]:
        ax.axvline(e + 0.5, color="#c3c2b7", lw=0.8, zorder=0)
    if label:
        for a, b in zip(edges[:-1], edges[1:]):
            ax.text((a + b) / 2 + 0.5, 1.0, f"z {z[a]:.0f}", transform=ax.get_xaxis_transform(),
                    ha="center", va="bottom", color=MUTED, fontsize=8)


def save(fig, out, name, saved):
    p = out / f"{name}.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    saved.append(p)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("runs", nargs="+", help="run CSVs, or a quoted wildcard")
    ap.add_argument("--bg", default="", help="no-magnet scan: subtracted for the plots and needed for the dipole fit")
    ap.add_argument("--out", default="", help="folder for the PNGs and summary.txt")
    ap.add_argument("--names", nargs="+", help="legend names, one per run (default run 1, run 2, ...)")
    ap.add_argument("--show", action="store_true", help="also open the figures")
    a = ap.parse_args(argv)

    files = expand(a.runs)
    if a.bg:
        files = [f for f in files if Path(f).resolve() != Path(a.bg).resolve()]
    if len(files) < 2:
        sys.exit(f"Need at least 2 runs, got {len(files)}.")
    R = len(files)
    names = a.names or [f"run {k}" for k in range(1, R + 1)]
    if len(names) != R:
        sys.exit(f"--names: {len(names)} names for {R} runs")
    out = Path(a.out) if a.out else Path(files[0]).resolve().parent.parent / "figures" / (
        Path(files[0]).stem.split("_run")[0] + "_repeat")
    out.mkdir(parents=True, exist_ok=True)

    P, B, noise = load_runs(files)
    N = len(P)
    bg_note = ""
    if a.bg:
        bg = pd.read_csv(a.bg)
        bg[POS] = bg[POS].round(2)
        bg = bg.dropna(subset=FIELD).drop_duplicates(subset=POS).set_index(POS)
        keys = pd.MultiIndex.from_arrays(P.T)
        have = keys.isin(bg.index)
        Bbg = np.full((N, 3), np.nan)
        Bbg[have] = bg.loc[keys[have], FIELD].to_numpy()
        bg_note = f" minus background ({have.sum()} of {N} points have one)"
    else:
        Bbg = np.zeros((N, 3))
    Bm = B - Bbg                                   # magnet field (or raw field without --bg)

    mean = B.mean(axis=0)                          # N x 3: deviations don't depend on the background
    dev = B - mean                                 # R x N x 3
    sig_vec = np.sqrt(B.var(axis=0, ddof=1).sum(axis=1))          # N: spread of the vector over runs
    noise_pt = np.sqrt((noise ** 2).mean(axis=0))                 # N x 3: one point's mean
    noise_vec = np.sqrt((noise_pt ** 2).sum(axis=1))
    rms_run = np.sqrt((dev ** 2).sum(axis=2).mean(axis=1))        # R: each run vs the mean
    offset = dev.mean(axis=1)                                     # R x 3: each run's mean offset
    pair = np.array([[np.sqrt(((B[i] - B[j]) ** 2).sum(axis=1).mean()) for j in range(R)] for i in range(R)])
    Bmag_m = np.linalg.norm(Bm, axis=2)                           # R x N
    rel = sig_vec / np.nanmedian(np.linalg.norm(Bm.mean(axis=0), axis=1))

    style()
    cols = run_colours(R)
    idx = np.arange(1, N + 1)
    saved = []
    what = "magnet field" if a.bg else "field"

    # 1. overlay ---------------------------------------------------------------
    fig, axs = plt.subplots(4, 1, figsize=(11, 9), sharex=True)
    series = [Bm[:, :, 0], Bm[:, :, 1], Bm[:, :, 2], Bmag_m]
    for ax, s, lab in zip(axs, series, ["Bx (G)", "By (G)", "Bz (G)", "|B| (G)"]):
        for r in range(R):
            ax.plot(idx, s[r], "-o", ms=2.5, lw=1.2, color=cols[r], label=names[r])
        ax.set_ylabel(lab)
        layer_marks(ax, P, label=ax is axs[0])
    axs[0].legend(ncol=R, loc="upper left", bbox_to_anchor=(0, 1.25), fontsize=8)
    axs[-1].set_xlabel("point (scan order)")
    fig.suptitle(f"All {R} runs overlaid: {what}{bg_note}, sensor axes", x=0.01, ha="left", y=1.0)
    fig.tight_layout()
    save(fig, out, "1_overlay", saved)

    # 2. deviation from the mean of all runs ----------------------------------
    fig, axs = plt.subplots(3, 1, figsize=(11, 7.5), sharex=True, sharey=True)
    for c, ax in enumerate(axs):
        n = noise_pt[:, c] * 1e3
        ax.fill_between(idx, -2 * n, 2 * n, color=NOISE, lw=0, step="mid", zorder=0,
                        label="sensor noise ±2σ (one point)")
        for r in range(R):
            ax.plot(idx, dev[r, :, c] * 1e3, "-", lw=1.0, color=cols[r], label=names[r])
        ax.set_ylabel(f"{FIELD[c][:2]} − mean (mG)")
        layer_marks(ax, P, label=c == 0)
    axs[0].legend(ncol=R + 1, loc="upper left", bbox_to_anchor=(0, 1.3), fontsize=8)
    axs[-1].set_xlabel("point (scan order)")
    fig.suptitle(f"Each run minus the mean of all {R}: median spread {np.median(sig_vec) * 1e3:.2f} mG, "
                 f"sensor noise {np.median(noise_vec) * 1e3:.2f} mG", x=0.01, ha="left", y=1.0)
    fig.tight_layout()
    save(fig, out, "2_deviation", saved)

    # 3. run vs run -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(1.1 * R + 2.5, 1.0 * R + 1.8))
    show = pair * 1e3
    im = ax.imshow(show, cmap=matplotlib.colors.LinearSegmentedColormap.from_list(
        "b", ["#f0efec"] + RAMP), vmin=0)
    for i in range(R):
        for j in range(R):
            ax.text(j, i, "–" if i == j else f"{show[i, j]:.2f}", ha="center", va="center",
                    color="white" if show[i, j] > 0.6 * show.max() else INK, fontsize=9)
    ax.set_xticks(range(R), names, rotation=30, ha="right")
    ax.set_yticks(range(R), names)
    ax.grid(False)
    fig.colorbar(im, ax=ax, label="RMS |ΔB| over all points (mG)", shrink=0.8)
    ax.set_title("Every run against every other run")
    fig.tight_layout()
    save(fig, out, "3_run_vs_run", saved)

    # 4. spread map per z layer -------------------------------------------------
    zs = np.unique(P[:, 2])[::-1]                    # top layer first
    xs, ys = np.unique(P[:, 0]), np.unique(P[:, 1])
    fig, axs = plt.subplots(1, len(zs), figsize=(2.2 + 1.1 * len(xs) * len(zs), 1.2 + 0.45 * len(ys)),
                            squeeze=False, sharey=True)
    vmax = np.nanmax(sig_vec) * 1e3
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("b", ["#cde2fb"] + RAMP)
    for ax, z in zip(axs[0], zs):
        G = np.full((len(ys), len(xs)), np.nan)
        for (x, y, zz), s in zip(P, sig_vec):
            if zz == z:
                G[np.searchsorted(ys, y), np.searchsorted(xs, x)] = s * 1e3
        im = ax.imshow(G, origin="lower", cmap=cmap, vmin=0, vmax=vmax, aspect="auto",
                       extent=[-0.5, len(xs) - 0.5, -0.5, len(ys) - 0.5])
        for i in range(len(ys)):
            for j in range(len(xs)):
                if np.isfinite(G[i, j]):
                    ax.text(j, i, f"{G[i, j]:.2f}", ha="center", va="center", fontsize=7,
                            color="white" if G[i, j] > 0.55 * vmax else INK)
        ax.set_xticks(range(len(xs)), [f"{v:.0f}" for v in xs])
        ax.set_yticks(range(len(ys)), [f"{v:.0f}" for v in ys])
        ax.grid(False)
        ax.set_title(f"z {z:.0f} mm")
        ax.set_xlabel("x (mm)")
    axs[0][0].set_ylabel("y (mm)")
    fig.colorbar(im, ax=axs[0].tolist(), label="spread of B over runs (mG)", shrink=0.9)
    fig.suptitle(f"Spread of the field vector over {R} runs at each point "
                 f"(sensor noise {np.median(noise_vec) * 1e3:.2f} mG)", x=0.01, ha="left")
    save(fig, out, "4_spread_map", saved)

    # 5. per run ------------------------------------------------------------------
    t0 = start_times(files)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.6))
    if t0:
        xr = np.array([(t - t0[0]).total_seconds() / 60 for t in t0])
        xl = "run start (min after run 1)"
    else:
        xr, xl = np.arange(1, R + 1), "run"
    for c in range(3):
        ax1.plot(xr, offset[:, c] * 1e3, "-o", ms=6, color=COMP[c], label=FIELD[c][:2])
        ax1.annotate(FIELD[c][:2], (xr[-1], offset[-1, c] * 1e3), xytext=(6, 0),
                     textcoords="offset points", va="center", color=INK2, fontsize=8)
    ax1.axhline(0, color="#c3c2b7", lw=0.8)
    if not t0:
        ax1.set_xticks(xr)
    ax1.set_xlabel(xl)
    ax1.set_ylabel("mean offset from all-run mean (mG)")
    ax1.set_title("Drift: each run's average offset")
    ax1.legend(loc="best", fontsize=8)
    ax2.bar(range(R), rms_run * 1e3, color=cols, width=0.6)
    ax2.axhline(np.median(noise_vec) * 1e3, color=INK2, lw=1, ls="--")
    ax2.annotate("sensor noise", (-0.45, np.median(noise_vec) * 1e3), xytext=(0, 3),
                 textcoords="offset points", va="bottom", ha="left", color=INK2, fontsize=8)
    ax2.set_xticks(range(R), names)
    ax2.set_ylabel("RMS |B − mean| over points (mG)")
    ax2.set_title("How far each run is from the mean")
    fig.tight_layout()
    save(fig, out, "5_per_run", saved)

    # 6. joint dipole fit -----------------------------------------------------------
    fit_lines = []
    if a.bg:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        try:
            import fit_dipole_joint as fj
        except ImportError as e:
            fit_lines.append(f"dipole fit skipped: {e} (pip install scipy)")
        else:
            bgd = pd.read_csv(a.bg)
            bgd[POS] = bgd[POS].round(2)
            data = [fj.load(f, bgd) for f in files]
            p, sd, resid = fj.fit(data)
            m = p[:3]
            r0 = np.array([p[3 + 3 * i:6 + 3 * i] * 1000 for i in range(R)])
            s0 = np.array([sd[3 + 3 * i:6 + 3 * i] * 1000 for i in range(R)])
            d0 = r0 - r0.mean(axis=0)
            fit_lines += [
                f"Joint dipole fit ({len(data[0][0])} points per run with a background): shared |m| = "
                f"{np.linalg.norm(m):.3f} A m^2, {np.degrees(np.arccos(m[2] / np.linalg.norm(m))):.1f} deg "
                f"from +z, residual RMS {np.sqrt((resid ** 2).sum(1).mean()):.4f} G",
                f"  {'run':10s} {'x':>8s} {'y':>8s} {'z':>8s}   (mm)  1-sigma (mm)"]
            for k in range(R):
                fit_lines.append(f"  {names[k]:10s} {r0[k, 0]:8.2f} {r0[k, 1]:8.2f} {r0[k, 2]:8.2f}"
                                 f"         ({s0[k, 0]:.1f}, {s0[k, 1]:.1f}, {s0[k, 2]:.1f})")
            sdp = r0.std(axis=0, ddof=1)
            fit_lines.append(f"  {'std':10s} {sdp[0]:8.2f} {sdp[1]:8.2f} {sdp[2]:8.2f}"
                             f"   -> fitted magnet position repeats to {np.linalg.norm(sdp):.2f} mm (3D std)")
            fig, ax = plt.subplots(figsize=(7, 3.6))
            for c in range(3):
                ax.errorbar(np.arange(R) + (c - 1) * 0.12, d0[:, c], yerr=s0[:, c], fmt="o", ms=6,
                            color=COMP[c], capsize=3, lw=1.2, label="xyz"[c])
            ax.axhline(0, color="#c3c2b7", lw=0.8)
            ax.set_xticks(range(R), names)
            ax.set_ylabel("fitted position − mean (mm)")
            ax.legend(ncol=3, loc="best", fontsize=8)
            ax.set_title(f"Fitted magnet position per run: std x {sdp[0]:.2f}, y {sdp[1]:.2f}, "
                         f"z {sdp[2]:.2f} mm")
            fig.tight_layout()
            save(fig, out, "6_dipole", saved)

    # summary ------------------------------------------------------------------------
    lines = [f"{R} runs, {N} points in every run{bg_note}"]
    lines += [f"  {n:8s} {Path(f).name}" for n, f in zip(names, files)]
    lines += [
        "",
        "Spread of the field vector over runs, per point (sqrt of var Bx + var By + var Bz):",
        f"  median {np.median(sig_vec) * 1e3:.3f} mG, 95th pct {np.percentile(sig_vec, 95) * 1e3:.3f} mG, "
        f"max {sig_vec.max() * 1e3:.3f} mG at ({', '.join(f'{v:.0f}' for v in P[sig_vec.argmax()])}) mm",
        f"  per axis x/y/z median: " + ", ".join(f"{v * 1e3:.3f}" for v in np.median(B.std(axis=0, ddof=1), axis=0))
        + " mG",
        f"  sensor noise of one point's mean: median {np.median(noise_vec) * 1e3:.3f} mG "
        f"(spread / noise = {np.median(sig_vec) / np.median(noise_vec):.1f})",
        f"  relative to the median {what} |B|: median {np.median(rel) * 100:.2f} %",
        "",
        "Each run vs the mean of all runs:",
        f"  {'run':10s} {'RMS (mG)':>9s}   mean offset Bx, By, Bz (mG)",
    ]
    for k in range(R):
        lines.append(f"  {names[k]:10s} {rms_run[k] * 1e3:9.3f}   "
                     + ", ".join(f"{v * 1e3:+.3f}" for v in offset[k]))
    lines += ["", f"Largest pairwise RMS difference: {pair.max() * 1e3:.3f} mG "
                  f"({names[np.unravel_index(pair.argmax(), pair.shape)[0]]} vs "
                  f"{names[np.unravel_index(pair.argmax(), pair.shape)[1]]})"]
    if fit_lines:
        lines += [""] + fit_lines
    lines += ["", "Figures:"] + [f"  {p}" for p in saved]
    text = "\n".join(lines)
    print(text)
    (out / "summary.txt").write_text(text + "\n")
    if a.show:
        plt.show()


if __name__ == "__main__":
    main()
