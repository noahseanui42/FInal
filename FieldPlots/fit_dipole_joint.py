"""Joint dipole fit: several scans of the SAME magnet moved between runs (not rotated).

    python FieldPlots/fit_dipole_joint.py BACKGROUND.csv RUN1.csv RUN2.csv ...

Fits one magnetic moment m shared by every run, and one position r0 per run, to
(run - background) at the points both scans share (matched by position). Sharing m
removes the trade-off between moment tilt and position that a one-run fit
(fit_dipole.m) has when the magnet is far below the grid, so the shifts between
runs come out much tighter. Prints each r0 and the shift of every run from the
first. Positions are the target probe coordinates (robot frame, mm); fields are
taken in sensor axes as logged (R_sensor_to_robot = identity, as scan_config.m).

Model as fit_dipole.m: B = mu0/(4 pi) (3 (m.u) u - m) / |r|^3, r = p - r0, u = r/|r|.
Uncertainties are 1-sigma from the fit covariance (independent residuals assumed,
so lower bounds). Needs numpy, pandas, scipy.
"""
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


def main(argv):
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


if __name__ == "__main__":
    main(sys.argv)
