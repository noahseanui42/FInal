"""Per-axis SD of the 20 averaged samples (nT), per scan file and pooled; exact-zero mean components."""
import glob
import numpy as np, pandas as pd
T, S = 'FieldTiltScan/data/', 'FieldScan/data/'
pooled, tot_rows, zeros = [], 0, 0
for f in sorted(glob.glob(T + '*.csv') + glob.glob(S + '*.csv')):
    if any(s in f for s in ('checks', 'combined', 'tiltcorr')):
        continue
    d = pd.read_csv(f)
    d = d[d.err == 0]
    tot_rows += len(d)
    zeros += int((d[['Bx_G', 'By_G', 'Bz_G']] == 0).sum().sum())
    st = d[['Bx_std_G', 'By_std_G', 'Bz_std_G']].values * 1e5            # G -> nT
    print('%-62s n=%3d  median SD %5.0f nT  max %5.0f' % (f.split('/')[-1], len(d), np.nanmedian(st), np.nanmax(st)))
    ok = d.n_samples >= 20                                                # skip reconnect-degraded rows
    pooled.append(st[ok.values].ravel())
a = np.concatenate(pooled)
print('POOLED (rows with 20 samples): n=%d median %.0f nT max %.0f nT' % (a.size, np.median(a), a.max()))
print('exact-zero mean components: %d of %d (%.2f%%) over %d rows' % (zeros, 3 * tot_rows, 100 * zeros / (3 * tot_rows), tot_rows))
