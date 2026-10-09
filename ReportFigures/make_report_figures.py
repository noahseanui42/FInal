"""Report figures for every test in this repo, in one consistent style.

    python ReportFigures/make_report_figures.py        # from the repo root

Writes the PNGs into ReportFigures/ and prints the numbers quoted in
ReportFigures/FIGURE_NOTES.md. Reads only the data already in the repo:

    DeltaAppCalibrated/tools/servo_sweep/   servo calibration (29-30 Sep)
    FieldScan/data/                         first field scans (2 Oct)
    FieldTiltScan/data/                     tilt scan (2 Oct), full box (3-4 Oct),
                                            dipole test (4 Oct), repeatability (6 Oct)

The analysis follows the MATLAB scripts in FieldPlots/ (compare_runs.m for the
position repeatability, fit_dipole_joint.py for the dipole fit, which is imported).
Fields are in the sensor's axes as logged (R_sensor_to_robot = identity), in
gauss (1 G = 100 uT, 1 mG = 0.1 uT). Needs numpy, pandas, scipy, matplotlib, openpyxl.
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm, Normalize

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ReportFigures"
FS = ROOT / "FieldScan" / "data"
FT = ROOT / "FieldTiltScan" / "data"
SWEEP = ROOT / "DeltaAppCalibrated" / "tools" / "servo_sweep"
sys.path.insert(0, str(ROOT / "FieldPlots"))
import fit_dipole_joint as fdj  # noqa: E402

F = ["Bx_G", "By_G", "Bz_G"]
POS = ["x_mm", "y_mm", "z_mm"]

# ---------------------------------------------------------------- style ----
INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"          # blue, orange, aqua (in this order)
MARK = ["o", "s", "^"]                                 # second encoding next to colour
SEQ = LinearSegmentedColormap.from_list(
    "seq", ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])
DIV = LinearSegmentedColormap.from_list(
    "div", ["#104281", "#3987e5", "#9ec5f4", "#f0efec", "#f2a3a2", "#e34948", "#a32a2a"])

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10,
    "axes.titleweight": "bold", "axes.titlelocation": "left",
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.8, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "axes.spines.top": False,
    "axes.spines.right": False, "legend.frameon": False, "legend.fontsize": 8,
    "lines.linewidth": 2, "lines.markersize": 5, "figure.facecolor": "white",
    "savefig.facecolor": "white", "savefig.dpi": 200, "figure.dpi": 100,
})


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print(f"  -> ReportFigures/{name}")


def heat(ax, x, y, v, cmap, norm, step=None):
    """Cell map of v on a regular x-y grid (one z layer)."""
    xs, ys = np.unique(x), np.unique(y)
    M = np.full((len(ys), len(xs)), np.nan)
    M[np.searchsorted(ys, y), np.searchsorted(xs, x)] = v
    hx = (xs[1] - xs[0]) / 2 if len(xs) > 1 else 12.5
    hy = (ys[1] - ys[0]) / 2 if len(ys) > 1 else 12.5
    im = ax.imshow(M, origin="lower", cmap=cmap, norm=norm, interpolation="nearest",
                   extent=[xs[0] - hx, xs[-1] + hx, ys[0] - hy, ys[-1] + hy], aspect="equal")
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    return im


def load(p):
    d = pd.read_csv(p)
    d[POS] = d[POS].round(2)
    return d


def bmag(d):
    return np.linalg.norm(d[F].values, axis=1)


def repeatability(files, noise_file):
    """Python port of FieldPlots/compare_runs.m: sigma_B over runs, noise floor, sigma_pos."""
    ds = [load(f) for f in files]
    P = ds[0][POS].values
    for d in ds[1:]:
        assert np.allclose(d[POS].values, P), "runs are not on the same grid"
    B = np.stack([d[F].values for d in ds], 2)                 # N x 3 x runs
    sigB = np.linalg.norm(B, axis=1).std(1, ddof=1)
    d0 = load(noise_file)
    sd0 = d0[["Bx_std_G", "By_std_G", "Bz_std_G"]].values / np.sqrt(d0.n_samples.values[:, None])
    u0 = d0[F].values / np.linalg.norm(d0[F].values, axis=1, keepdims=True)
    noise = np.sqrt(((u0 * sd0) ** 2).sum(1))
    sigBc = np.sqrt(np.maximum(sigB ** 2 - noise ** 2, 0))
    axes = [np.unique(P[:, k]) for k in range(3)]
    ix = tuple(np.searchsorted(a, P[:, k]) for k, a in enumerate(axes))
    V = np.full([len(a) for a in axes], np.nan)
    V[ix] = np.linalg.norm(B.mean(2), axis=1)
    grad = np.sqrt(sum(g[ix] ** 2 for g in np.gradient(V, *axes)))
    sp = sigBc / grad
    sp[~(grad > 0.1 * np.median(grad))] = np.nan
    return dict(P=P, sigB=sigB, noise=noise, grad=grad, sp=sp)


def pct(v, q):
    return np.nanpercentile(v, q)


# ============================================================ 1. servos ====
def fig_servo_sweep():
    print("\n[1] Assembled protractor sweep, 30 Sep")
    d = pd.read_csv(SWEEP / "sweep_2026-09-30_up.csv")
    up = d[d["pass"] == "up"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.0), constrained_layout=True)
    for k, (pin, arm) in enumerate([("D9", "Arm 1"), ("D10", "Arm 2"), ("D11", "Arm 3")]):
        cmd, meas = up.cmd_deg.values, up[f"meas_{pin}_deg"].values
        err = meas - cmd
        s, o = np.polyfit(cmd, meas, 1)
        res = meas - (s * cmd + o)
        lab = f"{pin} ({arm})"
        a.plot(up.probe_z_mm, err, "-", marker=MARK[k], color=[C1, C2, C3][k], label=lab, ms=4.5)
        b.plot(up.probe_z_mm, res, "-", marker=MARK[k], color=[C1, C2, C3][k], label=lab, ms=4.5)
        print(f"  {pin}: before refit error {err.min():+.1f} .. {err.max():+.1f} deg "
              f"(at -730: {err[0]:+.1f}); fit s = {s:.3f}, o = {o:+.2f} deg, "
              f"worst residual {np.abs(res).max():.1f} deg")
    for ax in (a, b):
        ax.axhline(0, color=AXIS, lw=1, zorder=1)
        ax.set_xlabel("Probe height z (mm), on the robot's axis")
        ax.invert_xaxis()
    a.set_ylabel("Measured − commanded bicep angle (°)")
    b.set_ylabel("Measured − straight-line fit (°)")
    a.set_title("a) Error with the old calibration")
    b.set_title("b) Left over after the straight-line refit")
    h, l = a.get_legend_handles_labels()
    fig.legend(h, l, loc="outside lower center", ncol=3, fontsize=8.5)
    save(fig, "fig01_servo_protractor_sweep.png")


def fig_arm2_ruler():
    print("\n[2] Arm 2 (D10) unloaded ruler sweep, 29 Sep")
    import openpyxl
    ws = openpyxl.load_workbook(SWEEP / "servo2_angles.xlsx").active
    R, D, h = ws["E4"].value, ws["E5"].value, ws["E6"].value
    c_old, k_old = ws["E7"].value, ws["E8"].value
    rows = [(r[0], r[1]) for r in ws.iter_rows(min_row=11, values_only=True)
            if isinstance(r[0], (int, float)) and isinstance(r[1], (int, float))]
    us, dcm = np.array(rows, float).T
    th = np.degrees(np.arcsin((dcm - D) / np.hypot(R, h)) + np.arctan(h / R))
    slope, icpt = np.polyfit(us, th, 1)
    res = th - (slope * us + icpt)
    print(f"  {len(us)} points {us[0]:.0f}-{us[-1]:.0f} us; fit {1 / slope:.2f} us/deg, "
          f"centre {-icpt / slope:.0f} us; worst off-line {np.abs(res).max():.1f} deg; "
          f"old config error up to {np.abs(th - (us - c_old) / k_old).max():.1f} deg; "
          f"reached {th.max():.1f} deg")
    fig, (a, b) = plt.subplots(2, 1, figsize=(6.0, 4.4), sharex=True, constrained_layout=True,
                               gridspec_kw={"height_ratios": [2.2, 1]})
    a.plot(us, th, "o", color=C1, ms=3.5, label="Measured (ruler)")
    a.plot(us, slope * us + icpt, "-", color=INK2, lw=1.5,
           label=f"Straight-line fit: {1 / slope:.2f} µs/°, θ = 0 at {-icpt / slope:.0f} µs")
    a.plot(us, (us - c_old) / k_old, "--", color=C2, lw=1.5,
           label=f"Old config.h: {k_old:g} µs/°, θ = 0 at {c_old:g} µs")
    a.set_ylabel("Bicep angle θ (°, + = down)")
    a.set_title("Arm 2 (D10), unloaded: angle against servo pulse width")
    a.legend(loc="upper left")
    b.axhline(0, color=AXIS, lw=1)
    b.plot(us, res, "o-", color=C1, ms=3, lw=1)
    b.set_ylabel("Off the fit (°)")
    b.set_xlabel("Servo pulse width (µs)")
    save(fig, "fig02_arm2_ruler_sweep.png")


# ====================================================== 2. field maps ====
def layer_maps(d, bg, title, name, arrows=True, ncol=None):
    """|B| of the magnet alone (scan − background) per z layer, with in-plane arrows."""
    j = d.merge(bg, on=POS, suffixes=("", "_bg"))
    Bm = j[F].values - j[[c + "_bg" for c in F]].values
    m = np.linalg.norm(Bm, axis=1) * 1000
    zs = np.sort(j.z_mm.unique())
    n = len(zs)
    xs, ys = np.unique(j.x_mm), np.unique(j.y_mm)
    tall = (np.ptp(ys) / max(np.ptp(xs), 1)) > 1.5
    fig, axs = plt.subplots(1, n, figsize=(1.9 * n + 1.0, 4.8 if tall else 2.8),
                            constrained_layout=True, squeeze=False)
    norm = Normalize(0, np.nanmax(m))
    for i, z in enumerate(zs):
        ax = axs[0, i]
        on = np.isclose(j.z_mm, z)
        im = heat(ax, j.x_mm[on].values, j.y_mm[on].values, m[on], SEQ, norm)
        if arrows:
            u, v = Bm[on, 0], Bm[on, 1]
            sc = np.nanmax(np.hypot(u, v))
            cell = xs[1] - xs[0]
            ax.quiver(j.x_mm[on], j.y_mm[on], u / sc, v / sc, color="white", scale=1 / (0.9 * cell),
                      scale_units="xy", angles="xy", pivot="middle", width=0.014, headwidth=3.5,
                      headlength=4, alpha=0.95)
        ax.set_title(f"z = {z:.0f} mm", fontweight="normal", loc="center")
        ax.set_xlabel("x (mm)")
        if i == 0:
            ax.set_ylabel("y (mm)")
        else:
            ax.set_yticklabels([])
    cb = fig.colorbar(im, ax=axs[0, :], shrink=0.85, pad=0.02)
    cb.set_label("|B| of the magnet alone (mG)")
    cb.outline.set_visible(False)
    fig.suptitle(title, x=0.01, ha="left", fontsize=10, fontweight="bold")
    save(fig, name)
    return m


def fig_field_map_2oct():
    print("\n[3] Example field map, magnet on +x side, 2 Oct")
    bg = load(FS / "nomagnet_corr-off_run1_20261002_172221.csv")
    d = load(FS / "magnet-xpos_corr-hybrid_run1_20261002_182828.csv")
    m = layer_maps(d, bg, "Magnet on the +x side: field of the magnet alone, per height "
                          "(arrows: in-plane direction)", "fig03_field_map_magnet_xpos.png")
    print(f"  background |B| {np.mean(bmag(bg)) * 1000:.0f} mG; magnet-only {m.min():.0f}-{m.max():.0f} mG "
          f"(median {np.median(m):.0f})")


def fig_full_box():
    print("\n[4] Full-box scan, magnet under the grid, 3 Oct (background 4 Oct)")
    bg = load(FT / "full25-4z_corr-hybrid_none_20261004_155505.csv")
    d = load(FT / "full25-4z_corr-hybrid_under_combined_20261003.csv")
    m = layer_maps(d, bg, "Full scan volume (5 × 13 × 4 = 260 points), magnet under the grid",
                   "fig04_full_box_magnet_under.png")
    print(f"  magnet-only {np.nanmin(m):.0f}-{np.nanmax(m):.0f} mG, median {np.nanmedian(m):.0f}; "
          f"{np.isnan(m).sum()} points blank (no background reading there)")


# ================================================== 3. settle time =====
def fig_settle():
    print("\n[5] Settle time 0.5 s vs 5 s, magnet on -x side, 2 Oct")
    a = load(FS / "magnet-xneg_corr-off_settle0p5s_run1_20261002_022713.csv")
    b = load(FS / "magnet-xneg_corr-off_run1_20261002_024004.csv")
    d = (a[F].values - b[F].values) * 1000
    off = d.mean(0)
    left = np.linalg.norm(d - off, axis=1)
    sa = np.linalg.norm(a[["Bx_std_G", "By_std_G", "Bz_std_G"]].values, axis=1) * 1000
    sb = np.linalg.norm(b[["Bx_std_G", "By_std_G", "Bz_std_G"]].values, axis=1) * 1000
    print(f"  mean difference (0.5 s - 5 s) Bx {off[0]:+.1f}, By {off[1]:+.1f}, Bz {off[2]:+.1f} mG "
          f"(|.| {np.linalg.norm(off):.1f}); left after removing it: median {np.median(left):.1f}, "
          f"max {left.max():.1f} mG")
    print(f"  scatter of the 20 readings at a point: median {np.median(sa):.2f} (0.5 s) vs "
          f"{np.median(sb):.2f} mG (5 s); max {sa.max():.2f} vs {sb.max():.2f}")
    ta, tb = a.t_s.iloc[-1] / 60, b.t_s.iloc[-1] / 60
    print(f"  scan time {ta:.1f} min (0.5 s) vs {tb:.1f} min (5 s)")
    rep = np.linalg.norm(load(sorted(glob.glob(str(FS / "magnet-xpos_corr-off_run1_*.csv")))[0])[F].values
                         - load(sorted(glob.glob(str(FS / "magnet-xpos_corr-off_run2_*.csv")))[0])[F].values,
                         axis=1) * 1000
    dd = np.linalg.norm(d, axis=1)
    print(f"  |dB| per point median {np.median(dd):.1f} mG (max {dd.max():.1f}); same-settings repeat "
          f"(+x, correction off) median {np.median(rep):.1f} mG")
    fig, (p, q) = plt.subplots(1, 2, figsize=(7.2, 3.0), constrained_layout=True,
                               gridspec_kw={"width_ratios": [1.6, 1]})
    idx = a.idx.values
    p.plot(idx, dd, "o", color=C2, ms=4, label="0.5 s scan vs 5 s scan")
    p.axhline(np.median(dd), color=C2, lw=1.2, ls="--")
    p.annotate(f"median\n{np.median(dd):.1f} mG", (idx[-1] + 13, np.median(dd)), xytext=(0, 3),
               textcoords="offset points", ha="right", va="bottom", fontsize=7.5, color=INK)
    p.axhline(np.median(rep), color=C1, lw=1.2, ls="--",
              label="Same settings scanned twice (+x magnet, median)")
    p.annotate(f"median\n{np.median(rep):.1f} mG", (idx[-1] + 13, np.median(rep)), xytext=(0, 3),
               textcoords="offset points", ha="right", va="bottom", fontsize=7.5, color=INK)
    p.set_xlim(0, idx[-1] + 14)
    p.set_ylim(0, None)
    p.set_xlabel("Point number (scan order)")
    p.set_ylabel("Size of the field difference |ΔB| (mG)")
    p.set_title("a) Difference between the two scans")
    p.legend(loc="upper left")
    rng = np.random.default_rng(0)
    for i, (v, c, lab) in enumerate([(sa, C2, "0.5 s"), (sb, C1, "5 s")]):
        q.plot(i + rng.uniform(-0.18, 0.18, len(v)), v, "o", color=c, ms=3, alpha=0.6)
        q.plot([i - 0.28, i + 0.28], [np.median(v)] * 2, color=INK, lw=2)
        q.annotate(f"median\n{np.median(v):.2f}", (i + 0.3, np.median(v)), fontsize=7.5,
                   va="center", color=INK2)
    q.set_xticks([0, 1], ["0.5 s settle", "5 s settle"])
    q.set_xlim(-0.5, 1.9)
    q.set_ylim(0, None)
    q.set_ylabel("Scatter of 20 readings at a point (mG)")
    q.set_title("b) Reading noise at each point")
    q.grid(axis="x", visible=False)
    save(fig, "fig05_settle_time.png")


# ======================================= 4. 2 Oct repeat pairs =========
def fig_repeat_2oct():
    print("\n[6] Repeat pairs, 2 Oct")
    bg = FS / "nomagnet_corr-off_run1_20261002_172221.csv"
    pairs = [("+x magnet,\ncorrection\noff", "magnet-xpos_corr-off_run[12]_*.csv"),
             ("+x magnet,\nhybrid\ncorrection", "magnet-xpos_corr-hybrid_run[12]_*.csv"),
             ("Magnet under,\nleft in place", "magnet-under-replaced_corr-hybrid_run[12]_*.csv")]
    res, diffs = [], []
    for lab, pat in pairs:
        files = sorted(glob.glob(str(FS / pat)))
        r = repeatability(files, bg)
        dd = np.linalg.norm(load(files[0])[F].values - load(files[1])[F].values, axis=1) * 1000
        res.append(r)
        diffs.append(dd)
        print(f"  {lab.replace(chr(10), ' ')}: |dB| median {np.median(dd):.1f} mG; "
              f"sigma_pos median {np.nanmedian(r['sp']):.2f} mm, 95th pct {pct(r['sp'], 95):.2f} mm; "
              f"|grad B| median {np.median(r['grad']) * 1000:.2f} mG/mm")
    moved = np.linalg.norm(load(FS / "magnet-under_corr-hybrid_run1_20261002_205751.csv")[F].values
                           - load(FS / "magnet-under-replaced_corr-hybrid_run2_20261002_214238.csv")[F].values,
                           axis=1) * 1000
    print(f"  magnet taken away and put back: |dB| median {np.median(moved):.0f} mG")
    fig, (p, q) = plt.subplots(1, 2, figsize=(7.4, 3.3), constrained_layout=True)
    rng = np.random.default_rng(1)
    labs = [l for l, _ in pairs] + ["Magnet under,\ntaken away\n& put back"]
    cols = [C1, C2, C3, MUTED]
    for i, (v, c) in enumerate(zip(diffs + [moved], cols)):
        p.plot(rng.uniform(-0.2, 0.2, len(v)) + i, v, "o", color=c, ms=2.8, alpha=0.6)
        p.plot([i - 0.3, i + 0.3], [np.median(v)] * 2, color=INK, lw=2)
        p.annotate(f"{np.median(v):.0f} mG" if np.median(v) >= 10 else f"{np.median(v):.1f} mG",
                   (i + 0.32, np.median(v)), va="center", fontsize=7.5, color=INK, fontweight="bold",
                   bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
    p.set_yscale("log")
    p.set_xticks(range(4), labs, fontsize=7)
    p.set_xlim(-0.5, 3.95)
    p.set_ylabel("Change in field between the two scans (mG)")
    p.set_title("a) Same setup scanned twice")
    p.grid(axis="x", visible=False)
    for i, (r, c) in enumerate(zip(res, cols)):
        v = r["sp"][np.isfinite(r["sp"])]
        q.plot(rng.uniform(-0.2, 0.2, len(v)) + i, v, "o", color=c, ms=2.8, alpha=0.6)
        q.plot([i - 0.3, i + 0.3], [np.median(v)] * 2, color=INK, lw=2)
        q.annotate(f"{np.median(v):.1f} mm", (i + 0.32, np.median(v)), fontsize=7.5, va="center",
                   color=INK, fontweight="bold", bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
    q.set_xticks(range(3), [l for l, _ in pairs], fontsize=7)
    q.set_xlim(-0.5, 2.9)
    q.set_ylim(0, None)
    q.set_ylabel("Position repeatability σ_pos (mm)")
    q.set_title("b) As a position (σ_B / |∇B|)")
    q.grid(axis="x", visible=False)
    save(fig, "fig06_repeat_pairs_2oct.png")


# ============================================================ 5. tilt ====
def fig_tilt():
    print("\n[7] Tilt scan, magnet under, 2 Oct 22:33")
    t = load(FT / "magnet_tilt_20261002_223300_tiltcorr.csv")
    raw = t[["Bx_raw_G", "By_raw_G", "Bz_raw_G"]].values
    dB = np.linalg.norm(t[F].values - raw, axis=1) * 1000
    tilt = t.tilt_deg.values
    zs = np.sort(t.z_mm.unique())[::-1]
    fig, axs = plt.subplots(2, len(zs), figsize=(6.4, 4.6), constrained_layout=True)
    nt, nd = Normalize(0, tilt.max()), Normalize(0, dB.max())
    for i, z in enumerate(zs):
        on = np.isclose(t.z_mm, z)
        im1 = heat(axs[0, i], t.x_mm[on].values, t.y_mm[on].values, tilt[on], SEQ, nt)
        im2 = heat(axs[1, i], t.x_mm[on].values, t.y_mm[on].values, dB[on], SEQ, nd)
        axs[0, i].set_title(f"z = {z:.0f} mm", fontweight="normal", loc="center")
        axs[1, i].set_xlabel("x (mm)")
        for r in range(2):
            if i:
                axs[r, i].set_yticklabels([])
            else:
                axs[r, i].set_ylabel("y (mm)")
            if r == 0:
                axs[r, i].set_xticklabels([])
    for im, row, lab in [(im1, 0, "Probe tilt vs\ngrid centre (°)"), (im2, 1, "Field change from\ntilt correction (mG)")]:
        cb = fig.colorbar(im, ax=axs[row, :], shrink=0.9, pad=0.02)
        cb.set_label(lab)
        cb.outline.set_visible(False)
    fig.suptitle("Probe tilt at each point, and how much correcting for it changes the field",
                 x=0.01, ha="left", fontsize=10, fontweight="bold")
    save(fig, "fig07_tilt_correction.png")
    print(f"  tilt median {np.median(tilt):.2f} deg, max {tilt.max():.2f} deg; field change median "
          f"{np.median(dB):.1f} mG, max {dB.max():.1f} mG "
          f"({100 * np.max(dB / np.linalg.norm(raw, axis=1) / 1000):.1f}% of |B| at most); "
          f"gyro rms median {t.gyro_rms_dps.median():.2f} deg/s")


# ========================================================== 6. dipole ====
def fig_dipole():
    print("\n[8] Dipole known-position test, 4 Oct (joint fit)")
    bg = pd.read_csv(FT / "full25-4z_corr-hybrid_none_20261004_155505.csv")
    bg[POS] = bg[POS].round(2)
    names = ["y0", "y+100", "y-100", "x-50", "x+50"]
    runs = [sorted(glob.glob(str(FT / f"dipole_{n}_2026*.csv")))[0] for n in names]
    data = [fdj.load(r, bg) for r in runs]
    p, sd, resid = fdj.fit(data)
    m = p[:3]
    r0 = [p[3 + 3 * i:6 + 3 * i] * 1000 for i in range(len(runs))]
    s0 = [sd[3 + 3 * i:6 + 3 * i] * 1000 for i in range(len(runs))]
    print(f"  shared moment {np.linalg.norm(m):.2f} A m^2, "
          f"{np.degrees(np.arccos(m[2] / np.linalg.norm(m))):.1f} deg from vertical; "
          f"residual RMS {np.sqrt((resid ** 2).sum(1).mean()) * 1000:.1f} mG over {len(resid)} points")
    for n, r, s in zip(names, r0, s0):
        print(f"  {n:6s} fitted ({r[0]:6.1f}, {r[1]:6.1f}, {r[2]:7.1f}) mm  +- ({s[0]:.1f}, {s[1]:.1f}, {s[2]:.1f})")
    ruler = {"y0": (0, 0), "y+100": (0, 100), "y-100": (0, -100), "x-50": (-50, 0), "x+50": (50, 0)}
    ruler = {k: np.array(v, float) for k, v in ruler.items()}
    base = r0[0][:2]                                   # ruler positions drawn from the fitted y0
    moves = [("y0", "y+100"), ("y0", "y-100"), ("y-100", "y+100"),
             ("y0", "x-50"), ("y0", "x+50"), ("x-50", "x+50")]
    rows = []
    for a, b in moves:
        i, j = names.index(a), names.index(b)
        L = np.linalg.norm(ruler[b] - ruler[a])
        d = (r0[j] - r0[i])[:2]
        Lf = np.linalg.norm(d)
        sdd = np.hypot(s0[i][:2], s0[j][:2])
        sdL = np.sqrt(np.sum((d / Lf) ** 2 * sdd ** 2))
        rows.append((f"{a} → {b}", L, Lf, sdL))
        print(f"  move {a:6s} -> {b:6s}: ruler {L:5.0f} mm, fitted {Lf:6.1f} +- {sdL:.1f} mm, "
              f"error {Lf - L:+5.1f} mm")

    # --- figure 8: field maps per run (bottom layer) ---
    zlow = min(P[:, 2].min() for P, _ in data)
    vmax = max(np.linalg.norm(B[np.isclose(P[:, 2], zlow)], axis=1).max() for P, B in data) * 1000
    fig, axs = plt.subplots(1, 5, figsize=(7.4, 3.9), constrained_layout=True)
    for k, ((P, B), r, n) in enumerate(zip(data, r0, names)):
        on = np.isclose(P[:, 2], zlow)
        im = heat(axs[k], P[on, 0] * 1000, P[on, 1] * 1000, np.linalg.norm(B[on], axis=1) * 1000,
                  SEQ, Normalize(0, vmax))
        e = base + ruler[n]
        axs[k].plot(*e, "o", mfc="none", mec=C2, ms=11, mew=2)
        axs[k].plot(r[0], r[1], "x", color=INK, ms=9, mew=2.2)
        axs[k].set_title(n, loc="center", fontweight="normal")
        axs[k].set_xlabel("x (mm)")
        axs[k].set_xlim(-80, 80)
        if k:
            axs[k].set_yticklabels([])
        else:
            axs[k].set_ylabel("y (mm)")
    cb = fig.colorbar(im, ax=axs, shrink=0.8, pad=0.02)
    cb.set_label(f"|B| of the magnet alone at z = {zlow * 1000:.0f} mm (mG)")
    cb.outline.set_visible(False)
    axs[0].plot([], [], "x", color=INK, mew=2, label="Fitted magnet position")
    axs[0].plot([], [], "o", mfc="none", mec=C2, mew=2, label="Ruler position")
    fig.legend(loc="lower center", bbox_to_anchor=(0.45, -0.07), ncol=2)
    fig.suptitle("Dipole test: the magnet's field for each of the five magnet positions",
                 x=0.01, ha="left", fontsize=10, fontweight="bold")
    save(fig, "fig08_dipole_field_maps.png")

    # --- figure 9: top view + move errors ---
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.4, 3.6), constrained_layout=True,
                               gridspec_kw={"width_ratios": [1, 1.25]})
    for n, r, s in zip(names, r0, s0):
        e = base + ruler[n]
        a.plot(*e, "o", mfc="none", mec=C2, ms=11, mew=1.8)
        a.errorbar(r[0], r[1], xerr=s[0], yerr=s[1], fmt="x", color=INK, ms=7, mew=2, capsize=2.5,
                   elinewidth=1)
        a.annotate(n, r[:2], textcoords="offset points", xytext=(8, 5), fontsize=8, color=INK2)
    a.plot([], [], "x", color=INK, mew=2, label="Fitted (±1σ)")
    a.plot([], [], "o", mfc="none", mec=C2, mew=1.8, label="Ruler (from fitted y0)")
    a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2)
    a.set_aspect("equal")
    a.set_xlim(-110, 130)
    a.set_ylim(-170, 110)
    a.set_xlabel("x (mm)")
    a.set_ylabel("y (mm)")
    a.set_title("a) Top view of the fitted positions")
    yy = np.arange(len(rows))[::-1]
    err = np.array([lf - L for _, L, lf, _ in rows])
    sig = np.array([s for *_, s in rows])
    cols = [C1 if "y" in lab.split("→")[1] else C2 for lab, *_ in rows]
    b.axvline(0, color=AXIS, lw=1)
    for y_, e_, s_, c_, (lab, L, lf, _) in zip(yy, err, sig, cols, rows):
        b.errorbar(e_, y_, xerr=s_, fmt="o", color=c_, ms=6, capsize=3, elinewidth=1.2)
        b.annotate(f"{e_:+.1f} mm", (e_, y_), textcoords="offset points", xytext=(0, 7),
                   ha="center", fontsize=7.5, color=INK)
    b.set_yticks(yy, [f"{lab}  ({L:.0f} mm)" for lab, L, *_ in rows], fontsize=7.5)
    b.set_xlabel("Fitted move − ruler move (mm), ±1σ")
    b.set_title("b) Error in each measured move")
    b.grid(axis="y", visible=False)
    b.set_ylim(-0.7, len(rows) - 0.4)
    save(fig, "fig09_dipole_positions.png")


# =================================================== 7. 6 Oct repeat =====
def fig_repeat_6oct():
    print("\n[9] Five-run repeatability test, 6 Oct")
    files = sorted(glob.glob(str(FT / "repeat_under-run*.csv")))
    none = FT / "repeat_none_20261006_192127.csv"
    ds = [load(f) for f in files]
    d0 = load(none)
    starts = ["18:05", "18:19", "18:34", "18:48", "19:03"]
    t_min = np.array([0, 14, 29, 43, 58])
    drift = np.array([(d[F].values - ds[0][F].values).mean(0) * 1000 for d in ds])
    pitch = np.array([d.acc_pitch_deg.mean() for d in ds + [d0]])
    roll = np.array([d.acc_roll_deg.mean() for d in ds + [d0]])
    for k in range(5):
        print(f"  run {k + 1} ({starts[k]}): drift vs run 1 ({drift[k, 0]:+.1f}, {drift[k, 1]:+.1f}, "
              f"{drift[k, 2]:+.1f}) mG |{np.linalg.norm(drift[k]):.1f}|; pitch {pitch[k]:.2f}, roll {roll[k]:.2f}")
    print(f"  no-magnet run: pitch {pitch[5]:.2f}, roll {roll[5]:.2f}")

    # --- figure 10: drift ---
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.0), constrained_layout=True)
    for k, (c, lab) in enumerate(zip([C1, C2, C3], ["Bx", "By", "Bz"])):
        a.plot(t_min, drift[:, k], "-", marker=MARK[k], color=c, label=lab)
    a.plot(t_min, np.linalg.norm(drift, axis=1), "--", color=INK2, lw=1.5, marker="D", ms=4,
           label="Size |ΔB|")
    a.axhline(0, color=AXIS, lw=1)
    a.set_xticks(t_min, [f"{i + 1}\n{s}" for i, s in enumerate(starts)])
    a.set_xlabel("Run and start time")
    a.set_ylabel("Mean change in field vs run 1 (mG)")
    a.set_title("a) Field drift over the hour")
    a.legend(loc="upper left", ncol=2)
    tt = np.r_[t_min, 76]
    lbl = [f"{i + 1}\n{s}" for i, s in enumerate(starts)] + ["none\n19:21"]
    b.plot(tt, pitch - pitch[0], "-", marker="o", color=C1, label="Pitch")
    b.plot(tt, roll - roll[0], "-", marker="s", color=C2, label="Roll")
    b.axhline(0, color=AXIS, lw=1)
    b.set_xticks(tt, lbl)
    b.set_xlabel("Run and start time")
    b.set_ylabel("Mean probe tilt vs run 1 (°)")
    b.set_title("b) Probe tilt creep over the hour")
    b.legend(loc="upper left")
    save(fig, "fig10_repeat_drift.png")

    # --- figure 11: sigma_pos map + histogram ---
    r = repeatability(files, none)
    sp = r["sp"]
    print(f"  sigma_B median {np.median(r['sigB']) * 1000:.1f} mG (95th {pct(r['sigB'], 95) * 1000:.1f}); "
          f"sensor noise median {np.median(r['noise']) * 1000:.2f} mG; |grad B| median "
          f"{np.median(r['grad']) * 1000:.2f} mG/mm")
    print(f"  sigma_pos median {np.nanmedian(sp):.2f} mm, 75th {pct(sp, 75):.2f}, 95th {pct(sp, 95):.2f}, "
          f"max {np.nanmax(sp):.2f}; {np.isfinite(sp).sum()} of {len(sp)} points usable")
    P = r["P"]
    zs = np.sort(np.unique(P[:, 2]))[::-1]
    fig = plt.figure(figsize=(7.2, 4.4), constrained_layout=True)
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.9])
    norm = Normalize(0, np.nanmax(sp))
    maps = []
    for i, z in enumerate(zs):
        ax = fig.add_subplot(gs[0, i])
        maps.append(ax)
        on = np.isclose(P[:, 2], z)
        im = heat(ax, P[on, 0], P[on, 1], sp[on], SEQ, norm)
        ax.set_title(f"z = {z:.0f} mm", loc="center", fontweight="normal")
        ax.set_xlabel("x (mm)")
        if i:
            ax.set_yticklabels([])
        else:
            ax.set_ylabel("y (mm)")
    cb = fig.colorbar(im, ax=maps, location="bottom", shrink=0.85, pad=0.02)
    cb.set_label("σ_pos (mm)")
    cb.outline.set_visible(False)
    h = fig.add_subplot(gs[0, 2])
    v = sp[np.isfinite(sp)]
    h.hist(v, bins=np.arange(0, np.ceil(v.max()) + 0.5, 0.5), color=C1, edgecolor="white", lw=1.5)
    for q, lab in [(50, "median"), (95, "95th pct")]:
        x = np.percentile(v, q)
        h.axvline(x, color=INK, lw=1.2, ls="-" if q == 50 else ":")
        h.annotate(f"{lab}\n{x:.1f} mm", (x, h.get_ylim()[1] * 0.92), xytext=(4, 0),
                   textcoords="offset points", fontsize=7.5, va="top")
    h.set_xlabel("Position repeatability σ_pos (mm)")
    h.set_ylabel("Number of points")
    h.grid(axis="x", visible=False)
    fig.suptitle("Position repeatability over five runs (σ_B / |∇B| at each point)",
                 x=0.01, ha="left", fontsize=10, fontweight="bold")
    save(fig, "fig11_repeat_sigma_pos.png")

    # --- figure 12: % change between consecutive runs ---
    j0 = d0[F].values
    mags = [np.linalg.norm(d[F].values - j0, axis=1) for d in ds]
    pc = [100 * (mags[k + 1] - mags[k]) / mags[k] for k in range(4)]
    for k, v in enumerate(pc):
        print(f"  run {k + 1} -> {k + 2}: mean |change| {np.mean(np.abs(v)):.1f}%, largest {np.abs(v).max():.1f}%")
    lim = max(np.abs(v).max() for v in pc)
    fig, axs = plt.subplots(2, 4, figsize=(6.6, 6.2), constrained_layout=True)
    nrm = TwoSlopeNorm(0, -lim, lim)
    for k in range(4):
        for i, z in enumerate(zs):
            on = np.isclose(P[:, 2], z)
            ax = axs[i, k]
            im = heat(ax, P[on, 0], P[on, 1], pc[k][on], DIV, nrm)
            if i == 0:
                ax.set_title(f"Run {k + 1} → {k + 2}", loc="center", fontweight="normal")
                ax.set_xticklabels([])
            else:
                ax.set_xlabel("x (mm)")
            if k == 0:
                ax.set_ylabel(f"z = {z:.0f} mm\ny (mm)")
            else:
                ax.set_yticklabels([])
    cb = fig.colorbar(im, ax=axs, shrink=0.6, pad=0.02)
    cb.set_label("Change in the magnet's |B| (%)")
    cb.outline.set_visible(False)
    fig.suptitle("Change in the magnet's field from each run to the next",
                 x=0.01, ha="left", fontsize=10, fontweight="bold")
    save(fig, "fig12_repeat_change_maps.png")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    fig_servo_sweep()
    fig_arm2_ruler()
    fig_field_map_2oct()
    fig_full_box()
    fig_settle()
    fig_repeat_2oct()
    fig_tilt()
    fig_dipole()
    fig_repeat_6oct()
