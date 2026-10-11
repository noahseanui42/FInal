"""Sign/size of the drift a tilt change would predict (repeat test), and tilt-correction size for the first tilt run."""
import csv, glob
import numpy as np, pandas as pd
T = 'FieldTiltScan/data/'
fs = sorted(glob.glob(T + 'repeat_under-run*.csv'))
d1, d5 = pd.read_csv(fs[0]), pd.read_csv(fs[4])
unit = lambda v: v / np.linalg.norm(v, axis=1)[:, None]
g1, g5 = unit(d1[['ax_g', 'ay_g', 'az_g']].values), unit(d5[['ax_g', 'ay_g', 'az_g']].values)
B1, B5 = d1[['Bx_G', 'By_G', 'Bz_G']].values * 1e5, d5[['Bx_G', 'By_G', 'Bz_G']].values * 1e5
def rot(a, b):
    v = np.cross(a, b); s = np.linalg.norm(v); c = a @ b
    if s < 1e-12:
        return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s**2)
pred = np.array([rot(a, b) @ B for a, b, B in zip(g1, g5, B1)]) - B1
obs = (B5 - B1).mean(0); pm = pred.mean(0)
print('observed mean change run5-run1 (nT):', obs.round(0), '| tilt-predicted:', pm.round(0))
print('size ratio %.2f, cosine %.2f' % (np.linalg.norm(pm) / np.linalg.norm(obs), pm @ obs / np.linalg.norm(pm) / np.linalg.norm(obs)))
rows = list(csv.DictReader(open(T + 'magnet_tilt_20261002_223300_tiltcorr.csv')))
g = lambda k: np.array([float(r[k]) for r in rows])
raw = np.c_[g('Bx_raw_G'), g('By_raw_G'), g('Bz_raw_G')]; cor = np.c_[g('Bx_G'), g('By_G'), g('Bz_G')]; t = g('tilt_deg')
dB = np.linalg.norm(cor - raw, axis=1) * 100
print('first tilt run: n=%d tilt median %.2f max %.2f deg ; |dB| median %.2f max %.2f uT ; max relative %.1f%%' % (
    len(rows), np.median(t), t.max(), np.median(dB), dB.max(), 100 * (np.linalg.norm(cor - raw, axis=1) / np.linalg.norm(raw, axis=1)).max()))
