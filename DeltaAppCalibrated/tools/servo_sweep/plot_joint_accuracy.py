"""Joint-angle accuracy and reversal hysteresis after the 2026-09-30 refit.

Reads verify_after_refit_up.csv / verify_after_refit_down.csv (protractor,
positive = bicep down) and prints the summary table, then writes
figures/joint_accuracy.png and .pdf.

    python3 plot_joint_accuracy.py
"""
import csv
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ARMS = ["D9", "D10", "D11"]
COLOURS = ["#2a78d6", "#eb6834", "#1baf7a"]
MARKERS = ["o", "s", "^"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def load(name):
    with open(HERE / name, newline="") as f:
        return list(csv.DictReader(f))


def angles(r, kind):
    return np.array([float(r[f"{kind}_{a}_deg"]) for a in ARMS])


up = load("verify_after_refit_up.csv")
down = load("verify_after_refit_down.csv")

# Joint angle error: every Up-pass point (-730..-590); the -740 lead-in was
# approached downward from Home, so it isn't part of the Up pass.
up_pts = [r for r in up if r["pass"] == "up"]
cmd = np.array([angles(r, "cmd") for r in up_pts])
err = np.array([angles(r, "meas") for r in up_pts]) - cmd
lead = [r for r in up if r["pass"] == "lead-in"][0]
lead_cmd, lead_err = angles(lead, "cmd"), angles(lead, "meas") - angles(lead, "cmd")

# Reversal hysteresis: Up-pass reading minus Down-pass reading at the same z.
# Both Down runs ("down", "down-cap"); the cap run's last row moved back UP.
up_at = {float(r["probe_z_mm"]): angles(r, "meas") for r in up_pts}
pairs = [(r["pass"], float(r["probe_z_mm"]), up_at[float(r["probe_z_mm"])] - angles(r, "meas"))
         for r in down
         if r["pass"] in ("down", "down-cap") and not r["note"]
         and float(r["probe_z_mm"]) in up_at]
hyst = np.array([p[2] for p in pairs])


def rms(a, axis=None):
    return np.sqrt(np.mean(np.square(a), axis=axis))


print(f"Joint angle error, Up pass -730..-590: n = {err.size} ({len(up_pts)} points x 3 arms)")
print(f"  all arms rms {rms(err):.2f} deg, max |err| {np.abs(err).max():.2f} deg")
for a, r_, m in zip(ARMS, rms(err, 0), np.abs(err).max(0)):
    print(f"  {a}: rms {r_:.2f}, max {m:.2f}")
e2 = err[1:]
print(f"  excluding -730 (first step after reversal): n = {e2.size}, rms {rms(e2):.2f} deg")
print(f"Reversal hysteresis (up - down), z = {sorted({p[1] for p in pairs})}: n = {hyst.size} ({len(pairs)} pairs x 3 arms)")
for a, col in zip(ARMS, hyst.T):
    print(f"  {a}: mean {col.mean():+.2f} deg, range {col.min():+.1f} .. {col.max():+.1f}")
print(f"  mean |hysteresis| all arms {np.abs(hyst).mean():.2f} deg; excl. D10 {np.abs(hyst[:, [0, 2]]).mean():.2f} deg")

# ---- figure -----------------------------------------------------------------
plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.1), gridspec_kw={"width_ratios": [1.6, 1]})

ax1.axhspan(-0.5, 0.5, color="#f0efec", zorder=0, lw=0)
ax1.axhline(0, color=INK2, lw=0.8, zorder=1)
for i, a in enumerate(ARMS):
    order = np.argsort(cmd[:, i])
    ax1.plot(cmd[order, i], err[order, i], color=COLOURS[i], lw=1.5, marker=MARKERS[i], ms=5,
             mec="white", mew=0.8, label=a, zorder=3)
    ax1.plot(lead_cmd[i], lead_err[i], ls="none", marker=MARKERS[i], ms=5, mfc="none",
             mec=COLOURS[i], mew=1.2, zorder=3)
ax1.annotate("−740 lead-in, approached\ndownward (excluded)", xy=(lead_cmd[1], lead_err[1]),
             xytext=(22, 3.6), fontsize=7.5, color=INK2, ha="right", va="center",
             arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
ax1.text(-11, 0.62, "±0.5° target", fontsize=7.5, color=INK2, va="bottom")
ax1.set_xlabel("Commanded bicep angle (°, + = down)")
ax1.set_ylabel("Measured − commanded (°)")
ax1.set_title("(a) Joint angle error, on-axis Up pass", fontsize=9, loc="left", color=INK)
ax1.set_ylim(-1.5, 5)
ax1.grid(axis="y", color=GRID, lw=0.6)
ax1.legend(frameon=False, fontsize=8, loc="upper left", ncol=3)

ax2.axhline(0, color=INK2, lw=0.8)
rng = np.random.default_rng(0)
for i, a in enumerate(ARMS):
    x = i + rng.uniform(-0.12, 0.12, len(hyst))
    ax2.plot(x, hyst[:, i], ls="none", marker=MARKERS[i], ms=5, color=COLOURS[i], mec="white", mew=0.8)
    m = hyst[:, i].mean()
    ax2.plot([i - 0.25, i + 0.25], [m, m], color=INK, lw=1.5)
    ax2.text(i + 0.3, m, f"{m:+.1f}°", va="center", fontsize=7.5, color=INK)
ax2.set_xticks(range(3), ARMS)
ax2.set_xlim(-0.5, 2.8)
ax2.set_ylabel("Up − Down at same z (°)")
ax2.set_title("(b) Reversal hysteresis", fontsize=9, loc="left", color=INK)
ax2.grid(axis="y", color=GRID, lw=0.6)

fig.tight_layout()
out = HERE / "figures"
out.mkdir(exist_ok=True)
for ext in ("png", "pdf"):
    fig.savefig(out / f"joint_accuracy.{ext}", dpi=300)
print("wrote", out / "joint_accuracy.png")
