"""python -m pytest FieldTiltScan/test_log_fixed_point.py"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import field_scan_tilt as fst  # noqa: E402
import log_fixed_point as lfp  # noqa: E402


def test_log_writes_one_row_per_interval(tmp_path):
    clock = fst.VirtualClock()
    sensor = lfp._StillSensor(clock)
    out = tmp_path / "log.csv"
    n = lfp.log(sensor, out, minutes=1.0, every_s=20.0, n_avg=5, dt_s=0.02, clock=clock, echo=lambda *_: None)
    rows = list(csv.DictReader(open(out)))
    assert n == len(rows) == 4                      # t = 0, 20, 40, 60 s
    assert [float(r["t_s"]) for r in rows] == [0.0, 20.0, 40.0, 60.0]
    assert float(rows[-1]["Bx_G"]) > float(rows[0]["Bx_G"])     # the simulated drift shows up
    assert set(lfp.COLUMNS) == set(rows[0])


def test_main_simulate_writes_meta(tmp_path):
    lfp.main(["--simulate", "--minutes", "0.5", "--every", "10", "--out-dir", str(tmp_path), "--label", "t"])
    assert len(list(tmp_path.glob("t_*.csv"))) == 1
    assert len(list(tmp_path.glob("t_*.meta.json"))) == 1
