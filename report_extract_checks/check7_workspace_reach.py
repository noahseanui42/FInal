"""Reachable workspace for the original (SP150, L_UP180) and calibrated (SP75, L_UP177) geometries.
Same IK as DeltaAppCalibrated/delta_servo/kinematics.cpp, limits -20..70 deg, 25 mm grid x,y in +-150, z -790..-565."""
import math
import numpy as np

def make(SB, SP, LU, LL, lim=(-20, 70)):
    wb = SB / (2 * math.sqrt(3)); up = SP / math.sqrt(3); wp = up / 2
    a = wb - up; b = SP / 2 - (math.sqrt(3) / 2) * wb; c = wp - wb / 2; s3 = math.sqrt(3)
    def ok(x, y, z):
        E = [2 * LU * (y + a), -LU * (s3 * (x + b) + y + c), LU * (s3 * (x - b) - y - c)]
        F = [2 * z * LU] * 3
        G = [x*x + y*y + z*z + a*a + LU**2 + 2*y*a - LL**2,
             x*x + y*y + z*z + b*b + c*c + LU**2 + 2*x*b + 2*y*c - LL**2,
             x*x + y*y + z*z + b*b + c*c + LU**2 - 2*x*b + 2*y*c - LL**2]
        for i in range(3):
            disc = E[i]**2 + F[i]**2 - G[i]**2
            if disc < 0 or abs(G[i] - E[i]) < 1e-6:
                return False
            r = math.sqrt(disc)
            if not any(lim[0] <= math.degrees(2 * math.atan((-F[i] + sg * r) / (G[i] - E[i]))) <= lim[1] for sg in (1, -1)):
                return False
        return True
    def zhome(th):
        t = math.radians(th); rad = wb + LU * math.cos(t) - up
        return -LU * math.sin(t) - math.sqrt(LL**2 - rad**2)
    return ok, zhome

for name, g in (('original SB175 SP150 LU180 LL625', (175, 150, 180, 625)), ('calibrated SB175 SP75 LU177 LL625', (175, 75, 177, 625))):
    ok, zhome = make(*g)
    on = [z for z in np.arange(-900, -300, 1.0) if ok(0, 0, z)]
    pts = [(x, y, z) for x in range(-150, 151, 25) for y in range(-150, 151, 25) for z in range(-790, -540, 25)]
    n_plat = sum(ok(x, y, z) for x, y, z in pts)
    n_probe = sum(ok(x, y, z - 21) for x, y, z in pts)
    box = [(x, y, z) for x in range(-50, 51, 10) for y in range(-150, 151, 10) for z in range(-700, -599, 10)]
    print('%s: on-axis platform z %.0f..%.0f (probe z %.0f..%.0f); zhome(-20)=%.1f zhome(0)=%.1f zhome(70)=%.1f' % (
        name, min(on), max(on), min(on) - 21, max(on) - 21, zhome(-20), zhome(0), zhome(70)))
    print('   grid of %d: reachable %d (%.1f%%) treating z as platform-centre; %d (%.1f%%) treating z as probe z' % (
        len(pts), n_plat, 100 * n_plat / len(pts), n_probe, 100 * n_probe / len(pts)))
    print('   R2 box (x+-50, y+-150, z -700..-600 probe) all reachable:', all(ok(x, y, z - 21) for x, y, z in box))
