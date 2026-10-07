"""Tests for FieldTiltScan/stationary_drift.py with the simulated drifting sensor.

    python -m pytest FieldTiltScan/ -v
"""
import csv
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import field_scan_tilt as ft
import stationary_drift as sd


def log(tmp_path, sensor=None, **kw):
    clock = sensor.clock if sensor else ft.VirtualClock()
    sensor = sensor or sd.FakeStillSensor(clock)
    kw.setdefault("duration_s", 1800.0)
    kw.setdefault("interval_s", 10.0)
    p, s = sd.run_log(sensor, "t", out_dir=tmp_path, out=lambda *_: None, clock=clock, **kw)
    return p, list(csv.DictReader(open(p))), json.loads(p.with_suffix(".meta.json").read_text()), s


def test_rows_on_a_fixed_schedule(tmp_path):
    p, rows, meta, _ = log(tmp_path, duration_s=600.0, interval_s=10.0)
    assert list(rows[0].keys()) == sd.CSV_COLUMNS
    assert len(rows) == 61 and meta["rows"] == 61 and not meta["aborted"]
    t = [float(r["t_s"]) for r in rows]
    # each row is stamped after its 20 x 20 ms window; the start times stay on the 10 s grid
    assert all(abs(b - a - 10.0) < 1e-6 for a, b in zip(t, t[1:]))
    assert all(int(r["n_samples"]) == 20 for r in rows)


def test_no_drift_reads_as_no_drift(tmp_path):
    clock = ft.VirtualClock()
    sensor = sd.FakeStillSensor(clock, warmup_G=0.0, drift_G_per_h=0.0)
    _, _, meta, s = log(tmp_path, sensor)
    for a in ("Bx", "By", "Bz"):
        assert abs(s["slope_mG_per_h"][a]) < 0.3       # 0.5 mG noise per reading, 181 rows
        assert s["noise_mG"][a] == pytest.approx(0.5 / math.sqrt(20), rel=0.3)
    assert meta["drift"]["rows"] == 181


def test_steady_drift_is_recovered(tmp_path):
    clock = ft.VirtualClock()
    sensor = sd.FakeStillSensor(clock, warmup_G=0.0, drift_G_per_h=0.010, drift_dir=(1.0, -0.5, 0.3))
    _, _, _, s = log(tmp_path, sensor, duration_s=3600.0)
    assert s["slope_mG_per_h"]["Bx"] == pytest.approx(10.0, abs=0.3)
    assert s["slope_mG_per_h"]["By"] == pytest.approx(-5.0, abs=0.3)
    assert s["slope_mG_per_h"]["Bz"] == pytest.approx(3.0, abs=0.3)
    # last 5 min minus first 5 min: centres 55 min apart
    assert s["change_mG"]["Bx"] == pytest.approx(10.0 * 55 / 60, abs=0.3)


def test_still_sensor_shows_no_tilt_change(tmp_path):
    _, rows, _, s = log(tmp_path)
    assert abs(s["pitch_change_deg"]) < 0.01 and abs(s["roll_change_deg"]) < 0.01
    assert all(abs(math.sqrt(sum(float(r[k]) ** 2 for k in ("ax_g", "ay_g", "az_g"))) - 1) < 2e-3 for r in rows)


def test_ctrl_c_keeps_the_data(tmp_path):
    clock = ft.VirtualClock()
    sensor = sd.FakeStillSensor(clock)
    real = sensor.mag

    def mag():
        if clock.now() > 300:
            raise KeyboardInterrupt
        return real()
    sensor.mag = mag
    p, rows, meta, s = log(tmp_path, sensor, duration_s=0.0)     # 0 = until Ctrl+C
    assert meta["aborted"] and meta["finished"] and 25 <= len(rows) <= 31
    assert s is not None and s["rows"] == len(rows)


def test_rows_without_data_are_nan_and_skipped_in_the_fit(tmp_path):
    clock = ft.VirtualClock()
    sensor = sd.FakeStillSensor(clock)
    real = sensor.samples

    def samples(n, dt_s, clk=None):
        if 95 < clock.now() < 125:      # rows at 100, 110, 120 s
            clock.sleep(n * dt_s)
            return [], [], [], [], []
        return real(n, dt_s, clk)
    sensor.samples = samples
    _, rows, meta, s = log(tmp_path, sensor, duration_s=600.0)
    assert meta["rows_without_data"] == 3 and len(rows) == 61
    assert sum(r["Bx_G"] == "nan" for r in rows) == 3 and s["rows"] == 58


def test_main_simulate(tmp_path, capsys):
    sd.main(["--simulate", "--duration", "5", "--out-dir", str(tmp_path), "--label", "demo"])
    files = list(tmp_path.glob("demo_*.csv"))
    assert len(files) == 1 and "mG/h" in capsys.readouterr().out
