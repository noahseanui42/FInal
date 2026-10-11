"""Background |B|, full-box map peaks and durations, probe tilt vs grid centre."""
import numpy as np, pandas as pd
T, S = 'FieldTiltScan/data/', 'FieldScan/data/'
K = ['x_mm', 'y_mm', 'z_mm']
L = pd.read_csv
bmag = lambda d: np.sqrt(d.Bx_G**2 + d.By_G**2 + d.Bz_G**2) * 100          # uT
for f in [S + 'nomagnet_corr-off_run1_20261002_172221.csv', T + 'full25-4z_corr-hybrid_none_20261004_155505.csv',
          T + 'repeat_none_20261006_192127.csv']:
    m = bmag(L(f))
    print('BG %-52s |B| uT min %.1f max %.1f median %.1f  (NaN rows %d)' % (f.split('/')[-1], m.min(), m.max(), m.median(), m.isna().sum()))
bg = L(T + 'full25-4z_corr-hybrid_none_20261004_155505.csv')
mg = L(T + 'full25-4z_corr-hybrid_under_combined_20261003.csv')
m = mg.merge(bg, on=K, suffixes=('', '_b'))
m['dB'] = np.sqrt((m.Bx_G - m.Bx_G_b)**2 + (m.By_G - m.By_G_b)**2 + (m.Bz_G - m.Bz_G_b)**2) * 100
for z, g in m.groupby('z_mm'):
    i = g.dB.idxmax()
    print('z %8.2f  magnet-only peak %.1f uT at (x,y)=(%g,%g)  min %.1f' % (z, g.dB.max(), g.loc[i, 'x_mm'], g.loc[i, 'y_mm'], g.dB.min()))
print('durations (min): magnet %.1f  background %.1f ; median seconds/point %.1f' % (mg.t_s.max() / 60, bg.t_s.max() / 60, bg.t_s.diff().median()))

def tilt(d):
    d = d.dropna(subset=['ax_g'])
    g = d[['ax_g', 'ay_g', 'az_g']].values
    g = g / np.linalg.norm(g, axis=1)[:, None]
    c = d[(d.x_mm == 0) & (d.y_mm == 0)][['ax_g', 'ay_g', 'az_g']].values
    gref = (c / np.linalg.norm(c, axis=1)[:, None]).mean(0)
    gref /= np.linalg.norm(gref)
    ang = np.degrees(np.arccos(np.clip(g @ gref, -1, 1)))
    return pd.Series(ang, index=pd.MultiIndex.from_frame(d[K])), d
for nm, d in (('background', bg), ('magnet', mg)):
    s, dd = tilt(d)
    y = dd.y_mm.values
    print('TILT %-10s n=%d median %.2f max %.2f deg ; median at |y|=150: %.2f, at y=0: %.2f' % (
        nm, len(s), np.median(s), s.max(), np.median(s.values[np.abs(y) == 150]), np.median(s.values[y == 0])))
ta, _ = tilt(mg); tb, _ = tilt(bg)
j = ta.index.intersection(tb.index)
ja, jb = ta[j].dropna(), tb[j].dropna()
j2 = ja.index.intersection(jb.index)
print('next-day tilt repeat: n=%d r=%.2f median |diff| %.2f deg' % (len(j2), np.corrcoef(ja[j2], jb[j2])[0, 1], np.median(np.abs(ja[j2] - jb[j2]))))
