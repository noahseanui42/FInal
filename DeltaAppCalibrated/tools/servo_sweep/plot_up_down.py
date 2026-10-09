"""Measured vs commanded bicep angle, Up pass vs Down passes, after the 2026-09-30 refit.

Commanded angles are the GUI/IK values at each probe z, so the Down pass at
-590/-600/-610 sits at exactly the same commanded angle as the Up pass there.

Up: verify_after_refit_up.csv (-740 lead-in excluded, it was approached
downward from Home). Down: verify_after_refit_down.csv, both runs ("down"
and "down-cap"); the cap run's last row moved back UP and is left out.
Writes figures/up_down.png and .pdf.

    python3 plot_up_down.py
"""
import csv
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ARMS = ["D9", "D10", "D11"]
UP, DOWN = "#2a78d6", "#eb6834"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def load(name, passes):
    with open(HERE / name, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["pass"] in passes and not r["note"].startswith("moved")]
    cmd = np.array([float(r["cmd_D9_deg"]) for r in rows])
    meas = np.array([[float(r[f"meas_{a}_deg"]) for a in ARMS] for r in rows])
    return cmd, meas


up_cmd, up_meas = load("verify_after_refit_up.csv", ("up",))
d1_cmd, d1_meas = load("verify_after_refit_down.csv", ("down",))
d2_cmd, d2_meas = load("verify_after_refit_down.csv", ("down-cap",))
up_err = up_meas - up_cmd[:, None]
down_err = np.vstack([d1_meas - d1_cmd[:, None], d2_meas - d2_cmd[:, None]])


def rms(a, axis=None):
    return np.sqrt(np.mean(np.square(a), axis=axis))


print(f"n: up {up_err.size}, down {down_err.size}")
for i, a in enumerate(ARMS):
    print(f"  {a}: up mean {up_err[:, i].mean():+.2f} rms {rms(up_err[:, i]):.2f}"
          f" | down mean {down_err[:, i].mean():+.2f} rms {rms(down_err[:, i]):.2f}")

plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
})
fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.1), sharey=True)
for i, (ax, a) in enumerate(zip(axes, ARMS)):
    ax.plot([-20, 40], [-20, 40], color=INK2, lw=0.8, ls=":", zorder=1, label="Measured = commanded")
    ax.plot(up_cmd, up_meas[:, i], color=UP, lw=1.5, marker="o", ms=4.5, mec="white", mew=0.8,
            label="Up pass (z rising)", zorder=3)
    ax.plot(d1_cmd, d1_meas[:, i], color=DOWN, lw=1.5, marker="s", ms=4.5, mec="white", mew=0.8,
            label="Down pass, run 1 (z falling)", zorder=3)
    ax.plot(d2_cmd, d2_meas[:, i], color=DOWN, lw=1.5, ls="--", marker="s", ms=4.5, mfc="white",
            mec=DOWN, mew=1.1, label="Down pass, run 2 (z falling)", zorder=3)
    ax.set_title(a, fontsize=9, loc="left", color=INK)
    ax.text(0.97, 0.03, f"mean error\n  up   {up_err[:, i].mean():+.1f}°\n  down {down_err[:, i].mean():+.1f}°",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5, color=INK, family="monospace")
    ax.set_xticks([-15, 0, 15, 30])
    ax.set_xlim(-20, 40)
    ax.set_aspect("equal")
    ax.grid(color=GRID, lw=0.6)
axes[0].set_ylim(-20, 40)
axes[0].set_yticks([-15, 0, 15, 30])
axes[0].set_ylabel("Measured bicep angle (°)")
axes[1].set_xlabel("Commanded bicep angle (°, + = down)")
fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=4, frameon=False,
           fontsize=7.5, bbox_to_anchor=(0.5, 1.0))
fig.tight_layout(rect=(0, 0, 1, 0.92))
out = HERE / "figures"
out.mkdir(exist_ok=True)
for ext in ("png", "pdf"):
    fig.savefig(out / f"up_down.{ext}", dpi=300)
print("wrote", out / "up_down.png")
