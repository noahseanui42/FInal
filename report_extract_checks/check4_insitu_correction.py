"""In-situ check of the position correction: measured change (hybrid - off) vs gradient-predicted change grad(B)*e."""
import numpy as np, pandas as pd
S = 'FieldScan/data/'
K = ['x_mm', 'y_mm', 'z_mm']
C = ['Bx_G', 'By_G', 'Bz_G']
L = lambda f: pd.read_csv(f).sort_values(K).reset_index(drop=True)
off = [L(S + 'magnet-xpos_corr-off_run1_20261002_180000.csv'), L(S + 'magnet-xpos_corr-off_run2_20261002_184415.csv')]
hyb = [L(S + 'magnet-xpos_corr-hybrid_run1_20261002_182828.csv'), L(S + 'magnet-xpos_corr-hybrid_run2_20261002_185818.csv')]
A = lambda d: d[C].values * 1e5                                               # nT
Boff, Bhyb = np.mean([A(d) for d in off], 0), np.mean([A(d) for d in hyb], 0)
d = hyb[0]
e = np.stack([d.sent_x_mm - d.x_mm, d.sent_y_mm - d.y_mm, d.sent_z_mm - d.z_mm], 1)
xs, ys, zs = (np.unique(d[k]) for k in K)
G = np.zeros((len(ys), len(xs), len(zs), 3))
ix = [(list(ys).index(y), list(xs).index(x), list(zs).index(z)) for x, y, z in d[K].values]
for i, v in zip(ix, Boff):
    G[i] = v
grad = np.zeros((len(d), 3, 3))
for c in range(3):
    gy, gx, gz = np.gradient(G[..., c], ys, xs, zs)
    for n, i in enumerate(ix):
        grad[n, c, :] = [gx[i], gy[i], gz[i]]
pred = np.einsum('icj,ij->ic', grad, e)
meas = Bhyb - Boff
k = (pred * meas).sum() / (pred * pred).sum()
r = np.corrcoef(pred.ravel(), meas.ravel())[0, 1]
print('n values %d  k %.2f  r %.2f  rms residual %.0f nT  rms measured change %.0f nT  max |e| %.1f mm' % (
    meas.size, k, r, np.sqrt(np.mean((meas - pred)**2)), np.sqrt(np.mean(meas**2)), np.abs(e).max()))
for nm, rr in (('off', off), ('hybrid', hyb)):
    dd = A(rr[0]) - A(rr[1])
    print('%s run1-run2 rms difference %.0f nT (/sqrt2 = %.0f)' % (nm, np.sqrt(np.mean(dd**2)), np.sqrt(np.mean(dd**2)) / np.sqrt(2)))
nm = L(S + 'nomagnet_corr-off_run1_20261002_172221.csv')
j = off[0].merge(nm, on=K, suffixes=('', '_b'))
dB = np.sqrt((j.Bx_G - j.Bx_G_b)**2 + (j.By_G - j.By_G_b)**2 + (j.Bz_G - j.Bz_G_b)**2) * 100
for x in (50, -50):
    print('magnet-only |B| at (%d,0,-675): %.1f uT' % (x, dB[(j.x_mm == x) & (j.y_mm == 0) & (j.z_mm == -675)].iloc[0]))
