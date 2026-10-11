"""Joint-sweep errors before/after the 30 Sep refit (in-sample), Jacobian sensitivity, correction magnitudes."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, 'DeltaAppCalibrated/delta_app')
import pose_correction as pc
d = pd.read_csv('DeltaAppCalibrated/tools/servo_sweep/sweep_2026-09-30_up.csv')
u = d[d['pass'] == 'up']
eb, ea = [], []
for n, c in (('D9', 'meas_D9_deg'), ('D10', 'meas_D10_deg'), ('D11', 'meas_D11_deg')):
    cmd, m = u.cmd_deg.values, u[c].values
    e = m - cmd
    s, o = np.polyfit(cmd, m, 1)
    r = m - (s * cmd + o)
    print('%s before rms %.2f max %.2f | fit s %.3f o %.2f | in-sample resid rms %.2f max %.2f | within 1deg: %d -> %d of %d' % (
        n, np.sqrt(np.mean(e**2)), np.abs(e).max(), s, o, np.sqrt(np.mean(r**2)), np.abs(r).max(), (np.abs(e) <= 1).sum(), (np.abs(r) <= 1).sum(), len(e)))
    eb += list(e); ea += list(r)
eb, ea = np.array(eb), np.array(ea)
print('ALL before rms %.2f, within 1deg %.0f%% ; after (in-sample) rms %.2f (dof-corrected %.2f), within 1deg %.0f%%' % (
    np.sqrt(np.mean(eb**2)), 100 * np.mean(np.abs(eb) <= 1), np.sqrt(np.mean(ea**2)), np.sqrt(np.sum(ea**2) / (len(ea) - 6)), 100 * np.mean(np.abs(ea) <= 1)))
print('max between-arm spread in the up pass: %.1f deg' % max(np.ptp(r[['meas_D9_deg', 'meas_D10_deg', 'meas_D11_deg']].values) for _, r in u.iterrows()))
p = np.array([0, 0, -650.0]); th = pc.ik(p); J = pc.jacobian(p, th)
print('at (0,0,-650): dz/dtheta per servo %.3f mm/deg, all three %.2f mm/deg' % (J[2, 0] * np.pi / 180, J[2].sum() * np.pi / 180))
f = pc.PoseCorrection.load()
for q in ([50, 0, -650], [50, 150, -700], [50, 150, -600], [-50, -150, -650]):
    q = np.array(q, float)
    print(q, 'predicted offset (deg, D9 D10 D11)', np.round(f.predict_offset_deg(q), 2), '| |send - target| %.1f mm' % np.linalg.norm(f.compensate(q) - q))
c = pd.read_csv('FieldTiltScan/data/full25-4z_corr-hybrid_under_combined_20261003.csv')
e = np.stack([c.sent_x_mm - c.x_mm, c.sent_y_mm - c.y_mm, c.sent_z_mm - c.z_mm], 1)
n = np.linalg.norm(e, axis=1)
corner = (c.x_mm.abs() == 50) & (c.y_mm.abs() == 150)
xedge = (c.x_mm.abs() == 50) & (c.y_mm == 0)
print('logged correction (sent - target): max %.1f mm; corners %.1f-%.1f (xy part %.1f-%.1f); x=+-50,y=0: %.1f-%.1f; centre %.2f' % (
    n.max(), n[corner].min(), n[corner].max(), np.hypot(e[:, 0], e[:, 1])[corner].min(), np.hypot(e[:, 0], e[:, 1])[corner].max(),
    n[xedge].min(), n[xedge].max(), n[(c.x_mm == 0) & (c.y_mm == 0)].max()))
