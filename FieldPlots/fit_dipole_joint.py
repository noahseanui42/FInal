"""Joint dipole fit: several scans of the SAME magnet moved between runs (not rotated).

    python FieldPlots/fit_dipole_joint.py BACKGROUND.csv RUN1.csv RUN2.csv ...
    python FieldPlots/fit_dipole_joint.py --plot BACKGROUND.csv RUN1.csv ...   # + comparison figure

Fits one magnetic moment m shared by every run, and one position r0 per run, to
(run - background) at the points both scans share (matched by position). Sharing m
removes the trade-off between moment tilt and position that a one-run fit
(fit_dipole.m) has when the magnet is far below the grid, so the shifts between
runs come out much tighter. Prints each r0 and the shift of every run from the
first. Positions are the target probe coordinates (robot frame, mm); fields are
taken in sensor axes as logged (R_sensor_to_robot = identity, as scan_config.m).

--plot draws one figure (and saves it next to the first run as dipole_joint_fit.png):
the magnet-only |B| on the bottom layer for every run, with the fitted magnet position
(x) and the ruler position (o); a top view of fitted vs ruler positions; and the shift
table. The ruler position comes from the file name (dipole_y+100_..., dipole_x-50_...:
that offset from the run named ..._y0_ or ..._x0_, or from the first run if none is).

Model as fit_dipole.m: B = mu0/(4 pi) (3 (m.u) u - m) / |r|^3, r = p - r0, u = r/|r|.
Uncertainties are 1-sigma from the fit covariance (independent residuals assumed,
so lower bounds). Needs numpy, pandas, scipy.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

POS = ["x_mm", "y_mm", "z_mm"]
FIELD = ["Bx_G", "By_G", "Bz_G"]


def load(run, bg):
    d = pd.read_csv(run)
    d[POS] = d[POS].round(2)
    j = d.merge(bg, on=POS, suffixes=("", "_bg")).dropna(subset=FIELD + [c + "_bg" for c in FIELD])
    return j[POS].values / 1000.0, j[FIELD].values - j[[c + "_bg" for c in FIELD]].values


def dipole_G(P, r0, m):
    r = P - r0
    n = np.linalg.norm(r, axis=1, keepdims=True)
    u = r / n
    return 1e-7 * (3 * (u @ m)[:, None] * u - m) / n ** 3 * 1e4      # T -> G


def fit(data):
    n = len(data)

    def res(p):
        return np.concatenate([(dipole_G(P, p[3 + 3 * i:6 + 3 * i], p[:3]) - B).ravel()
                               for i, (P, B) in enumerate(data)])

    best = None
    for z0 in (-0.85, -0.95, -1.05):                 # start below the grid, a few guesses
        for mx in (-0.5, 0.0, 0.5):
            s = least_squares(res, np.r_[mx, 0.0, 2.5, [0.0, 0.0, z0] * n])
            if best is None or s.cost < best.cost:
                best = s
    p, J = best.x, best.jac
    cov = np.linalg.inv(J.T @ J) * 2 * best.cost / (len(best.fun) - len(p))
    return p, np.sqrt(np.diag(cov)), best.fun.reshape(-1, 3)


def ruler_offset(run):
    """(dx, dy) mm from a name like dipole_y+100_... or dipole_x-50_..., else None."""
    m = re.search(r"_([xy])([+-]?\d+(?:\.\d+)?)_", Path(run).stem)
    if not m:
        return None
    v = float(m.group(2))
    return np.array([v, 0.0]) if m.group(1) == "x" else np.array([0.0, v])


def plot(runs, data, r0, s0, out_png):
    import matplotlib.pyplot as plt
    names = [Path(r).stem.split("_2026")[0] for r in runs]
    offs = [ruler_offset(r) for r in runs]
    ref = next((i for i, o in enumerate(offs) if o is not None and not o.any()), 0)
    base = r0[ref][:2] - (offs[ref] if offs[ref] is not None else 0)
    expect = [base + o if o is not None else None for o in offs]

    n = len(runs)
    fig = plt.figure(figsize=(3.2 * max(n, 4), 9.5), constrained_layout=True)
    top, bottom = fig.subfigures(2, 1, height_ratios=[1.15, 1])   # rows laid out separately
    maps = np.atleast_1d(top.subplots(1, n))
    view, table = bottom.subplots(1, 2, gridspec_kw={"width_ratios": [1, 1.25]})
    zlow = min(P[:, 2].min() for P, _ in data)
    vmax = max(np.linalg.norm(B, axis=1).max() for _, B in data)
    for i, ((P, B), r, e) in enumerate(zip(data, r0, expect)):
        ax = maps[i]
        on = np.isclose(P[:, 2], zlow)
        xs, ys = np.unique(P[on, 0] * 1000), np.unique(P[on, 1] * 1000)
        M = np.full((len(ys), len(xs)), np.nan)
        for p, b in zip(P[on] * 1000, np.linalg.norm(B[on], axis=1)):
            M[np.searchsorted(ys, p[1]), np.searchsorted(xs, p[0])] = b
        im = ax.imshow(M, origin="lower", interpolation="bilinear", vmin=0, vmax=vmax, cmap="viridis",
                       extent=[xs[0], xs[-1], ys[0], ys[-1]], aspect="equal")
        ax.plot(*np.meshgrid(xs, ys), "k.", ms=3)
        if e is not None:
            ax.plot(*e, "o", mfc="none", mec="w", ms=12, mew=2)
        ax.plot(r[0], r[1], "x", color="r", ms=11, mew=2.5)
        ax.set_xlim(-110, 110)
        ax.set_ylim(ys[0] - 20, ys[-1] + 20)
        ax.set_title(names[i], fontsize=10)
        ax.set_xlabel("x (mm)")
        if i == 0:
            ax.set_ylabel("y (mm)")
    top.colorbar(im, ax=maps, shrink=0.8, label=f"magnet-only |B| at z = {zlow * 1000:.0f} mm (G)")

    ax = view
    for name, r, s, e in zip(names, r0, s0, expect):
        if e is not None:
            ax.plot(*e, "o", mfc="none", mec="0.4", ms=10)
            ax.annotate("", xy=r[:2], xytext=e, arrowprops=dict(arrowstyle="->", color="0.5"))
        ax.errorbar(r[0], r[1], xerr=s[0], yerr=s[1], fmt="x", color="r", ms=9, mew=2, capsize=3)
        ax.annotate(name.replace("dipole_", ""), r[:2], textcoords="offset points", xytext=(8, 6), fontsize=9)
    ax.plot([], [], "o", mfc="none", mec="0.4", label="ruler position (from the reference run)")
    ax.plot([], [], "x", color="r", mew=2, label="fitted position (1 sigma bars)")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=8, borderaxespad=0)
    pts = np.array([r[:2] for r in r0] + [e for e in expect if e is not None])
    ax.set_xlim(pts[:, 0].min() - 30, pts[:, 0].max() + 30)
    ax.set_ylim(pts[:, 1].min() - 30, pts[:, 1].max() + 30)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_title("Top view: fitted magnet positions vs ruler")

    ax = table
    ax.axis("off")
    rows = []
    for i in range(n):
        for j in range(i + 1, n):
            if offs[i] is None or offs[j] is None:
                continue
            ruler = offs[j] - offs[i]
            if np.count_nonzero(ruler) != 1:      # moves along x or along y only
                continue
            d = r0[j] - r0[i]
            sd = np.hypot(s0[i][:2], s0[j][:2])   # 1 sigma of the difference, per axis
            L, Lf = np.linalg.norm(ruler), np.linalg.norm(d[:2])
            sdL = np.sqrt(np.sum((d[:2] / max(Lf, 1e-9)) ** 2 * sd ** 2))
            rows.append([f"{names[i].replace('dipole_', '')} -> {names[j].replace('dipole_', '')}",
                         f"{L:.0f}", f"{Lf:.1f} +- {sdL:.1f}", f"{Lf - L:+.1f}"])
    if rows:
        t = ax.table(cellText=rows, colLabels=["move", "ruler (mm)", "fitted (mm)", "error (mm)"],
                     loc="center", cellLoc="center")
        t.auto_set_font_size(False)
        t.set_fontsize(9)
        t.scale(1, 1.4)
    ax.set_title("Moves along x or y: fitted length vs ruler")
    fig.suptitle("Dipole known-position test: joint fit, one shared moment", fontsize=13)
    fig.savefig(out_png, dpi=150)
    print(f"saved {out_png}")
    plt.show()


def main(argv):
    want_plot = "--plot" in argv
    argv = [a for a in argv if a != "--plot"]
    if len(argv) < 3:
        sys.exit(__doc__)
    bg = pd.read_csv(argv[1])
    bg[POS] = bg[POS].round(2)
    runs = argv[2:]
    data = [load(r, bg) for r in runs]
    p, sd, resid = fit(data)
    m = p[:3]
    print(f"shared moment m = [{m[0]:.3f} {m[1]:.3f} {m[2]:.3f}] A m^2, |m| = {np.linalg.norm(m):.3f}, "
          f"{np.degrees(np.arccos(m[2] / np.linalg.norm(m))):.1f} deg from +z")
    print(f"residual RMS {np.sqrt((resid ** 2).sum(1).mean()):.4f} G over {len(resid)} points")
    r0 = [p[3 + 3 * i:6 + 3 * i] * 1000 for i in range(len(runs))]
    s0 = [sd[3 + 3 * i:6 + 3 * i] * 1000 for i in range(len(runs))]
    for run, r, s, (P, _) in zip(runs, r0, s0, data):
        print(f"{Path(run).stem:34s} r0 = ({r[0]:7.1f}, {r[1]:7.1f}, {r[2]:7.1f}) mm"
              f"  +- ({s[0]:.1f}, {s[1]:.1f}, {s[2]:.1f})  [{len(P)} points]")
    for run, r in zip(runs[1:], r0[1:]):
        d = r - r0[0]
        print(f"shift {Path(run).stem} - first: ({d[0]:6.1f}, {d[1]:6.1f}, {d[2]:5.1f}) mm, "
              f"|shift| = {np.linalg.norm(d):.1f} mm")
    if want_plot:
        plot(runs, data, r0, s0, Path(runs[0]).with_name("dipole_joint_fit.png"))


if __name__ == "__main__":
    main(sys.argv)
