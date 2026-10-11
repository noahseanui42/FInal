"""5-run repeat test spread/drift/sigma_pos; settle 0.5 s vs 5 s; magnet re-placement."""
import glob
import numpy as np, pandas as pd
T, S = 'FieldTiltScan/data/', 'FieldScan/data/'
K = ['x_mm', 'y_mm', 'z_mm']
L = pd.read_csv
runs = [L(f) for f in sorted(glob.glob(T + 'repeat_under-run*.csv'))]
bg = L(T + 'repeat_none_20261006_192127.csv')
B = np.stack([r[['Bx_G', 'By_G', 'Bz_G']].values for r in runs]) * 1e5       # nT, (5,70,3)
mag = np.linalg.norm(B, axis=2)
sd = mag.std(axis=0, ddof=1)
print('|B| per-point SD across 5 runs: median %.0f nT, p95 %.0f' % (np.median(sd), np.percentile(sd, 95)))
off = (B - B.mean(0)).mean(1)
B2 = B - off[:, None, :]
sd2 = np.linalg.norm(B2, axis=2).std(axis=0, ddof=1)
print('after removing a uniform vector offset per run: median %.0f, p95 %.0f' % (np.median(sd2), np.percentile(sd2, 95)))
for i in range(5):
    print('run %d drift vs run 1 (Bx,By,Bz) nT' % (i + 1), np.round((B[i] - B[0]).mean(0)))
r0 = runs[0]
xs, ys, zs = (np.unique(r0[k]) for k in ('x_mm', 'y_mm', 'z_mm'))
idx = [(list(ys).index(y), list(xs).index(x), list(zs).index(z)) for x, y, z in r0[K].values]
def grid(v):
    G = np.full((len(ys), len(xs), len(zs)), np.nan)
    for ix, val in zip(idx, v):
        G[ix] = val
    return G
def gradmag(v):
    a, b, c = np.gradient(grid(v), ys, xs, zs)
    return np.array([np.sqrt(a[i]**2 + b[i]**2 + c[i]**2) for i in idx])
g_total = gradmag(np.linalg.norm(B.mean(0), axis=1))                          # gradient of run-mean |B| (what compare_runs uses)
print('median |grad|B| (run-mean total field): %.0f nT/mm' % np.median(g_total))
print('sigma_pos median: %.2f mm raw, %.2f mm with uniform offset removed' % (np.median(sd / g_total), np.median(sd2 / g_total)))
def md(p, q):
    m = p.merge(q, on=K)
    return np.sqrt((m.Bx_G_x - m.Bx_G_y)**2 + (m.By_G_x - m.By_G_y)**2 + (m.Bz_G_x - m.Bz_G_y)**2) * 1e5
a = L(S + 'magnet-xneg_corr-off_settle0p5s_run1_20261002_022713.csv')
b = L(S + 'magnet-xneg_corr-off_run1_20261002_024004.csv')
d = md(a, b)
print('settle 0.5 s vs 5 s: n=%d median diff %.0f nT, max %.0f ; run times %.1f vs %.1f min' % (len(d), np.median(d), d.max(), a.t_s.max() / 60, b.t_s.max() / 60))
u = L(S + 'magnet-under_corr-hybrid_run1_20261002_205751.csv')
r1 = L(S + 'magnet-under-replaced_corr-hybrid_run1_20261002_212800.csv')
r2 = L(S + 'magnet-under-replaced_corr-hybrid_run2_20261002_214238.csv')
print('first placement vs replaced1: median %.0f nT ; replaced1 vs replaced2: median %.0f nT' % (np.median(md(u, r1)), np.median(md(r1, r2))))
