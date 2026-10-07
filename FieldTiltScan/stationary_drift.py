"""Stationary drift test: log the 1044 at one fixed spot for a long time, to see whether
the field reading drifts with nothing moving.

    python FieldTiltScan/stationary_drift.py --label drift-robot-off --magnet underneath --note "servos unpowered"
    python FieldTiltScan/stationary_drift.py --duration 90 --interval 10      # 90 min, a row every 10 s
    python FieldTiltScan/stationary_drift.py --duration 0                     # until Ctrl+C
    python FieldTiltScan/stationary_drift.py --simulate --duration 30         # no hardware

Only the 1044 is opened; the robot is not connected, so this works with the servos
off (support the arms so the probe can't move) or with the delta app holding the robot.
The sensor is read the same way as a scan point in field_scan_tilt.py: every
--interval seconds, n_avg Spatial events (20 x 20 ms by default) are averaged into one
row of field, acceleration, gyro and pitch/roll. Rows are written as they are taken,
so Ctrl+C keeps everything so far. At the end it prints the drift: a straight-line fit
per axis in mG/h, the change from the first to the last few minutes, and the change
in tilt over the same time (a tilt change rotates the field, so it is a drift source).

Start it as soon as the sensor is powered: the warm-up is part of what is measured.
On a Mac, run it under `caffeinate -i` so the laptop doesn't sleep.

CSV columns (field in gauss, SENSOR axes, as in field_scan_tilt.py):
    idx, t_s, time              row number, seconds since the start, wall-clock time
    Bx_G, By_G, Bz_G            mean field
    Bx_std_G, By_std_G, Bz_std_G  std over the samples
    B_G                         |B|
    n_samples                   field readings averaged
    ax_g .. az_g, ax_std_g .. az_std_g, gyro_rms_dps, gyro_max_dps, pitch_deg, roll_deg,
    acc_pitch_deg, acc_roll_deg, spatial_t_first_ms, spatial_t_last_ms
                                as in field_scan_tilt.py
"""

import argparse
import csv
import json
import math
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import field_scan_tilt as ft   # noqa: E402  (sensor and per-point reading, reused unchanged)
fs = ft.fs

CSV_COLUMNS = [
    "idx", "t_s", "time", "Bx_G", "By_G", "Bz_G", "Bx_std_G", "By_std_G", "Bz_std_G", "B_G",
    "n_samples", "ax_g", "ay_g", "az_g", "ax_std_g", "ay_std_g", "az_std_g",
    "gyro_rms_dps", "gyro_max_dps", "pitch_deg", "roll_deg", "acc_pitch_deg", "acc_roll_deg",
    "spatial_t_first_ms", "spatial_t_last_ms",
]


# --------------------------------------------------------------------------
# Drift summary
# --------------------------------------------------------------------------
def _slope(t, y):
    """Least-squares slope of y against t, or NaN with fewer than 2 points."""
    pts = [(a, b) for a, b in zip(t, y) if math.isfinite(b)]
    if len(pts) < 2:
        return math.nan
    tm = statistics.fmean(a for a, _ in pts)
    ym = statistics.fmean(b for _, b in pts)
    stt = sum((a - tm) ** 2 for a, _ in pts)
    return sum((a - tm) * (b - ym) for a, b in pts) / stt if stt else math.nan


def _window_mean(t, y, lo, hi):
    v = [b for a, b in zip(t, y) if lo <= a <= hi and math.isfinite(b)]
    return statistics.fmean(v) if v else math.nan


def drift_summary(rows, window_s=300.0):
    """rows: dicts with t_s, B (3), Bsd (3), n, pitch, roll, acc_pr. Returns a dict:
    slope_mG_per_h (x, y, z, |B|), change_mG (mean of the last window minus the first),
    noise_mG (median standard error of one row), scatter_mG (row-to-row std about the
    fitted line), tilt change in deg (board filter, or from acceleration if no filter)."""
    t = [r["t_s"] for r in rows]
    if len(rows) < 2:
        return None
    window_s = min(window_s, (t[-1] - t[0]) / 2)
    comps = [[r["B"][i] for r in rows] for i in range(3)]
    comps.append([ft._norm(r["B"]) for r in rows])
    th = [x / 3600.0 for x in t]
    slope = [_slope(th, c) * 1000.0 for c in comps]
    change = [(_window_mean(t, c, t[-1] - window_s, t[-1]) - _window_mean(t, c, t[0], t[0] + window_s)) * 1000.0
              for c in comps]
    scatter = []
    for c, s in zip(comps, slope):
        tm, cm = statistics.fmean(th), statistics.fmean(c)
        res = [y - (cm + s / 1000.0 * (x - tm)) for x, y in zip(th, c)]
        scatter.append(statistics.stdev(res) * 1000.0 if len(res) > 2 else math.nan)
    noise = [statistics.median(r["Bsd"][i] / math.sqrt(r["n"]) for r in rows if r["n"] > 0) * 1000.0
             for i in range(3)]
    use_filter = all(math.isfinite(r["pitch"]) for r in rows)
    pitch = [r["pitch"] if use_filter else r["acc_pr"][0] for r in rows]
    roll = [r["roll"] if use_filter else r["acc_pr"][1] for r in rows]
    return {
        "duration_s": t[-1] - t[0], "rows": len(rows), "window_s": window_s,
        "slope_mG_per_h": dict(zip(("Bx", "By", "Bz", "B"), slope)),
        "change_mG": dict(zip(("Bx", "By", "Bz", "B"), change)),
        "noise_mG": dict(zip(("Bx", "By", "Bz"), noise)),
        "scatter_mG": dict(zip(("Bx", "By", "Bz", "B"), scatter)),
        "tilt_from": "board filter" if use_filter else "acceleration",
        "pitch_change_deg": _window_mean(t, pitch, t[-1] - window_s, t[-1]) - _window_mean(t, pitch, t[0], t[0] + window_s),
        "roll_change_deg": _window_mean(t, roll, t[-1] - window_s, t[-1]) - _window_mean(t, roll, t[0], t[0] + window_s),
    }


def format_summary(s):
    if s is None:
        return "Not enough rows for a drift estimate."
    ax = ("Bx", "By", "Bz", "B")
    lines = [
        f"Drift over {s['duration_s'] / 60:.1f} min ({s['rows']} rows):",
        "            " + "".join(f"{a:>9}" for a in ("Bx", "By", "Bz", "|B|")),
        "  slope     " + "".join(f"{s['slope_mG_per_h'][a]:9.2f}" for a in ax) + "  mG/h (straight-line fit)",
        "  change    " + "".join(f"{s['change_mG'][a]:9.2f}" for a in ax)
        + f"  mG (last {s['window_s'] / 60:.0f} min minus first {s['window_s'] / 60:.0f} min)",
        "  scatter   " + "".join(f"{s['scatter_mG'][a]:9.2f}" for a in ax) + "  mG (row-to-row, about the fit)",
        "  noise     " + "".join(f"{s['noise_mG'][a]:9.2f}" for a in ax[:3]) + "           mG (one row's standard error)",
        f"  tilt change: pitch {s['pitch_change_deg']:+.3f} deg, roll {s['roll_change_deg']:+.3f} deg ({s['tilt_from']})",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------
def run_log(sensor, label="drift", magnet="", note="", duration_s=3600.0, interval_s=10.0,
            n_avg=20, sample_dt_s=0.02, zero_gyro=True, out_dir=HERE / "data",
            out=print, clock=ft.Clock, settings=None):
    """Read the sensor every interval_s for duration_s (0 = until Ctrl+C) and write a CSV
    and .meta.json. Returns (csv path, drift summary dict)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now()
    stamp = started.strftime("%Y%m%d_%H%M%S")
    slug = ft.magnet_slug(magnet)
    csv_path = out_dir / (f"{label}_{slug}_{stamp}.csv" if slug else f"{label}_{stamp}.csv")
    meta_path = csv_path.with_suffix(".meta.json")

    gyro_zeroed = False
    if zero_gyro:
        out("Zeroing the gyro (keep the sensor still)...")
        sensor.zero_gyro(clock)
        gyro_zeroed = True

    meta = {
        "label": label, "magnet": magnet, "note": note, "test": "stationary drift",
        "started": started.isoformat(timespec="seconds"), "csv": csv_path.name,
        "script": "FieldTiltScan/stationary_drift.py",
        "frame": "sensor axes, raw: B in gauss, acceleration in g, angular rate in deg/s, pitch/roll in deg",
        "robot": "not connected by this script",
        "settings": dict(settings or {}, duration_s=duration_s, interval_s=interval_s, n_avg=n_avg,
                         sample_dt_s=sample_dt_s, gyro_zeroed=gyro_zeroed),
        "sensor": sensor.info() if hasattr(sensor, "info") else {},
        "finished": None, "rows": 0, "aborted": False, "rows_without_data": 0,
        "sensor_reconnected_at_rows": [], "drift": None,
    }

    def write_meta():
        meta_path.write_text(json.dumps(meta, indent=2))

    t0 = clock.now()
    meta["spatial_timestamp_at_t0_ms"] = (sensor.latest_timestamp()
                                          if hasattr(sensor, "latest_timestamp") else None)
    write_meta()
    rows, n_empty, k = [], 0, 0
    try:
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(CSV_COLUMNS)
            f.flush()
            out(f"Logging every {interval_s:g} s "
                + (f"for {duration_s / 60:g} min" if duration_s > 0 else "until Ctrl+C")
                + f" -> {csv_path}")
            while duration_s <= 0 or k * interval_s <= duration_s:
                wait = t0 + k * interval_s - clock.now()     # fixed schedule: no creep from read time
                if wait > 0:
                    clock.sleep(wait)
                k += 1
                r = ft.read_point(sensor, n_avg, sample_dt_s, clock)
                t = clock.now() - t0
                if getattr(sensor, "take_reattaches", lambda: 0)():
                    meta["sensor_reconnected_at_rows"].append(k)
                    out(f"  WARNING: the 1044 reconnected before row {k}; data rate restored, "
                        "gyro zero lost (gyro columns biased from here; field is fine)")
                if r["n"] == 0:
                    n_empty += 1
                    out(f"  row {k}: no data from the 1044 (USB?); logged as NaN")
                else:
                    rows.append({"t_s": t, "B": r["B"], "Bsd": r["Bsd"], "n": r["n"],
                                 "pitch": r["pitch"], "roll": r["roll"], "acc_pr": r["acc_pr"]})
                B = r["B"]
                w.writerow([k, f"{t:.2f}", (started + timedelta(seconds=t)).isoformat(timespec="seconds"),
                            *(f"{v:.6f}" for v in B), *(f"{v:.6f}" for v in r["Bsd"]),
                            f"{ft._norm(B):.6f}", r["n"],
                            *(f"{v:.6f}" for v in r["a"]), *(f"{v:.6f}" for v in r["asd"]),
                            f"{r['g_rms']:.4f}", f"{r['g_max']:.4f}",
                            f"{r['pitch']:.4f}", f"{r['roll']:.4f}",
                            *(f"{v:.4f}" for v in r["acc_pr"]),
                            *(f"{v:.3f}" for v in r["ts"])])
                f.flush()
                meta["rows"] = k
                if rows and r["n"]:
                    d = [(b - b0) * 1000.0 for b, b0 in zip(B, rows[0]["B"])]
                    pr = (r["pitch"], r["roll"]) if math.isfinite(r["pitch"]) else r["acc_pr"]
                    out(f"{k:5d}  {t / 60:6.1f} min  B = [{B[0]:8.5f} {B[1]:8.5f} {B[2]:8.5f}] G  "
                        f"change from row 1 = [{d[0]:+6.2f} {d[1]:+6.2f} {d[2]:+6.2f}] mG  "
                        f"pitch {pr[0]:7.3f}  roll {pr[1]:7.3f} deg  gyro {r['g_rms']:.2f} deg/s")
    except KeyboardInterrupt:
        meta["aborted"] = True
        out("Stopped; data so far is saved.")
    finally:
        summary = drift_summary(rows)
        meta["rows_without_data"] = n_empty
        meta["drift"] = summary
        meta["finished"] = datetime.now().isoformat(timespec="seconds")
        write_meta()
    out(format_summary(summary))
    return csv_path, summary


# --------------------------------------------------------------------------
# Simulated sensor (for --simulate and tests)
# --------------------------------------------------------------------------
class FakeStillSensor(ft.FakeTiltSensor):
    """A still 1044 whose field reading drifts: a warm-up step that settles with time
    constant warmup_tau_s, plus a steady drift_G_per_h, both added to every axis
    in the ratio drift_dir."""

    def __init__(self, clock, warmup_G=0.004, warmup_tau_s=900.0, drift_G_per_h=0.002,
                 drift_dir=(1.0, -0.5, 0.3), **kw):
        super().__init__(SimpleNamespace(pos=None), clock, ring_dps=0.0, **kw)
        self.warmup, self.tau, self.rate, self.dir = warmup_G, warmup_tau_s, drift_G_per_h, drift_dir

    def offset(self):
        t = self.clock.now()
        return self.warmup * (1 - math.exp(-t / self.tau)) + self.rate * t / 3600.0

    def mag(self):
        o = self.offset()
        return tuple(b + o * d for b, d in zip(super().mag(), self.dir))

    def info(self):
        return {"serial": 0, "name": "simulated (still, drifting)"}


# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--label", default="drift", help="start of the file name, e.g. drift-robot-off")
    ap.add_argument("--magnet", default="",
                    help="where the magnet is, e.g. 'underneath' or 'none'; goes in the file name and metadata")
    ap.add_argument("--note", default="",
                    help="free text stored in the metadata, e.g. 'servos unpowered, probe on PLA block, 21 C'")
    ap.add_argument("--duration", type=float, default=60.0, help="minutes to log; 0 = until Ctrl+C (default 60)")
    ap.add_argument("--interval", type=float, default=10.0, help="seconds between rows (default 10)")
    ap.add_argument("--n-avg", type=int, default=20, help="readings averaged per row (default 20)")
    ap.add_argument("--sample-dt", type=float, default=0.02, help="1044 data interval, s (default 0.02)")
    ap.add_argument("--no-zero-gyro", action="store_true", help="don't zero the gyro at the start")
    ap.add_argument("--algorithm", choices=ft.ALGORITHMS, default="imu",
                    help="board's orientation filter for pitch/roll (default imu)")
    ap.add_argument("--mag-serial", type=int, default=0, help="1044 serial number (0 = any)")
    ap.add_argument("--out-dir", default=str(HERE / "data"))
    ap.add_argument("--simulate", action="store_true", help="fake drifting sensor, no hardware")
    a = ap.parse_args(argv)
    if a.interval <= a.n_avg * a.sample_dt:
        sys.exit(f"ERROR: --interval {a.interval:g} s is shorter than one reading "
                 f"({a.n_avg} x {a.sample_dt:g} s).")

    if a.simulate:
        clock = ft.VirtualClock()
        sensor = FakeStillSensor(clock)
    else:
        clock = ft.Clock
        try:
            sensor = ft.Phidget1044Spatial(a.mag_serial, a.sample_dt, a.algorithm)
        except Exception as e:
            sys.exit(f"ERROR: could not open the 1044: {e}")
    try:
        run_log(sensor, a.label, a.magnet, a.note, a.duration * 60.0, a.interval, a.n_avg, a.sample_dt,
                zero_gyro=not a.no_zero_gyro, out_dir=a.out_dir, clock=clock,
                settings={"algorithm": a.algorithm, "mag_serial": a.mag_serial, "simulate": a.simulate})
    finally:
        sensor.close()


if __name__ == "__main__":
    main()
