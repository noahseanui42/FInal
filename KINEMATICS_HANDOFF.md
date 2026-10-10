# Kinematics handoff — for the report's kinematics section

What kinematics the delta robot code actually implements, where each piece
lives, and the equations to put in the report. Everything here is taken from
`DeltaAppCalibrated/` (the code the field scans ran on). `DeltaApp/` is the
older, uncalibrated copy — don't quote numbers from it.

## 1. Geometry the code uses (quote these, not the old design values)

| Symbol | Meaning | Value | Source |
|---|---|---|---|
| s_b | base triangle side, through the servo shafts | 175 mm | `delta_servo/config.h`, `delta_app/robot_config.py` |
| s_p | platform triangle side, through the forearm ball-joint centres (the 75 mm inner triangle, **not** the 150 mm plate outline) | 75 mm | same |
| L | bicep, pivot to pivot | 177 mm | same |
| l | forearm, pivot to pivot | 625 mm | same |
| TCP | probe tip offset below the platform | (0, 0, −21) mm | `robot_config.TCP_DEFAULT` |
| θ limits | per arm; θ > 0 = bicep down | −20° … +70° | `CAL[i]`, `ANGLE_LIMITS_DEG` |
| arm remap | model slot → physical servo | `GEOM_TO_PHYS = [2, 0, 1]` | config.h / robot_config.py |

**Flag:** the older project notes say s_b = 450, s_p = 18, L = 180, l = 600. The
code doesn't use any of these values, so the report should use the table above.
`DeltaApp/` (uncalibrated) still has s_p = 150 and L = 180.

Derived constants (`kinematics.cpp:17-22`):

- w_b = s_b / (2√3) = 50.52 mm (centre to servo shaft, at the base side midpoint)
- u_p = s_p / √3 = 43.30 mm (centre to platform ball joint, at the corner)
- w_p = u_p / 2 = 21.65 mm
- a = w_b − u_p = 7.22 mm
- b = s_p/2 − (√3/2) w_b = −6.25 mm
- c = w_p − w_b/2 = −3.61 mm

Frame: origin at the base centre, z up, so working z is negative. Arm slot 1
is on −y, and slots 2 and 3 follow CCW from above. Unit radial vectors are
û_i = (cos φ_i, sin φ_i, 0) with φ = −90°, 30°, 150°.

## 2. Map of the code

| Piece | Where | Upstream or own work |
|---|---|---|
| Inverse kinematics (closed form) | `delta_servo/kinematics.cpp: ik()`, `delta_app/deltarobot.py: calculateIPK` | Upstream (grzesiek2201/Delta-Robot), with guards and the remap added |
| Forward kinematics, three-sphere intersection | `deltarobot.py: calculateFPK` | Upstream, precedence bug fixed |
| Forward kinematics, Newton–Raphson | `delta_app/pose_correction.py: fk()` | Own |
| On-axis home height | `kinematics.cpp: zHome()` | Own |
| Jacobian | `pose_correction.py: jacobian()` | Own |
| Pose-dependent error correction | `pose_correction.py` + `pose_correction_hybrid.json` | Own |
| Trajectory generation, upward approach | `delta_servo/motion.cpp` | Own |
| Angle → servo pulse, calibration | `motion.cpp: angleToUs`, `config.h CAL[]`, `tools/servo_sweep/` | Own |
| Probe tilt (orientation) correction | `FieldTiltScan/field_scan_tilt.py`, `FieldPlots/tilt_correct.m` | Own |

## 3. Equations

### 3.1 Inverse kinematics

Elbow of arm i: **A_i = (w_b + L cos θ_i) û_i − L sin θ_i ẑ**

Forearm constraint, with p = probe target − TCP:
**|p + u_p û_i − A_i|² = l²**

Expanding gives **E_i cos θ_i + F_i sin θ_i + G_i = 0** with

```
E1 = 2L(y + a)
E2 = −L(√3(x + b) + y + c)
E3 =  L(√3(x − b) − y − c)
F_i = 2Lz
G1 = x² + y² + z² + a² + L² + 2ya − l²
G2 = x² + y² + z² + b² + c² + L² + 2xb + 2yc − l²
G3 = x² + y² + z² + b² + c² + L² − 2xb + 2yc − l²
```

The vector form, as written in `pose_correction.ik`: d = p + (u_p − w_b)û_i,
E = −2L(d·û_i), F = 2L d_z, G = |d|² + L² − l².

The half-angle substitution t = tan(θ/2) turns this into a quadratic in t:
(G−E)t² + 2Ft + (G+E) = 0, so

**θ_i = 2 atan[ (−F_i ± √(E_i² + F_i² − G_i²)) / (G_i − E_i) ]**

- E² + F² − G² < 0 means the point is out of reach, and the move is rejected.
- |G − E| < 10⁻⁶ means a singularity guard trips, and the move is rejected.
- The '+' root is tried first, then '−'. The first root inside [−20°, 70°] is
  used. If neither fits, the move is rejected and no partial angles are written.

### 3.2 Forward kinematics

1. **Three-sphere intersection (GUI).** The elbows are shifted by −u_p û_i, and
   spheres of radius l are centred on the shifted points. Subtracting spheres
   pairwise gives two linear equations, which are solved as
   x = a₄y + a₅, z = a₆y + a₇. Substituting into sphere 1 gives a quadratic in y,
   and the code keeps the root with z < 0. Special case: when all elbow heights
   are equal (a₁₃ = a₂₃ = 0), x and y are solved linearly, followed by a
   quadratic in z.
2. **Newton–Raphson (pose correction).** Solves f_i(p) = |s_i|² − l² = 0 with
   s_i = p + u_p û_i − A_i by iterating p ← p − (2S)⁻¹ f, where S has rows s_iᵀ,
   until the step is below 10⁻¹⁰ mm. It has no divide-by-zero poses.
3. **On-axis closed form (firmware).**
   z_home(θ) = −L sin θ − √(l² − (w_b + L cos θ − u_p)²), which gives
   −597.2 mm at θ = 0.

### 3.3 Jacobian

Differentiating the constraint: s_i·dp = (s_i·∂A_i/∂θ_i) dθ_i, with
∂A_i/∂θ_i = −L sin θ_i û_i − L cos θ_i ẑ.

**S dp = D dθ  ⇒  J = S⁻¹D**, where D = diag(s_i·∂A_i/∂θ_i), in mm/rad.

### 3.4 Pose-dependent error correction (open loop)

Off-centre, the servos give under load, which pulls the probe back towards the
axis: about 13 % of the offset, or about 19 mm rms at the corners. The
correction is a compliance model in which a centring "force" maps to joint
deflection through Jᵀ:

```
Δθ = β_x Jᵀ(−x,0,0) + β_y Jᵀ(0,−y,0) + β_mid Jᵀ(−x,0,0)(1 − (y/150)²)   [deg]
p_send = FK( IK(p) − Δθ )
```

β_x = β_y = 5.39 × 10⁻⁷ and β_mid = 2.68 × 10⁻⁷. The firmware is unchanged:
it is sent a target slightly past the real one and settles on the real one.
This is validated for x ±50, y ±150, z −600 … −700 mm, where corner error fell
from about 19 to 2.3 mm rms. It is **not** validated outside that box.

### 3.5 Trajectory generation

- Duration: T = max(|Δp| / v, max|Δθ_i| / ω_max, 200 ms), with v = 5·v_step mm/s
  (5–50) and ω_max = 90 °/s.
- Profile: cubic smoothstep, s(u) = 3u² − 2u³ with u = t/T. Velocity is zero at
  both ends, and the peak is 1.5× the average.
- Joint moves: θ(t) = θ₀ + s(θ₁ − θ₀).
- Linear moves: p(t) = p₀ + s(p₁ − p₀), with IK re-solved every 20 ms tick
  (50 Hz).
- Upward final approach: if any bicep would finish moving down
  (Δθ_i > 0.1°), the robot first goes 20 mm below the target (floor
  z = −779 mm) and then rises vertically into it. This takes up backlash,
  which measured about 1.3° per servo and up to 4.5° on servo 2.

### 3.6 Joint angle → servo pulse

**pulse_i = c_i + d_i k_i θ_i**, clamped to [830, 2170] µs.

| Pin | c_i (µs) | k_i (µs/°) |
|---|---|---|
| D9 | 1456 | 9.8315 |
| D10 | 1373 | 9.7664 |
| D11 | 1393 | 9.6658 |

These come from an assembled protractor sweep. Each arm was fitted as
measured = s·cmd + o, then updated with k ← k/s and c ← c − o·k.

### 3.7 Probe tilt (only if the section covers orientation)

- Accelerometer pitch = atan2(−a_x, √(a_y² + a_z²)) and roll = atan2(a_y, |a_z|).
- With g = a/|a|, the rotation taking g onto g_ref has axis
  k = (g × g_ref)/|g × g_ref| and angle φ = atan2(|g × g_ref|, g·g_ref).
  Rodrigues' formula then gives
  **B_corr = B cos φ + (k × B) sin φ + k(k·B)(1 − cos φ)**.
- Yaw is unobservable from gravity, so it is not corrected.

## 4. Verification evidence for the report

`python3 -m pytest DeltaAppCalibrated/tests/test_kinematics.py test_ik_parity.py
test_pose_correction.py test_config_sync.py` gives **27 passed** (re-run
2026-10-10). The suites check:

- FK(IK(p)) round-trips back to p
- firmware C++ IK matches the GUI Python IK
- the pose correction lands on its targets
- firmware and GUI geometry and limits stay identical

## 5. Loose ends worth knowing

- `deltarobot.py`'s comment on `ub` says "centre to side" but it's really the
  distance from the centre to the base vertex (2·w_b). Only the comment is
  wrong; the maths is right.
- `validatePoints()` and the `safe_leg_*` collision boxes are no-ops. They model
  upstream's frame, not this one, so the code does no collision checking
  against this robot's frame.
- The firmware has no TCP. The GUI and scan scripts subtract it before sending.
- The firmware has no general FK; only `zHome()` exists on the Arduino.
