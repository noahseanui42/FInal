"""Log the 1044 at one fixed point over time, without moving the robot.

Used to find where the field drift seen in the 6 Oct repeat test comes from
(REPEAT_TEST.md: about 1 uT per hour, mostly in Bx, not explained by tilt).
Park the probe first (e.g. a one-point scan with field_scan_tilt.py, which leaves the
robot enabled at the park position), then log:

    python FieldTiltScan/log_fixed_point.py --label drift_servos-on  --minutes 30
    # switch the servo supply off, arms supported so the probe doesn't move, then:
    python FieldTiltScan/log_fixed_point.py --label drift_servos-off --minutes 30
    python FieldTiltScan/log_fixed_point.py --simulate --minutes 1 --every 5   # no hardware

If the drift continues with the servos off, it is the sensor; if it stops or
reverses, it is the servo motors warming or cooling.

Each row averages --n-avg Spatial events (field, acceleration, gyro, pitch/roll),
the same reading as a scan point. Rows are written as they are measured, so Ctrl+C
keeps everything logged so far. A .meta.json records the settings.
"""
import argparse
import csv
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import field_scan_tilt as fst  # noqa: E402

COLUMNS = ["i", "t_s", "Bx_G", "By_G", "Bz_G", "Bx_std_G", "By_std_G", "Bz_std_G", "n_samples",
           "ax_g", "ay_g", "az_g", "gyro_rms_dps", "pitch_deg", "roll_deg",
           "acc_pitch_deg", "acc_roll_deg", "reconnected"]


class _StillSensor:
    """--simulate: a still probe whose field drifts slowly in x (about 1 uT per hour)."""

    def __init__(self, clock):
        self.clock, self.t0 = clock, clock.now()

    def samples(self, n, dt_s, clock=None):
        B, A, W, E, T = [], [], [], [], []
        for _ in range(n):
            t = self.clock.now() - self.t0
            B.append((0.006 + 0.01 * t / 3600.0, -0.18, 0.77))
            A.append((0.017, -0.009, 1.0))
            W.append((0.0, 0.0, 0.0))
            E.append((1.0, -0.5))
            T.append(t * 1000.0)
            self.clock.sleep(dt_s)
        return B, A, W, E, T

    def take_reattaches(self):
        return 0

    def close(self):
        pass


def log(sensor, out_csv, minutes, every_s, n_avg, dt_s, clock, echo=print):
    """Read one averaged point every every_s seconds for minutes; return the number of rows."""
    t0 = clock.now()
    rows = 0
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        while True:
            t = clock.now() - t0
            if t > minutes * 60:
                break
            r = fst.read_point(sensor, n_avg, dt_s, clock)
            rc = sensor.take_reattaches() if hasattr(sensor, "take_reattaches") else 0
            w.writerow([rows, f"{t:.1f}", *(f"{v:.6f}" for v in r["B"]), *(f"{v:.6f}" for v in r["Bsd"]),
                        r["n"], *(f"{v:.5f}" for v in r["a"]), f"{r['g_rms']:.4f}",
                        f"{r['pitch']:.4f}", f"{r['roll']:.4f}",
                        *(f"{v:.4f}" for v in r["acc_pr"]), rc])
            f.flush()
            bx, by, bz = r["B"]
            echo(f"{t / 60:6.1f} min  B = ({bx:+.4f}, {by:+.4f}, {bz:+.4f}) G  |B| = {math.sqrt(bx*bx + by*by + bz*bz):.4f}")
            rows += 1
            nxt = t0 + rows * every_s
            while clock.now() < nxt:
                clock.sleep(min(0.5, nxt - clock.now()))
    return rows


def main(argv=None):
    cfg = fst.TiltScanConfig()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", default="fixed_point")
    ap.add_argument("--minutes", type=float, default=30.0)
    ap.add_argument("--every", type=float, default=20.0, help="seconds between readings")
    ap.add_argument("--n-avg", type=int, default=cfg.n_avg)
    ap.add_argument("--note", default="", help="free text stored in the metadata, e.g. 'servos on, cold start'")
    ap.add_argument("--mag-serial", type=int, default=cfg.mag_serial)
    ap.add_argument("--algorithm", default=cfg.algorithm)
    ap.add_argument("--out-dir", default=cfg.out_dir)
    ap.add_argument("--simulate", action="store_true", help="no hardware")
    a = ap.parse_args(argv)

    if a.simulate:
        clock = fst.VirtualClock()
        sensor = _StillSensor(clock)
    else:
        clock = fst.Clock
        sensor = fst.Phidget1044Spatial(a.mag_serial, cfg.sample_dt_s, a.algorithm)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out / f"{a.label}_{stamp}.csv"
    meta = {"label": a.label, "note": a.note, "started": datetime.now().isoformat(timespec="seconds"),
            "minutes": a.minutes, "every_s": a.every, "n_avg": a.n_avg, "sample_dt_s": cfg.sample_dt_s,
            "mag_serial": a.mag_serial, "simulated": a.simulate, "script": "log_fixed_point.py"}
    print(f"Logging to {path} for {a.minutes:g} min, one reading every {a.every:g} s. Ctrl+C to stop early.")
    try:
        meta["rows"] = log(sensor, path, a.minutes, a.every, a.n_avg, cfg.sample_dt_s, clock)
    except KeyboardInterrupt:
        meta["stopped_early"] = True
        print("\nStopped; rows so far are saved.")
    finally:
        meta["finished"] = datetime.now().isoformat(timespec="seconds")
        path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2))
        sensor.close()


if __name__ == "__main__":
    main()
