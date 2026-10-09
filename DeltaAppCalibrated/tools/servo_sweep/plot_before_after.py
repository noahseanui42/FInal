"""Joint-angle error before and after the 2026-09-30 refit, on-axis Up pass.

Before: sweep_2026-09-30_up.csv (old CAL[]: D9 1460 / 11.8231, D10 1350 /
9.51, D11 1410 / 10.5544). After: verify_after_refit_up.csv (refit CAL[]).
Both exclude the -740 lead-in, which was approached downward from Home.
Writes figures/before_after.png and .pdf.

    python3 plot_before_after.py
"""
import csv
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ARMS = ["D9", "D10", "D11"]
BEFORE, AFTER = "#8a8984", "#2a78d6"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def load(name):
    with open(HERE / name, newline="") as f:
        return [r for r in csv.DictReader(f) if r["pass"] == "up"]


before = load("sweep_2026-09-30_up.csv")
after = load("verify_after_refit_up.csv")
b_cmd = np.array([float(r["cmd_deg"]) for r in before])
b_err = np.array([[float(r[f"meas_{a}_deg"]) for a in ARMS] for r in before]) - b_cmd[:, None]
a_cmd = np.array([float(r["cmd_D9_deg"]) for r in after])
a_err = np.array([[float(r[f"meas_{a}_deg"]) for a in ARMS] for r in after]) - a_cmd[:, None]


def rms(a, axis=None):
    return np.sqrt(np.mean(np.square(a), axis=axis))


print(f"n = {b_err.size} before, {a_err.size} after")
print(f"all arms rms: before {rms(b_err):.2f} deg, after {rms(a_err):.2f} deg")
for i, a in enumerate(ARMS):
    print(f"  {a}: before rms {rms(b_err[:, i]):.2f} max {np.abs(b_err[:, i]).max():.2f}"
          f" | after rms {rms(a_err[:, i]):.2f} max {np.abs(a_err[:, i]).max():.2f}")

plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
})
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.9), sharey=True)
for i, (ax, a) in enumerate(zip(axes, ARMS)):
    ax.axhspan(-0.5, 0.5, color="#f0efec", zorder=0, lw=0)
    ax.axhline(0, color=INK2, lw=0.8, zorder=1)
    ax.plot(b_cmd, b_err[:, i], color=BEFORE, lw=1.5, ls="--", marker="o", ms=4.5,
            mfc="white", mec=BEFORE, mew=1.1, label="Before refit", zorder=2)
    ax.plot(a_cmd, a_err[:, i], color=AFTER, lw=1.5, marker="o", ms=4.5,
            mec="white", mew=0.8, label="After refit", zorder=3)
    ax.set_title(f"{a}", fontsize=9, loc="left", color=INK)
    ax.text(0.03, 0.97, f"rms {rms(b_err[:, i]):.1f}° → {rms(a_err[:, i]):.1f}°",
            transform=ax.transAxes, ha="left", va="top", fontsize=8, color=INK)
    ax.set_xticks([-10, 0, 10, 20, 30])
    ax.grid(axis="y", color=GRID, lw=0.6)
axes[0].set_ylim(-4.6, 8)
axes[0].set_ylabel("Measured − commanded (°)")
axes[1].set_xlabel("Commanded bicep angle (°, + = down)")
axes[0].text(-10, 0.6, "±0.5°", fontsize=7.5, color=INK2, va="bottom")
fig.legend(*axes[0].get_legend_handles_labels(), loc="upper right", ncol=2, frameon=False,
           fontsize=8, bbox_to_anchor=(1.0, 1.0))
fig.tight_layout(rect=(0, 0, 1, 0.93))
out = HERE / "figures"
out.mkdir(exist_ok=True)
for ext in ("png", "pdf"):
    fig.savefig(out / f"before_after.{ext}", dpi=300)
print("wrote", out / "before_after.png")
