"""Fig 1: system architecture block diagram. Writes fig01_architecture.png/.svg/.pdf
next to this script. Values are from DeltaAppCalibrated/delta_servo/config.h
(pins, L_UP, L_LO, SP, STREAM_MS), delta_app/robot_config.py (TCP) and FieldScan/HANDOFF.md;
servo supply is a 5 V / 5 A bench PSU (replaced the 6 V AA pack)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

OUT = Path(__file__).resolve().parent / "fig01_architecture"

ink, muted, line = "#2b2b29", "#6b6a66", "#9a9893"
act_fill, act_edge = "#fbf1e4", "#c98a3c"     # actuator zone (warm)
vol_fill, vol_edge = "#e8f1fc", "#256abf"     # measured volume (blue)
box_fill = "#ffffff"
sig, pwr, mech = "#256abf", "#b8302f", "#6b6a66"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 6.4, "text.color": ink})

W, H = 226, 146
fig, ax = plt.subplots(figsize=(W / 25.4, H / 25.4))
ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.axis("off")


def zone(x0, y0, x1, y1, fill, edge, title, sub):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=3",
                                fc=fill, ec=edge, lw=1.2, ls=(0, (5, 2.5))))
    ax.text(x0 + 3, y1 - 3, title, ha="left", va="top", fontsize=7.2, weight="bold", color=edge)
    ax.text(x0 + 3, y1 - 7.4, sub, ha="left", va="top", fontsize=5.8, color=muted)


def box(x0, y0, x1, y1, title, sub=None, edge=ink):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=1.5",
                                fc=box_fill, ec=edge, lw=1.0))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    lines = sub.split("\n") if sub else []
    lh = 3.1                                   # line pitch, data units
    top = cy + lh * len(lines) / 2 + (0.5 if lines else 0)
    ax.text(cx, top, title, ha="center", va="center", weight="bold", color=edge)
    for i, s in enumerate(lines):
        ax.text(cx, top - 1.0 - lh * (i + 1), s, ha="center", va="center", fontsize=5.6, color=muted)


def arrow(pts, color, style="-|>", lw=1.3, ls="-"):
    for i, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
        last = i == len(pts) - 2
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style if last else "-", mutation_scale=9,
                                     color=color, lw=lw, ls=ls, shrinkA=0, shrinkB=0,
                                     capstyle="butt", joinstyle="miter"))


def label(x, y, s, color, ha="center", va="bottom", **kw):
    ax.text(x, y, s, ha=ha, va=va, fontsize=5.6, color=color, linespacing=1.25, **kw)


# Zones
zone(22, 86, 156, 142, act_fill, act_edge, "ACTUATOR ZONE: above the coil",
     "frame-mounted, kept ≥600 mm from the probe")
zone(22, 4, 156, 76, vol_fill, vol_edge, "MEASURED VOLUME: inside the Helmholtz coil",
     "non-magnetic parts only (PLA, carbon fibre, aluminium, nylon)")

# Mechanical chain (centre column)
cx0, cx1 = 27, 88
cx = (cx0 + cx1) / 2
box(cx0, 104, cx1, 128, "3 × hobby servos", "arm 1 on D9 · arm 2 on D10 · arm 3 on D11\nservo axis = robot base plane")
box(cx0, 89, cx1, 98, "3 × biceps, 177 mm")
box(cx0, 53, cx1, 63, "3 × forearms, 625 mm", "ball-jointed parallelograms")
box(cx0, 39, cx1, 47, "Effector platform", "75 mm ball-joint triangle")
box(cx0, 26, cx1, 33, "Probe holder (PLA)")
box(cx0, 8, cx1, 20, "Phidget 1044 probe", "3-axis magnetometer + accel + gyro\nTCP 21 mm below platform", edge=vol_edge)
for ya, yb in [(104, 98), (89, 63), (53, 47), (39, 33), (26, 20)]:
    ax.plot([cx, cx], [ya, yb], color=mech, lw=3.2, solid_capstyle="butt", zorder=0)

# Electronics (right of the column, upper zone)
ex0, ex1 = 102, 152
box(ex0, 113, ex1, 131, "Arduino UNO R4 Minima", "IK · motion planner · protocol\n(no WiFi: no RF near probe)")
box(ex0, 92, ex1, 104, "5 V bench PSU", "5 V / 5 A, servo supply only")

# Host PC (outside both zones)
px0, px1 = 186, 222
box(px0, 98, px1, 134, "Host PC (macOS)", "pyserial + Phidget22\nfield_scan.py\nfield_scan_tilt.py\nGUI: main.py\nMATLAB fallback scan")

# Signal links
arrow([(px0, 127), (ex1, 127)], sig)                          # commands PC -> Arduino
label((px0 + ex1) / 2, 128, "USB serial\nmode byte + JSON\n<m><{…}><#>", sig)
arrow([(ex1, 117), (px0, 117)], sig)                          # status Arduino -> PC
label((px0 + ex1) / 2, 116, "status JSON\nevery 20 ms\n{deg, mv, run,\nen, e}", sig, va="top")
arrow([(ex0, 121), (cx1, 121)], sig)                          # PWM
label((ex0 + cx1) / 2, 122, "PWM\nD9–D11", sig)
arrow([(ex0, 98), (95, 98), (95, 109), (cx1, 109)], pwr)     # servo power
label(93.5, 101, "5 V", pwr, ha="right")
arrow([((px0 + px1) / 2, 98), ((px0 + px1) / 2, 14), (cx1, 14)], sig)   # Phidget22 USB
label(128, 15, "Phidget22 over USB\nB, accel, gyro, pitch/roll", sig)

# ≥600 mm actuator-to-probe dimension
dx = 12
for y, x in [(116, cx0), (14, cx0)]:
    ax.plot([dx - 3, x], [y, y], color=ink, lw=0.6, ls=(0, (2, 1.5)))
ax.add_patch(FancyArrowPatch((dx, 116), (dx, 14), arrowstyle="<|-|>", mutation_scale=8, color=ink, lw=0.9))
ax.text(dx - 2.2, 65, "≥ 600 mm   servo axis → probe", rotation=90, ha="right", va="center",
        fontsize=6.2, weight="bold")

# Legend
lx, ly = 162, 50
for i, (c, w, s) in enumerate([(sig, 1.3, "data / signal"), (pwr, 1.3, "power"), (mech, 3.2, "mechanical link")]):
    yy = ly - i * 6
    ax.plot([lx, lx + 8], [yy, yy], color=c, lw=w, solid_capstyle="butt")
    ax.text(lx + 10, yy, s, va="center", fontsize=5.6, color=muted)

for ext in ("png", "svg", "pdf"):
    fig.savefig(f"{OUT}.{ext}", dpi=300, bbox_inches="tight", pad_inches=0.04, facecolor="white")
print("wrote", OUT)
