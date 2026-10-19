# Demo notes: ENGR489 delta robot field mapper

Prep notes for explaining this repo to examiners. Every `file:line` points into this repo
as committed. Where I couldn't tell what something does, or couldn't verify a claim, it
says so.

**What I checked while writing these notes** (no code was changed):

- `python -m pytest DeltaAppCalibrated/tests FieldTiltScan`: **56 passed**. Phidget22 has
  to be pip-installed; without it 3 tilt tests fail on `import Phidget22`.
  `python -m pytest DeltaApp/tests`: **35 passed**.
- I recomputed scan point 1 of `FieldScan/data/magnet-xpos_corr-hybrid_run1_20261002_182828.csv`
  through the correction, the firmware IK and the pulse mapping. It matches the logged row
  (section 2).
- I did **not** run any MATLAB/Octave code (none installed here) and did **not** compile
  the sketch for the R4 (no Arduino toolchain). The C++ modules compile and pass on the
  host with g++.

---

## 0. One-paragraph pitch

A 3-servo delta robot (Arduino UNO R4 Minima) moves a Phidget 1044 magnetometer through
a 3D grid. A Python script on the laptop owns both the robot (serial) and the sensor
(USB/Phidget22). At each grid point it sends a move, waits for the firmware to report
it has arrived, waits for the arm to settle, averages 20 readings and writes a CSV row.
MATLAB then subtracts a background scan, applies an optional tilt correction and plots
heat maps, direction maps and 3D maps. It also measures repeatability (σ_pos = σ_B/|∇B|)
and accuracy (dipole fit to a magnet moved by a known distance). The firmware is open
loop. Positioning accuracy comes from calibration, a backlash-removing "approach from
below" move, and a Jacobian-based correction for the arm sagging under load.

**Which folders are live:**

| Use | Folder |
|---|---|
| Firmware + GUI + scan runner on the robot | `DeltaAppCalibrated/` |
| Scans with tilt logging (all scans from 3 Oct on) | `FieldTiltScan/` |
| Analysis and plots | `FieldPlots/` |
| 2 Oct scans and the older MATLAB fallback | `FieldScan/` |
| Pre-calibration copy, kept for comparison only | `DeltaApp/` |

---

## 1. Architecture map

### 1.1 Components

| Component | Where | Language | Job |
|---|---|---|---|
| **GUI ("delta app")** | `DeltaAppCalibrated/delta_app/main.py`, `deltagui.py`, `deltarobot.py`, `robot_config.py` | Python 3, Tkinter + matplotlib, pyserial | Set-up only: connect, enable, jog, go-to-point, teach and upload ≤50-point programs, live 3D plot of the arm. **Not used during scans.** |
| **Kinematics (host)** | `delta_app/deltarobot.py` (GUI), `delta_app/pose_correction.py` (scan) | Python (pose_correction needs numpy) | IK/FK for the GUI's reach checks and 3D plot. Separate IK, Newton FK and Jacobian for the position correction. |
| **Kinematics (firmware)** | `delta_servo/kinematics.cpp` | C++ (no Arduino headers) | Closed-form IK on the robot. **The firmware IK is the one that actually drives the servos.** |
| **Firmware** | `delta_servo/delta_servo.ino`, `protocol.cpp`, `motion.cpp`, `config.h` | C++ / Arduino (UNO R4 Minima) | Serial parser, motion planner (smoothstep, upward approach), angle→µs mapping, PWM on D9/D10/D11, 20 ms status stream. |
| **Scan runner / sensor logging** | `delta_app/field_scan.py` | Python | Grid → moves → wait → settle → average the 1044's Magnetometer channel → CSV + `.meta.json`. |
| **Tilt scan runner** | `FieldTiltScan/field_scan_tilt.py` | Python | Reuses `field_scan.py` unchanged. Reads the 1044's **Spatial** channel (field + accel + gyro at the same instant) and adds 16 tilt/gyro columns. |
| **Position correction** | `delta_app/pose_correction.py` + `pose_correction_hybrid.json` | Python/numpy | Predicts each servo's load sag from the Jacobian and aims past the target. |
| **MATLAB fallback scan** | `FieldScan/*.m`, `FieldTiltScan/*.m` | MATLAB (`serialport`, MATLAB's Python interface for Phidget22) | Same scan without Python as the driver. Fallback only. |
| **MATLAB plotting/analysis** | `FieldPlots/*.m` | MATLAB (most also run in Octave) | Heat/direction/side/3D maps, baseline subtraction, tilt correction, repeatability, dipole fit. |
| **Joint dipole fit** | `FieldPlots/fit_dipole_joint.py` | Python (numpy, pandas, scipy) | One shared magnetic moment and one position per run, for the known-move test. |
| **Calibration tool** | `DeltaAppCalibrated/tools/servo_sweep/` | Arduino sketch + xlsx + csv | Drives one servo to a raw µs. Holds the protractor sweep data the calibration was fitted from. |
| **Host tests** | `DeltaAppCalibrated/tests/`, `FieldTiltScan/test_field_scan_tilt.py`, `FieldPlots/test_*.m` | pytest + g++ runners, MATLAB | IK parity C++↔Python, protocol, motion planner, config sync, scan logic, correction, tilt. |

### 1.2 How they talk

**(a) Host ↔ Arduino: USB CDC serial.** It is opened at "115200", which the R4's native USB
ignores. **DTR must be asserted** or nothing arrives (`robot_config.py:48`,
`field_scan.py:120`, `FieldScan/delta_connect.m:8`). Only one program can hold the port,
so the GUI must be closed during a scan.

- **Host → firmware frames** are ASCII tokens in angle brackets:
  `<mode><{json}><#>`. Example move: `<2><{"n":0,"i":0,"v":2,"a":0,"c":[x,y,z]}><#>`.
  `c` is the **effector-centre** position in mm (probe − TCP). The firmware knows nothing
  about the TCP.

  | mode | meaning | firmware action | reply |
  |---|---|---|---|
  | `2` | manual move/jog/home | plan move to `c` | none |
  | `1` | program point `n` | store; `programLen = n+1` | `OK` (no newline) |
  | `3` | wait time after point | store dwell | `OK` |
  | `4`,`5` | wait input / set output | parsed, **not acted on** | `OK` |
  | `0` | start/stop program | `{"start":bool}` | none |
  | `8` | enable | **inverted:** `enable:0` = ENABLE (left over from active-low stepper drivers) | none |
  | `6`,`7`,`9` | calibrate / gripper / SD | ignored | none |

  Dispatch is in `protocol.cpp:95-157`. Frames longer than 128 bytes are dropped
  (`protocol.cpp:57`, `protocol.h` `kBufCap`).
- **Firmware → host:** one status line every 20 ms (`config.h:64`, `delta_servo.ino:121-123`),
  `{"deg":[t1,t2,t3],"mv":0|1,"run":0|1,"en":0|1,"e":0..5}` + CRLF (`Serial.println`).
  Streaming **pauses while a frame is mid-transit** (`rxBusy`, cleared by `<#>` or 1 s of
  silence, `protocol.cpp:64-69`), so a status line can't land inside an `OK`.
  `deg` is the **commanded** angle, not a measured one (open loop).
  `e`: 0 ok, 1 unreachable, 2 linear path left the workspace, 3 not allowed
  (disabled / program running), 4 JSON parse error, 5 µs clamp hit. It is a single latch
  that clears when the next move is accepted.

**(b) Arduino → servos:** `Servo.writeMicroseconds()` on D9/D10/D11, clamped to
830–2170 µs, updated every 20 ms tick (`delta_servo.ino:74-83`).

**(c) Host ↔ Phidget 1044:** USB to the laptop (not the Arduino), through the Phidget22
library. `field_scan.py` uses the Magnetometer channel and **polls** `getMagneticField()`
(`field_scan.py:251-299`). `field_scan_tilt.py` uses the Spatial channel, an **event
callback** that buffers (accel g, gyro °/s, field G, timestamp ms)
(`field_scan_tilt.py:95-238`). The 1044 is USB serial 302277 (`field_scan.py:68`).

**(d) File formats**

| File | Written by | Read by | Content |
|---|---|---|---|
| `<label>_<YYYYMMDD_HHMMSS>.csv` | `field_scan.py` | all `FieldPlots` | 19 columns: `idx, x_mm,y_mm,z_mm` (**target**), `Bx_G..Bz_G` (raw gauss, **sensor axes**), `B*_std_G`, `err`, `t_s`, `n_samples`, `deg1..3` (commanded angles), `sent_x_mm..sent_z_mm` (what was actually sent) (`field_scan.py:44-49`) |
| same, tilt version | `field_scan_tilt.py` | `FieldPlots` | those 19 + 16: `ax_g..az_g`, stds, `gyro_rms_dps`, `gyro_max_dps`, `settle_s`, `settled`, `pitch_deg`, `roll_deg`, `acc_pitch_deg`, `acc_roll_deg`, `spatial_t_first_ms`, `spatial_t_last_ms` (`field_scan_tilt.py:65-73`) |
| MATLAB fallback CSV | `FieldScan/run_field_scan.m` | `FieldPlots` | first 12 columns only |
| `*_tiltcorr.csv` | `FieldPlots/tilt_correct.m` | `FieldPlots` | input with `B*_G` replaced by the corrected field, plus `Bx_raw_G..Bz_raw_G, tilt_deg` |
| `.meta.json` | scan scripts | humans, `fit_dipole` (sensor range) | label, note, full config, sensor info, geometry, correction coefficients, aborted/finished, reconnects |
| `pose_correction_hybrid.json` | fitted in another repo (see §5) | `pose_correction.py` | forces, β, valid box, geometry it was fitted with |
| GUI program file | `deltagui.py:1554-1571` | GUI | two JSON lines (points, functions) |
| `config.txt` (cwd) | GUI Settings | GUI `loadConfig` | TCP, jog step, z limit (overrides `robot_config`!) |

### 1.3 Block diagram

```
                       LAPTOP (macOS)
 ┌──────────────────────────────────────────────────────────────────────┐
 │  SET-UP (GUI closed during scans)     SCAN                           │
 │  main.py → deltagui.py (Tk)           field_scan.py  /  field_scan_  │
 │      │  deltarobot.py (IK/FK, plot)     │                tilt.py      │
 │      │  robot_config.py ◄──────────────┤ pose_correction.py (+json)  │
 │      │                                 │   IK, Newton FK, Jacobian   │
 │      └───────────┐          ┌──────────┤                             │
 │                  ▼          ▼          │ Phidget22 (Python)          │
 │           pyserial, DTR=1, "115200"    │                             │
 └──────────────────┬──────────▲──────────┼──────────▲──────────────────┘
   <2><{json}><#>   │          │ {"deg",  │          │ field G / accel g /
   <8>,<1>,<3>,<0>  │          │  "mv",   │ USB      │ gyro °/s, events or
                    │          │  "e"..}  │          │ polled
                    │          │ 20 ms    ▼          │
                    │          │       ┌────────────────────┐
                    │          │       │ Phidget 1044_0     │  on the end
                    │          │       │ (sn 302277)        │  effector,
                    │          │       └────────────────────┘  21 mm below
 ┌──────────────────▼──────────┴─────────────────────────┐    platform
 │ Arduino UNO R4 Minima: delta_servo                     │
 │  loop(): Serial → protocol.cpp (frames, ArduinoJson)   │
 │          → motion.cpp (state machine, smoothstep,      │
 │            upward approach) → kinematics.cpp (IK)      │
 │          every 20 ms: tick → angleToUs (config.h CAL)  │
 │                       → writeMicroseconds              │
 │          every 20 ms: status line (unless rxBusy)      │
 └───────────────┬────────────────────────────────────────┘
                 │ PWM 830–2170 µs on D9 / D10 / D11 (6 V AA pack)
                 ▼
        3 hobby servos → biceps (177) → forearms (625) → platform (SP 75)

   CSV + .meta.json  ──►  MATLAB  FieldPlots/
     (FieldScan/data,       read_scan / readtable → baseline subtract (match on
      FieldTiltScan/data)   position, 0.1 mm) → [tilt_correct] → R_sensor_to_robot
                            → heat/direction/side/3D maps, compare_runs,
                              fit_dipole, fit_dipole_joint.py
```

### 1.4 Geometry actually in the code

| | Value | Where |
|---|---|---|
| SB (base triangle side, through the bicep pivots) | 175 mm | `config.h:13`, `robot_config.py:11` |
| SP (triangle through the forearm ball joints) | 75 mm (`DeltaApp/` had 150, the platform outline) | `config.h:16`, `robot_config.py:14` |
| L_UP (bicep) | 177 mm (`DeltaApp/` had 180) | `config.h:17` |
| L_LO (forearm) | 625 mm | `config.h:18` |
| TCP (probe below platform centre) | (0, 0, −21) mm | `robot_config.py:42` |
| Joint limits | −20° … 70° all arms (θ>0 = bicep down) | `config.h:42-44` |
| Arm remap `GEOM_TO_PHYS` | [2, 0, 1] | `config.h:60`, `robot_config.py:38` |

If the report or slides quote other numbers (e.g. planning-stage values), they won't match
the code. Check before the demo.

---

## 2. End-to-end trace of one scan point

**Important framing:** scans do **not** start from the GUI. The GUI is for set-up and
jogging. A scan point's "input" is the command line of `field_scan.py`/`field_scan_tilt.py`.
Trace A shows the GUI path (the GUI and the scan share the same firmware path). Trace B
follows a real scan point all the way to the plot.

### Trace A: GUI "Move" (manual input → firmware)

1. The user types x/y/z (probe coordinates) into the entries (`deltagui.py:424-437`) and clicks
   **Move**. That calls `setSendManual` (`deltagui.py:1973-1985`), which in Online mode only
   sets the flag `send_manual = True`.
2. The GUI's poll loop `readEncoders` (`deltagui.py:231`) runs every 10 ms
   (`root.after(10, …)`, `deltagui.py:281`). Commands are only sent right after a status
   line has been parsed: `sendData()` is called at `deltagui.py:252` and calls `manualMove`
   (`deltagui.py:298-299`).
3. `manualMove` (`deltagui.py:1576`) first runs `update3DPlot(..., onlycheck=True)`
   → `DeltaRobot.calculateIPK` (`deltarobot.py:74`). That checks the z guards
   (`deltarobot.py:81`: −800 ≤ z_probe ≤ −300) and the joint limits per arm
   (`deltarobot.py:94-108`). If it passes, `c = entry − TCP` (`deltagui.py:1601-1603`)
   and `v = int(speed% / 10)` (`deltagui.py:1599`).
4. It serialises `<2><{json}>` with spaces stripped (`deltagui.py:1613-1618`), then `<#>`
   (`deltagui.py:1623`).
5. Firmware: the same as Trace B steps 5–9.
6. Coming back: the status line → `json.loads` (`deltagui.py:236`) →
   `writeDataToAngles` (`deltagui.py:260`, `2020`) → `update3DPlot(online=True)` →
   `readCoordinates` → `calculateFPK(angles)` (`deltagui.py:1818`) → redraw. So in Online
   mode the 3D plot shows the angles the firmware *streams back*, including the dip of
   the upward approach.

### Trace B: one real point, CLI → robot → CSV → plot

The point: **row 1 of `FieldScan/data/magnet-xpos_corr-hybrid_run1_20261002_182828.csv`**,
target probe position **(−50, −50, −675) mm**, hybrid correction on. That run's config
(from its `.meta.json`): grid x, y ±50 ×5, z −675…−625 ×3, speed 2, settle 5 s, 20 samples.

| # | Step | Code | Value for this point |
|---|---|---|---|
| 1 | CLI args → `ScanConfig` | `field_scan.py:481-509`, defaults `57-72` | `--label magnet-xpos_corr-hybrid_run1 --correction hybrid --z -675 -625 3` |
| 2 | Grid generated (serpentine) | `scan_grid`, `field_scan.py:79-89` | first point = (x_min, y_min, z of `zr[0]`) = (−50, −50, −675) |
| 3 | Pre-scan: enable, park at (0,0,−650) | `ensure_enabled` `field_scan.py:175-193`; park `350-355` | robot asked to enable only if `en==0`; operator confirms |
| 4a | Correction: IK of the target | `corrected_target` `field_scan.py:315-323` → `PoseCorrection.compensate` `pose_correction.py:150` → `ik` `77-99` | θ(target) = (25.22°, 17.46°, 14.53°) for (D9, D10, D11) |
| 4b | Predicted sag | `predict_offset_deg` `pose_correction.py:145-148` ← `features` `125-131` ← `jacobian` `116-122` | Δθ = (−1.17°, +0.48°, +0.63°) |
| 4c | Aim past it, back to xyz | `aim = ik − Δθ` `pose_correction.py:154`; limits `155-157`; Newton FK `fk` `102-113` | **sent = (−60.68, −57.13, −673.51)**, in the CSV `sent_*` columns ✓ |
| 5 | Build and send the frame | `move_probe` `field_scan.py:212`; timeout `218` (`expected_move_s` `204-209`); `c = sent − TCP` `219`; `frame()` `92-97`; `DeltaLink.send` `158-159` | `<2><{"n":0,"i":0,"v":2,"a":0,"c":[-60.68,-57.13,-652.51]}><#>` |
| 6 | Firmware receives bytes | `loop()` drains Serial `delta_servo.ino:108-111` → `Protocol::feed` `protocol.cpp:31-62` | `<2>` sets `mode_` and `rxBusy` (`protocol.cpp:72-76`); `{..}` → `dispatchPayload` (`95`) → `deserializeJson` (`97`) → case `'2'` (`115`) → `parseMovePoint` (`16-27`) → `onMove` (`delta_servo.ino:20`); `<#>` clears rxBusy (`protocol.cpp:78-80`) |
| 7 | Accept + firmware IK | `Motion::acceptManualMove` `motion.cpp:158-178` → `solveAndBuildTarget` `36-48` → `ik()` `kinematics.cpp:59-93` | θ₁ = (26.39°, 16.98°, 13.90°); `e=0` (`motion.cpp:171`) |
| 8 | Plan: dip or direct, and duration | `startMove` `motion.cpp:89-100` → `planApproach` `55-86`; `beginMove` `102-136` | if any θ grows >0.1° (a bicep would finish going **down**), dip to z_eff − 20 mm (`66`), then a linear rise. Duration = max(dist/(5·v mm/s), Δθmax/(90°/s), 200 ms) (`125-132`) |
| 9 | Every 20 ms: interpolate, IK, pulses | `delta_servo.ino:113-118` → `Motion::tick` `motion.cpp:301-352` (smoothstep `316`; joint interp `338-340`; linear IK each tick `318-336`) → `writeServos` `delta_servo.ino:74-83` → `computeServoUs`/`angleToUs` `motion.cpp:354-376` | final pulses: D9 1456+9.8315·26.39 ≈ **1715 µs**, D10 1373+9.7664·16.98 ≈ **1539 µs**, D11 1393+9.6658·13.90 ≈ **1527 µs** |
| 10 | Status stream back | `printStatusLine` `delta_servo.ino:85-90` → `buildStatus` `protocol.cpp:159-162` | `{"deg":[26.39,16.98,13.90],"mv":1,...}` while moving, then `mv:0` |
| 11 | Host waits for arrival | reader thread `field_scan.py:130-137`; `status()` `139-156`; sleep 0.1 s + flush `223-224`; loop `227-245` | returns on the first `mv=0` after seeing `mv=1`. Arrival means the **commanded** motion has finished, not that the arm has physically stopped |
| 12 | Settle | `time.sleep(cfg.settle_s)` `field_scan.py:398` (tilt version: `wait_settled` `field_scan_tilt.py:256-279`) | 5 s |
| 13 | Read and average | `read_avg` `field_scan.py:284-299` (tilt: `read_point` `field_scan_tilt.py:314-326` ← `samples` `201-219`) | 20 samples × 20 ms ≈ 0.4 s → B = (−0.060399, −0.178922, 0.715232) G, std ≈ 0.4–0.5 mG |
| 14 | Write the row, flush | `field_scan.py:400-406` | `1,-50.00,-50.00,-675.00,-0.060399,-0.178922,0.715232,0.000501,0.000370,0.000370,0,16.87,20,26.390,16.980,13.900,-60.68,-57.13,-673.51` |
| 15 | MATLAB load | `plot_field_layers` → `read_scan` `FieldPlots/plot_field_layers.m:281-292` | columns by header name (textscan, so Octave works too) |
| 16 | Baseline subtract | `plot_field_layers.m:69-84`: match on **target** position to 0.1 mm (`71`), `B = B − B0` (`81`) | e.g. minus `nomagnet_corr-off_run1_20261002_172221.csv` |
| 17 | Sensor → robot axes, \|B\| | `plot_field_layers.m:86-87` (`R` from `scan_config.m`, currently `eye(3)`) | |
| 18 | Grid + plot | `to_grid` `plot_field_layers.m:272-278`; heat map `106-133` (interp2 to 101×101 `111-113`; value labels `117-122`) | this point is the bottom-left cell of the z = −675 panel |

I recomputed steps 4a–4c, 7 and 9 independently. The firmware IK of the sent point gives
(26.386, 16.978, 13.901)°, which matches the logged `deg1..3` to the 2 dp the firmware
streams.

---

## 3. Per-file summary

### Top level
- **`README.md`**: map of the folders, quick start, test command.
- **`.gitignore`**: Python/OS junk plus **MATLAB/Simulink artefacts** (`slprj/`, `*.slxc`, `codegen/`). This is a hint the MATLAB side came from a Simulink project (§5).
- **`ENGR489 Literature Notes.pdf`**: 74 pages of literature notes keyed by Zotero cite key (Williams 2016 delta kinematics, Clavel patent, Helmholtz uniformity, servo calibration, ISO 9283, …). Includes a transcription of the Williams IK equations the code uses (pp. 18–21). Not code.

### `DeltaAppCalibrated/delta_servo/` (firmware, C++)
- **`delta_servo.ino`**: Arduino glue only. `setup()` starts Serial, with servos unattached (boots DISABLED). `loop()` drains Serial into the parser, ticks motion every 20 ms, writes servos, and streams status every 20 ms. `onEnable` does `attach()` then `writeMicroseconds()`, because the R4 Servo library ignores writes made before attach (`delta_servo.ino:35-58`).
- **`config.h`**: the single source of firmware constants: geometry, per-servo `CAL[]` (pin, centre_us, us_per_deg, dir, limits), `US_MIN/MAX`, `GEOM_TO_PHYS`, timing, speeds, upward-approach parameters. No Arduino headers, so the host tests can regex it.
- **`kinematics.h/.cpp`**: `ik(xyz)→θ[3]` (closed form, half-angle, limits, remap), and `zHome(θ)` (on-axis z for equal angles, used for the boot pose). In: effector-centre mm. Out: degrees in physical-servo order, or `false` with no partial write.
- **`protocol.h/.cpp`**: byte-wise frame parser (`<`…`>`, 128-byte cap, `rxBusy` with a 1 s idle timeout), JSON dispatch to `ProtocolCallbacks`, and `buildStatus()`. Numeric strings are coerced for modes 3–5 (Tk sends strings).
- **`motion.h/.cpp`**: planner/state machine (DISABLED → IDLE → MOVING → DWELL). Manual moves with a single "newest wins" pending slot; ≤50-point program runner with dwells; smoothstep timing; joint or linear interpolation; upward final approach; `angleToUs` with clamp → `e=5`.
- **`COPYING`**: GPL-3.0 text (licence of the upstream code).

### `DeltaAppCalibrated/delta_app/` (Python host)
- **`main.py`**: entry point; constructs `DeltaGUI`.
- **`deltagui.py`** (2063 lines, upstream GUI + patches): Tk layout, serial connect (DTR), the `readEncoders` poll loop, flag-based command sending, manual/jog/home moves, program creator/upload (`OK` handshake), 3D and 2D plots, settings/`config.txt`.
- **`deltarobot.py`**: `DeltaRobot`. `calculateIPK` (IK + z guard + remap), `calculateFPK` (three-sphere FK with the upstream equal-height nudge), `calculateConstants` (E, F, G), plot-vertex builders. `validatePoints` is a deliberate no-op.
- **`robot_config.py`**: Python twin of `config.h`: geometry, limits, remap, z guards, TCP, jog step, port, DTR.
- **`field_scan.py`**: the scan CLI. Contains `scan_grid`, `frame`, `DeltaLink` (background reader thread), `ensure_enabled`, `move_probe` (arrival logic + length-scaled timeout), `Phidget1044`, `read_avg`, `run_scan` (CSV/meta), and `FakeLink`/`FakeMag` for `--simulate`.
- **`pose_correction.py`**: the hybrid correction: its own IK, Newton FK, analytic Jacobian, "force" features, `PoseCorrection.compensate`, valid-box and geometry-mismatch checks.
- **`pose_correction_hybrid.json`**: the 3 β coefficients, the valid box (x ±50, y ±150, z −700…−600 probe), the fitted geometry, and the source note (fitted in `noahseanui42/engr489-REPORT`).
- **`collisionException.py`**: an empty exception class. Still caught in the GUI, but nothing raises it any more (§7).
- **`VerticesCoordinates.py`**: dataclass holding the plot line coordinates.
- **`calculateworkarea.py`**: upstream workspace-contour plot. Opens `working area/contours_light.txt`, which isn't in the repo. **Dead.**
- **`gyro data.py`, `joint_angle_plot.py`**: upstream live serial plotters, hard-coded to `COM4`. They expect `acc_x` JSON or bare floats, which this firmware never sends. **Dead.**
- **`requirements.txt`**: pyserial, matplotlib, pandas, Phidget22. numpy is **not** listed, though `--correction hybrid` needs it.
- **`delta icon.ico`**, **`COPYING`**.

### `DeltaAppCalibrated/tests/`
- **`test_kinematics.py`**: Python IK on-axis regression values, unreachable cases, FK∘IK round trip (0.2 mm tolerance, because of the FK nudge).
- **`test_ik_parity.py` + `ik_cli.cpp`**: compiles the firmware IK with g++ and compares it to Python over a grid. Skips the ill-conditioned (G−E)≈0 points.
- **`test_protocol.py` + `protocol_test_runner.cpp`**: 10 parser cases (framing, numeric strings, oversized frames, rxBusy timeout, JSON error → e=4).
- **`test_motion.py` + `motion_test_runner.cpp`**: 17 planner cases (smoothstep, duration formula, pending slot, dwell, stop, clamp, dip/rise variants, disable mid-dip).
- **`test_config_sync.py`**: regexes `config.h` and asserts it equals `robot_config.py` and `field_scan.py` (geometry, limits, pins, remap, dip floor, speed constants).
- **`test_field_scan.py`**: serpentine order, framing, CSV/meta, NaN for unreachable, int speed, stale-line handling, timeouts.
- **`test_pose_correction.py`**: IK/FK/Jacobian (vs finite differences), a reference value from the report repo, compensation, valid box, CLI integration.

### `DeltaAppCalibrated/tools/servo_sweep/`
- **`servo_sweep.ino`**: bench sketch: type `<pin> <us>`, `n`/`p` to step 1200…1840…1200, `off`. Clamped to 830–2170.
- **`sweep_2026-09-30_up.csv`**: the assembled on-axis protractor sweep (cmd vs measured per servo) that the current `CAL[]` was fitted from.
- **`CALIBRATION_LOG.md`**: 29–30 Sep notes, plan, refit table.
- **`joint_angle_calibration_test.xlsx`**: test template (up/down sweep, repeatability, off-axis, analysis formulas). **The measured cells are empty** in the committed copy.
- **`servo_calibration_sheet.xlsx`**, **`servo2_angles.xlsx`**: ruler-method sheets (single-arm sweeps). `servo2_angles` has D10's 29 Sep data.

### `DeltaApp/` (pre-calibration copy)
Same files as `DeltaAppCalibrated/` minus `tools/`. Differences: SP 150, L_UP 180, no
`GEOM_TO_PHYS` remap, older `CAL[]` values, **no upward approach**, a fixed 30 s move
timeout. Kept "for comparison". Don't demo it.

### `FieldScan/` (2 Oct scans + MATLAB fallback)
- **`scan_config.m`**: all MATLAB scan settings (port, TCP, speed, **settle 0.5 s**, grid, python path, sensor serial, `R_sensor_to_robot = eye(3)`, output dir).
- **`scan_grid.m`**: the serpentine grid. Same algorithm as `field_scan.py:79-89`. Has a `%#codegen` pragma (§5).
- **`delta_connect.m` / `delta_send.m` / `delta_status.m` / `delta_move.m`**: serial link: open + DTR + wait for status; frame + `jsonencode`; parse the next status line; send a move and block until `mv==0`.
- **`mag_open.m` / `mag_read.m`**: the 1044 Magnetometer channel through `py.` calls to Phidget22; average n samples.
- **`test_magnetometer.m`**: prints the range and 20 live readings (expect about 0.55–0.6 G with the coils off in Wellington).
- **`make_demo_scan.m`**: synthetic Helmholtz pair (Biot–Savart loops, R = 0.3 m, 50 A-turns) + Earth field. Writes fake coils-on and baseline CSVs.
- **`run_field_scan.m`**: the full MATLAB-only scan. Writes 12-column CSVs and applies `R_sensor_to_robot` itself (unlike the Python scan).
- **`README.md`**, **`HANDOFF.md`** (state of the work at hand-over, risks, decisions), **`data/INDEX.md`** (naming convention, what each scan is).
- **`data/*.csv` + `.meta.json`**: 11 scans from 2 Oct (background, magnet ±x and under, correction off and hybrid, repeats); `data/checks/` holds 8 test, aborted and simulated runs.

### `FieldTiltScan/`
- **`field_scan_tilt.py`**: tilt-logging scan. `Phidget1044Spatial` (event buffer, IMU filter, re-attach handling), `wait_settled` (fixed or gyro-quiet), `accel_pitch_roll`, `read_point`, `run_scan` (adds the tilt columns, gyro zeroing at park, one retry if no data), `FakeTiltSensor` + `VirtualClock` for `--simulate`.
- **`test_field_scan_tilt.py`**: 17 tests with the simulated robot/sensor and stand-ins for the Spatial channel.
- **`mag_settle.m`**: MATLAB wrapper calling the Python `wait_settled`.
- **`mag_open.m`, `mag_read.m`, `run_field_scan.m`, `scan_config.m`, `make_demo_scan.m`, `test_magnetometer.m`, `delta_move.m`**: tilt versions of the FieldScan files. They call the Python reader through MATLAB's out-of-process Python. Settle is 5 s here.
- **`delta_connect.m`, `delta_send.m`, `delta_status.m`, `scan_grid.m`**: identical copies of the FieldScan ones.
- **`README.md`**: usage, columns, how the tilt is computed and its limits, the not-yet-checked list.
- **`data/DIPOLE_TEST.md`**: known-move accuracy test (4 Oct): results and interpretation.
- **`data/REPEAT_TEST.md`**: 5-run repeatability test (6 Oct): spread, drift, σ_pos.
- **`data/*.csv` + `.meta.json`**: the full-box 25 mm scans, dipole runs, repeat runs, the first tilt run and its `_tiltcorr`.
- **`figures/magnet_tilt_20261002_223300/`**: PNGs + `make_correction_change.py` (matplotlib: tilt per point and how much the correction changes Bx/By/Bz).

### `FieldPlots/` (MATLAB analysis)
- **`plot_field_layers.m`**: the main plot. Four figures: |B| heat map per z layer, direction map (xy arrows + Bz colour), side views, stacked 3D. Options: baseline, `R`, `TiltCorrect`, `Save`, `Figures`.
- **`plot_field_arrows3d.m`**: 3D arrows coloured per layer on see-through planes.
- **`plot_field_map.m`**: vectors, |B| slices, and the Helmholtz % uniformity plot on the middle plane. Uses `readtable`/`scatteredInterpolant` (MATLAB-only). **Does not apply `R_sensor_to_robot`.**
- **`plot_correction_map.m`**: arrows of `sent − target` per layer (what the hybrid correction did).
- **`compare_runs.m`**: repeatability: σ of |B| across runs, minus the sensor noise floor in quadrature, ÷ |∇|B|| → σ_pos in mm; weak-gradient points flagged.
- **`compare_repeatability.m`**: two `compare_runs` results side by side (histograms, point vs point).
- **`plot_repeatability_layers.m`**: σ_pos and |∇B| maps per layer.
- **`compare_positions.m`**: `compare_runs` per magnet position group.
- **`compare_heatmaps.m`**: % (or mG) change in the |B| map between runs. Can run standalone with a file picker.
- **`compare_repeat_heatmaps.m`**: standalone version for the 6 Oct repeat test.
- **`repeatability_heatmaps.m`**: preset wrapper over `compare_heatmaps` (6 Oct or 2 Oct pairs).
- **`tilt_correct.m`**: gravity-vector tilt per point; Rodrigues rotation of B back to the reference orientation; optional `_tiltcorr.csv`.
- **`apply_tilt.m`**: what the plots' `TiltCorrect` option calls (chooses the reference, refuses files that are already corrected).
- **`plot_tilt.m`**: tilt map, gyro/settle record, pitch/roll maps, board-vs-accelerometer check.
- **`fit_dipole.m`**: point-dipole fit (linear least squares for m, grid search + `fminsearch` for r0), residual stats, uncertainties. Drops `err≠0` and saturated points.
- **`fit_dipole_joint.py`**: one shared moment and one position per run (scipy `least_squares`). Prints the shifts vs the ruler; `--plot`.
- **`compare_tilt_runs.m`**: repeatability and dipole accuracy, raw vs tilt-corrected.
- **`scan_grid.m`**: copy of the serpentine generator, for the tests.
- **`test_tilt_correct.m`, `test_fit_dipole.m`, `test_compare_tilt_runs.m`**: synthetic-data self-checks.
- **`README.md`**: index of the scripts.

---

## 4. Key algorithms

### 4.1 Inverse kinematics (closed form, per arm)

**Source:** R. L. Williams II, *The Delta Parallel Robot: Kinematics Solutions* (2016).
Same notation as the code. Transcribed in the literature notes PDF, pp. 18–21.

**Geometry constants** (`kinematics.cpp:17-22`, `deltarobot.py:29-35`):

```
w_B = SB/(2√3)   (base inradius: centre → bicep pivot)          = 50.52 mm
u_P = SP/√3      (platform circumradius: centre → ball joint)    = 43.30 mm
w_P = u_P/2      (platform inradius)                             = 21.65 mm
a = w_B − u_P            =  7.217
b = SP/2 − (√3/2)·w_B    = −6.250
c = w_P − w_B/2          = −3.608
```

**Derivation (arm 1, on the −y axis).** Pivot B₁ = (0, −w_B, 0). With bicep angle θ
(0 = horizontal, **positive = down**), the elbow is A₁ = (0, −w_B − L cosθ, −L sinθ).
The platform joint is P₁ = (x, y − u_P, z), where (x, y, z) is the platform centre. The
forearm has fixed length l, so |A₁ − P₁|² = l²:

```
x² + (y + a + L cosθ)² + (z + L sinθ)² = l²
⇒  2L(y+a)·cosθ + 2zL·sinθ + (x²+y²+z²+a²+L²+2ya−l²) = 0
⇒  E cosθ + F sinθ + G = 0
```

Arms 2 and 3 are the same equation rotated by ±120°, giving the other E, F, G.

**Solve with the tangent half-angle substitution** t = tan(θ/2), cosθ = (1−t²)/(1+t²),
sinθ = 2t/(1+t²):

```
(G − E) t² + 2F t + (G + E) = 0
t = (−F ± √(E² + F² − G²)) / (G − E),    θ = 2·atan(t)
```

**In code** (`kinematics.cpp`):
- E, F, G for all three arms: lines 64-77 (Python: `deltarobot.py:253-259`).
- `solveArm` (lines 31-56): a negative discriminant (line 32) means the forearm can't reach
  the point. |G − E| < 1e-6 is guarded (line 37). It tries the `+` root first (42) and
  falls back to `−` (48). Each root must lie inside that servo's [min_deg, max_deg].
- **Root choice:** Williams picks "knees out". The code picks the `+` root if it's inside
  the limits, else the `−` root. With limits −20…70° only the knees-out root is ever in
  range in practice. This is my reading; I didn't prove it for every point.
- **Remap** (lines 79-91): E, F, G are indexed by *geometric slot* (0 = −y, 1 = +120°,
  2 = +240°). `GEOM_TO_PHYS = {2,0,1}` says which physical servo sits in each slot. The
  arms were bolted on 120° round from the model, so physical arm 3 (D11) is the model's
  −y arm. Results are written into physical order (line 90), so `CAL[i]` stays indexed by pin.
- **All-or-nothing:** if any arm fails, `thetaDeg` is untouched (line 85).
- **zHome** (lines 95-99): on-axis with all angles equal, the radial gap
  r = w_B + L cosθ − u_P, so z = −L sinθ − √(l² − r²). At θ = 0 this gives z ≈ −597.2 mm,
  the boot pose.

**Worked check:** effector (0, 0, −629), i.e. probe −650, gives 10.0646° on all arms. That
matches the spreadsheet's expected value at probe z −650.

**Workspace** (my check with the firmware IK, effector coordinates): on-axis z −540 to
−786 mm. On a 25 mm grid x, y ∈ [−150, 150], z ∈ [−790, −550], 1414 of 1690 points (84 %)
are reachable.

**Forward kinematics** (GUI only, `deltarobot.py:122-239`): the intersection of three
spheres of radius l centred on the elbows shifted by the platform joints. There is a
special branch when all three centres are at the same height (`a13 = a23 = 0`). If exactly
two are equal it adds the upstream ±0.01 mm z nudge (`167-171`; biases FK by up to
~0.17 mm). The correction module instead uses **Newton** on the three constraints
(`pose_correction.py:102-113`), which has no special cases.

**Jacobian** (`pose_correction.py:116-122`): differentiate each constraint
|p + u_P·Uᵢ − Aᵢ(θᵢ)|² = l². With sᵢ = p + u_P·Uᵢ − Aᵢ, that gives sᵢ·dp = (sᵢ·∂Aᵢ/∂θᵢ) dθᵢ,
so **J = S⁻¹·diag(sᵢ·∂Aᵢ/∂θᵢ)** with dp = J dθ, then reordered into physical servo order.
Tested against finite differences (`test_pose_correction.py:50`).

**Float32 vs float64:** the firmware uses float32 and Python float64. Near (G−E) ≈ 0 they
round to measurably different angles; the parity test skips those points
(`DeltaAppCalibrated/README.md`, "Tests").

### 4.2 Servo angle → pulse mapping and calibration

**Mapping** (`motion.cpp:354-366`, constants `config.h:41-46`):

```
us = round(centre_us + dir · us_per_deg · θ_deg),   clamped to [830, 2170] µs  (clamp → e = 5)
```

| Pin | centre_us (θ=0, bicep level) | µs/° | dir |
|---|---|---|---|
| D9 | 1456 | 9.8315 | +1 |
| D10 | 1373 | 9.7664 | +1 |
| D11 | 1393 | 9.6658 | +1 |

The −20…70° limits map to roughly 1180–2145 µs (depending on the servo), inside the clamp. The clamp is a backstop.
`motion.h` notes it is only reachable in tests.

**How the numbers were obtained** (`config.h:24-31`, `tools/servo_sweep/CALIBRATION_LOG.md:63-90`):
1. A first pass drove each arm on its own (ruler/angle-finder, 5-point linear fit). D10 was
   re-swept on 29 Sep (`servo2_angles.xlsx`) → 1350 / 9.51.
2. **The 30 Sep refit, fully assembled:** all three arms connected, probe on-axis, z −730 → −590
   in 10 mm steps, **always approached moving up**. A digital protractor on each bicep. The
   raw data is `sweep_2026-09-30_up.csv`.
3. Fit `measured = s·commanded + o` per servo (the −740 lead-in point is excluded because
   it was approached from above). Then correct the mapping so the commanded angle comes out:

   ```
   commanded pulse u = c + k·θ_cmd,  actual θ_meas = s·θ_cmd + o
   want θ_meas:  θ_cmd = (θ_meas − o)/s  ⇒  u = (c − o·k/s) + (k/s)·θ_meas
   ⇒  k' = k/s,   c' = c − o·k'
   ```

   Check: D9 11.8231/1.203 = 9.828 ≈ 9.8315; 1460 − 0.37·9.83 = 1456.4 ✓. D10 9.51/0.974
   = 9.764; 1350 + 2.38·9.766 = 1373.2 ✓. D11 10.5544/1.092 = 9.665; 1410 − 1.73·9.666
   = 1393.3 ✓. Max fit residuals: 1.0°, 1.3°, 0.5°.
4. **Limits −20°/70°**: set by jogging the **full assembly** (single-arm limits were falsely
   tight because the plate sagged). Described as a safe margin, not the hard stop
   (`config.h:33-39`).
5. Both `config.h` and `robot_config.py` must be updated; `test_config_sync.py` fails if
   they differ.

Rule of thumb from the spreadsheet: ~3.1 mm of probe z per degree of bicep error on-axis.

**Enable quirk:** `attach()` on the R4 starts at 1500 µs, and writes before attach are
ignored. So `onEnable` writes the commanded pulse immediately after attach
(`delta_servo.ino:35-51`). The first enable "snaps to flat" (boot θ = 0); later
re-enables snap to the last commanded pose (`motion.cpp:14-25`).

### 4.3 Backlash / overshoot handling

Three separate mechanisms:

**(1) Upward final approach (backlash), firmware** (`config.h:73-84`, `motion.cpp:55-100`, `233-243`).
- *Why:* each servo lands about 1.3° differently depending on whether the bicep last moved
  down or up (servo 2 up to ~4.5°), but tracks within ~0.5° when the last motion is upward.
  This is the claim in `config.h:73-78`; see the caveat below.
- *Rule:* if any bicep's angle would *increase* (go down) by more than 0.1° (`motion.cpp:61`),
  first move to the target's x/y but 20 mm lower (`66`), then rise straight up into the
  target as a **linear** move (`93`). Every bicep is then moving up at the end.
- *Fallbacks to a direct move:* the dip is clamped at z_eff −779 mm, which is the GUI's −800
  probe limit minus the TCP (`67`, test-enforced); there is no room (`68`); the dip point is
  unreachable (`72`); or rising from the dip wouldn't raise *every* bicep (`75-77`).
- *Atomic:* `mv` stays 1 through both legs. A dwell, a pending move or a stop all wait for
  the rise (`motion.cpp:238-242`). If the rise leaves the workspace mid-path, it stops with
  `e=2` and doesn't continue the rise (`325-330`).
- *Cost:* ~40 mm extra travel per move, about 4 s at v = 2 (10 mm/s). `field_scan.py`
  includes it in the timeout (`field_scan.py:199-209`).
- **Caveat:** `CALIBRATION_LOG.md:89` says the Down pass (hysteresis) was *not measured
  yet*, and the hysteresis test sheet is empty. The 1.3°/4.5° figures look like they come
  from the single −740 lead-in point. I computed its deviation from the up-fit: D9 −0.8°,
  D10 +4.1°, D11 −1.7°, which is consistent. Be ready to say the backlash evidence is that
  one point plus the repeatability results.

**(2) Load-sag compensation ("hybrid" correction), host** (`pose_correction.py`).
- *Observation:* off-centre, the servos give under load and the probe lands short, pulled
  toward the axis by ~13 % of its offset (~19 mm rms at the box corners).
- *Model:* a lumped joint-compliance model. A virtual force F pointing back to the axis
  maps to joint torques τ = Jᵀ F (statics), and each joint yields Δθ ∝ τ:

  ```
  f_cx = Jᵀ(−x, 0, 0),  f_cy = Jᵀ(0, −y, 0),  f_mid = f_cx·(1 − (y/150)²)    [deg]
  Δθ = β_x f_cx + β_y f_cy + β_mid f_mid,     β = (5.39e-7, 5.39e-7, 2.68e-7)
  send = FK( IK(p) − Δθ )
  ```

  Code: `features` (`pose_correction.py:125-131`), `predict_offset_deg` (`145-148`),
  `compensate` (`150-158`). The firmware is unchanged: its IK of `send` gives IK(p) − Δθ,
  and the servos sag back onto IK(p).
- *Claimed validation* (in another repo, see §5): corner error ~19 → 2.3 mm rms inside
  x ±50, y ±150, z −600…−700. The script warns outside that box (`field_scan.py:341-343`).
  About 5 mm remains at the centre from platform tilt, which no angle correction can fix
  (`FieldScan/README.md:79-82`).
- So the scan deliberately **aims past** the target. That's the intentional "overshoot";
  the CSV keeps target and sent positions separate.

**(3) Mechanical overshoot / ringing after a move.**
- The trajectory itself has no overshoot: **smoothstep** s(u) = 3u² − 2u³ (`motion.cpp:316`)
  has zero velocity at both ends, so commanded motion starts and stops gently.
- The physical arm still swings for a few seconds. `field_scan.py` waits a fixed **5 s**
  after `mv` drops (`field_scan.py:63,398`). `field_scan_tilt.py` can instead wait until
  the gyro stays below a threshold for `still_s` (`field_scan_tilt.py:256-279`). Each row
  logs `gyro_rms_dps` so you can check after the fact.
- Evidence the settle matters (my quick calculation from the 2 Oct data):
  `magnet-xneg … settle0p5s` vs the same magnet at 5 s settle differ by a **median 8.2 mG**
  per point (max 17). Two 5 s runs of `magnet-xpos` differ by a median 2.9 mG. Caveat: the
  runs are 13 and 44 min apart, so drift is mixed in; this isn't a controlled comparison.

### 4.4 Scan path generation

`scan_grid` (`field_scan.py:79-89`, identical to `FieldScan/scan_grid.m:1-21`):

```
xs = linspace(xr), ys = linspace(yr), zs = linspace(zr)
for z in zs:                 # layer by layer, in the order zr gives (default -700 → -600: bottom up)
    for j, y in enumerate(ys):
        x order = xs if j even else reversed(xs)      # serpentine within a layer
```

- The serpentine (boustrophedon) halves the travel within a layer compared with raster
  order, because each row starts where the last one ended.
- It is **not** serpentine between layers. Each layer restarts at (x_min, y_min), so a
  layer change is a long diagonal move (the code comment gives 340 mm ≈ 36 s at v = 2,
  `field_scan.py:206`). That's why the move timeout scales with distance:
  `timeout = 30 s + (d + 2·20)/(5·v)` (`field_scan.py:204-218`).
- Positions are **probe (TCP) coordinates in the robot frame**. TCP is subtracted only when
  the frame is built (`field_scan.py:219`).
- Points that are unreachable (`e=1`), or that the correction would push outside the joint
  limits, are logged as NaN rows. The robot isn't moved for them (`field_scan.py:386-396`).
- Moves are **joint mode** (`i=0`) so they can't fail mid-path. Only the vertical rise of the
  upward approach is linear.

### 4.5 Sensor read timing

Timeline of one point (Python scan, defaults):

```
t=0      send <2>{...}<#>
t=0.1 s  flush buffered status lines (anything older is stale; every move lasts ≥200 ms)
         wait: status lines every 20 ms; need mv=1 then mv=0
         (or mv=0 with no mv=1 seen for >1 s → trust it)            field_scan.py:221-245
         move itself: dip leg + 20 mm rise at 10 mm/s (v=2) ≈ 4–6 s for a 25 mm step
t_arr    mv 1→0  (commanded motion finished)
+5.0 s   settle (fixed), or gyro-quiet wait (tilt script)          field_scan.py:398
+0.4 s   20 samples × 20 ms                                        field_scan.py:284-299
         row written + flushed                                     field_scan.py:401-406
```

Measured in the data: `magnet-xpos_corr-off_run1` took 829 s for 75 points, **≈ 11 s per
point**. That fits ~5–6 s of motion + 5 s settle + 0.4 s sampling.

Details worth knowing:
- **Firmware side:** status every `STREAM_MS = 20` ms, servo update every `TICK_MS = 20` ms
  (`config.h:63-64`). Streaming pauses while `rxBusy`.
- **Why a reader thread:** if nothing reads the port while the script sleeps (settle,
  sampling, prompts), status lines pile up and old `en=0`/`mv=0` lines arrive first and
  look current. `DeltaLink` reads continuously into a queue, and `flush_input()` discards
  the backlog (`field_scan.py:103-111`, `130-167`).
- **Magnetometer channel (`field_scan.py`):** data interval set to
  max(min interval, 20 ms) (`field_scan.py:258`), then **polled** with
  `getMagneticField()` + `sleep(20 ms)`. Polls aren't synchronised to the sensor's own
  updates, so a sample could be read twice or skipped. That would slightly understate the
  std. I haven't verified whether it happens.
- **Spatial channel (`field_scan_tilt.py`):** a callback appends every event to a deque
  (`161-166`). `samples()` **clears the buffer first**, so nothing from the settle period is
  used, then collects the next n events (`201-219`). Field, accel and gyro in a row come
  from the same events. Each row also records the 1044's own timestamps of the first and
  last event (≈380 ms apart).
- **Gyro zeroing** at the park position before the scan (`field_scan_tilt.py:370-374`;
  Phidget's `zeroGyro` needs the board still for 1–2 s).
- **USB drop-outs:** if the 1044 re-attaches mid-scan, the data interval and filter are
  restored (`139-154`), an empty point is retried once after 5 s (`434-437`), and the point
  index is logged in `.meta.json`. The gyro zero is lost from then on.
- **MATLAB fallback is weaker:** `FieldScan/scan_config.m:11` uses 0.5 s settle, and
  `delta_move.m:27-33` returns on the first `mv==0` (no "seen moving" guard) with a fixed
  30 s timeout.

### 4.6 Analysis maths (brief, in case it comes up)

- **Baseline subtraction:** the field at a target point minus the no-magnet (or coils-off)
  scan at the same target point, matched to 0.1 mm (`plot_field_layers.m:71`). This removes
  the Earth's field, the servo motors' magnets (~0.15 G at the probe, `REPEAT_TEST.md:67`)
  and the sensor offset, as long as they don't change between scans.
- **Tilt correction** (`tilt_correct.m:59-82`): at rest the accelerometer measures gravity,
  so g = a/|a|. Rotate B by the smallest rotation taking g onto the reference g_ref
  (Rodrigues: v cosθ + (k×v) sinθ + k(k·v)(1−cosθ)). It corrects pitch and roll only; yaw
  is invisible to gravity. The correction is relative to a reference point, not absolute.
- **Repeatability** (`compare_runs.m:62-104`): σ_B = std of |B| across runs. Remove the
  sensor noise in quadrature: σ_B,corr = √(σ_B² − σ_noise²). Then σ_pos = σ_B,corr/|∇|B||.
  Points with gradient < 10 % of the median are flagged. Result: **2.2 mm median**
  (`REPEAT_TEST.md:76`).
- **Dipole fit** (`fit_dipole.m`): B = μ₀/4π·(3(m·û)û − m)/r³. For a fixed r₀ it's linear in
  m, so the code solves m by least squares and searches only over r₀ (grid + fminsearch).
  The joint version shares m across runs (`fit_dipole_joint.py`). **y moves come out within
  1.3 mm over 100–200 mm; x moves are off by −10 / +6 mm** (x grid only 100 mm wide).
  There's a consistent ~4° rotation and a 33 mm y offset of the floor mark
  (`DIPOLE_TEST.md:67-91`).

---

## 5. Provenance (what's adapted vs written fresh)

### 5.1 Evidence used
- File headers: `Derived from grzesiek2201/Delta-Robot (GPL-3.0) @ 48a8038`.
- READMEs and `FieldScan/HANDOFF.md`.
- `git log`: 38 commits. The first six (2 Oct, by `noahseanui42`, e.g. "Add DeltaApp…",
  "Add FieldPlots…") are **bulk imports** of work done in other repos, so this repo's
  history can't show how that code was developed.

### 5.2 Adapted from `grzesiek2201/Delta-Robot` (commit 48a8038, GPL-3.0, Jakub Wrona & Grzegorz Radziwiłko)

| File | How much is upstream | Local changes (per comments) |
|---|---|---|
| `delta_app/deltagui.py` | **Most of it** (Tk GUI, framing constants, upload/handshake, plots) | macOS Dark-Mode colours (`57-63`), window sizing (`64-78`), menus moved into File (`146-155`), DTR from config (`221`), 3D plot shrunk, leg prisms removed, `ALLOWED_PINS` for R4 |
| `delta_app/deltarobot.py` | **Most of it** (IK/FK, plot vertices, collision helpers) | geometry from `robot_config`, per-arm limits, `GEOM_TO_PHYS` remap, operator-precedence fix in the FK guard (`162-167`), `validatePoints` → no-op, `Z_MAX` replaces hard-coded −70 |
| `main.py`, `collisionException.py`, `VerticesCoordinates.py`, `calculateworkarea.py`, `gyro data.py`, `joint_angle_plot.py`, `delta icon.ico` | Unchanged upstream apart from the header | none |
| `delta_servo/kinematics.cpp` | **Port** of upstream `inverse_kin.cpp` (`kinematics.cpp:4-7`) | explicit discriminant/singularity guards, `M_PI` instead of 3.14, per-arm limits, remap |
| `delta_servo/protocol.cpp` | **Framing ported** from upstream `delta_main_code.ino` (`recvWithStartEndMarkers`, `readMode`, `deserializeSerial`) (`protocol.cpp:4-8`) | new dispatch table and reply rules for this firmware |
| `delta_servo/config.h`, `delta_servo.ino`, `kinematics.h`, `robot_config.py` | Carry the header, but the content is new (servo version; the upstream firmware drove **steppers**) | The header is there for GPL attribution |

- The **IK maths** is Williams (2016), the same derivation upstream used. The constants and
  E/F/G match the paper exactly (literature notes pp. 18–21).
- **Vendored:** `third_party/ArduinoJson` v7.2.1 (MIT, Benoît Blanchon).
- **No header, so new relative to upstream:** `motion.h/.cpp` (servo planner, upward approach,
  smoothstep timing), `protocol.h` (the callback interface), and all of `tests/`.

### 5.3 "Inherited" MATLAB / other repos

- `FieldScan/HANDOFF.md:6-20` says the field-scan work was done in **`noahseanui42/Matlab`**
  (branch `claude/brave-edison-mui291`), which had **`Kinematics/`** and **`Simulink/`**
  folders: "the older offline MATLAB pipeline" (`HANDOFF.md:141-145`). Those folders are
  **not in this repo**.
- **`scan_grid.m`** came from that `Kinematics/` folder. Evidence: the `%#codegen` pragma
  (`FieldScan/scan_grid.m:2`, a MATLAB Coder/Simulink leftover), the docstring
  "identical to Kinematics/scan_grid.m" (`field_scan.py:80`), and HANDOFF's description of
  `run_field_scan.m` using "the serpentine grid from `Kinematics/scan_grid.m`".
- `.gitignore` lists Simulink build artefacts, which also suggests it was copied from that
  project.
- `init_scan.m` and the Simulink model are mentioned but absent. I can't tell from this repo
  who wrote them or whether they were course-supplied. **Ask yourself/your notes**.
- **`noahseanui42/engr489-REPORT`** holds the correction fit (`analysis/refit_v2.py
  --hybrid`) and the calibration write-ups `calibration/2026-10-01_*.md`
  (`pose_correction.py:16-21`, JSON `source`). The 19 → 2.3 mm validation lives there, not here.
- **Calibrated firmware branch** `claude/amazing-lovelace-onixrv` (`a185b44` calibration refit,
  `ffe256b` upward approach) is named in the JSON's `geometry.firmware`.
- **`engr489-delta-robot` repo:** the 2 Oct `.meta.json` files record
  `out_dir: /Users/rochelle/engr489-delta-robot/host/Matlab-fieldscan/...`, so the scans ran
  from a checkout of a bigger repo on the scan MacBook.
- **References to missing documents:** `HANDOFF §4/§5/§6/§8/§9/§12` throughout the firmware
  and GUI comments refer to a planning HANDOFF document that isn't in this repo
  (`FieldScan/HANDOFF.md` is a different, later note). `python -m host.calibrate` is also
  "not part of this repo" (`DeltaAppCalibrated/README.md`, Calibration procedure).

### 5.4 AI-assisted code (be ready for this question)

- **21 of the 38 commits are authored `Claude <noreply@anthropic.com>`** with `Claude-Session`
  trailers (2–7 Oct). They cover: all the later `FieldPlots` heat-map scripts,
  `fit_dipole_joint.py --plot`, the FieldTiltScan reconnect fix, the length-scaled move
  timeout, and the `REPEAT_TEST.md`/`DIPOLE_TEST.md` write-ups.
- **Commits by `Noah-Seā Nui`:** the scan data (dipole, repeat, full-box runs).
- **The imported code also shows signs of AI sessions:** branch names `claude/...`
  throughout. `HANDOFF.md:85-86`: "`field_scan.py` was written by another session (branch
  `claude/gallant-planck-stiamj`)". `CALIBRATION_LOG.md:45`: "Send Claude the step 1–4
  numbers. Claude updates `config.h`". `DeltaAppCalibrated/README.md`: "Assumptions made …
  confirmed with the user before implementation", and "this container's network blocks
  downloads.arduino.cc".
- What the record shows as **yours**: hardware, measurements (sweeps, pen tests, scans), the
  design decisions the docs say were "confirmed with the user" (geometry, forearm length,
  pin map, TCP, limits), and the experiments (dipole, repeat). **Be upfront** about which
  parts you designed and verified versus which were generated, and check your course's
  AI-use declaration. Being able to explain the maths in §4 is the best answer to "did you
  understand it?".

---

## 6. Likely examiner questions (short answers)

1. **"Walk me through what happens when you scan a point."** → §2 Trace B. In short: grid
   point → optional correction → `<2>` joint move → firmware IK → smoothstep → dip and rise →
   `mv` 1→0 → 5 s settle → 20-sample average → CSV row → MATLAB subtracts the baseline and plots.
2. **"How does your IK work? Is it numerical?"** → Closed form per arm. Each forearm-length
   constraint becomes E cosθ + F sinθ + G = 0, solved with t = tan(θ/2). There's no
   iteration on the robot (`kinematics.cpp:31-93`). Williams 2016.
3. **"Why is IK in both Python and C++? How do you know they agree?"** → The firmware IK
   drives the servos. The Python IK is for GUI reach checks, plotting and the correction.
   `test_ik_parity.py` compiles the C++ and compares the two over a grid. `test_config_sync.py`
   keeps the constants identical.
4. **"Is it closed loop?"** → No. Hobby servos, open loop. `deg` in the CSV is the
   *commanded* angle. Accuracy comes from calibration, the upward approach and the hybrid
   correction. Pot feedback on A0–A2 is listed as future work.
5. **"How did you calibrate the servos?"** → An assembled on-axis protractor sweep, always
   approached upward. Fit measured = s·cmd + o, then k' = k/s, c' = c − o·k' (§4.2). Limits
   from jogging the full assembly.
6. **"What's GEOM_TO_PHYS?"** → The arms were bolted on 120° round from the model's layout
   (found with the pen-holder test: the marks were rotated exactly 120°). It was fixed in
   software by remapping slots to pins, in both firmware and GUI, with a test that keeps
   them equal.
7. **"What about backlash?"** → Every move ends with all biceps moving up: dip 20 mm below
   the target, then rise (`motion.cpp:55-100`). Cost ~4 s per move. (Caveat in §4.3: the
   down-pass hysteresis wasn't fully measured.)
8. **"Why not linear interpolation for moves?"** → Joint-mode moves can't leave the
   workspace mid-path, and they need no IK per tick. Only the 20 mm rise is linear, so it's
   a straight vertical approach.
9. **"Why smoothstep?"** → 3u² − 2u³ gives zero velocity at both ends, so moves start and
   stop gently, with less excitation of the flexible arms. The duration is set by the
   larger of the linear speed limit and a 90°/s joint-speed cap, with a 200 ms minimum
   (`motion.cpp:102-136`).
10. **"How do you know the robot has arrived?"** → `mv` goes 1→0 in the 20 ms status stream.
    The script ignores stale lines (flush after 100 ms, needs to see `mv=1` first), then
    waits 5 s more because `mv` only means the *commanded* motion has finished
    (`field_scan.py:221-245`).
11. **"Why 5 s settle?"** → The arms keep swinging. Data with 0.5 s vs 5 s settle differ by
    ~8 mG median vs ~3 mG between two 5 s runs (confounded by drift). The tilt script can
    instead wait for the gyro to go quiet.
12. **"What's the position correction?"** → A compliance model: virtual restoring force →
    joint torque via Jᵀ → predicted Δθ (3 fitted βs). Aim at FK(IK(p) − Δθ). Corners ~19 →
    2.3 mm rms in the validated box (§4.3).
13. **"What's your repeatability and accuracy?"** → Repeatability: 2.2 mm median σ_pos from
    5 runs (`REPEAT_TEST.md`), matching 2–2.5 mm from pen tests. Accuracy (dipole known-move):
    y shifts within 1.3 mm; x shifts −10/+6 mm; ~4° frame rotation and 33 mm y offset of the
    mark unresolved (`DIPOLE_TEST.md`).
14. **"The servos have magnets. How is that not ruining the measurement?"** → Their static
    field (~0.15 G at the probe) is in both the magnet scan and the background scan at the
    same points, so it cancels on subtraction. What doesn't cancel is drift: ~11 mG per hour,
    ~17 % explained by tilt creep and the rest probably thermal, so take the background close
    in time or fit a per-run offset.
15. **"Why Python for the scan and MATLAB for the analysis?"** → Python owns the serial port
    and the Phidget library in real time. MATLAB is what the analysis/plots were built in.
    CSV is the boundary. A MATLAB-only scan exists as a fallback.
16. **"What if the scan crashes?"** → Every row is flushed immediately. Ctrl+C marks
    `aborted` in the meta. Unreachable points are logged as NaN, not skipped silently. The
    robot is left **enabled** because disabling drops the arms.
17. **"Why the Spatial channel / why IMU not AHRS?"** → Spatial gives field + accel + gyro
    from the same instant, so the tilt in a row belongs to the same field reading. The tilt
    script's docstring also says the separate Magnetometer/Accelerometer/Gyroscope channels
    "don't open on our board" (`field_scan_tilt.py:13-14`). But the 2 Oct scans *did* use
    the Magnetometer channel (`field_scan.py:251-258`), so presumably it was the accel/gyro
    channels that failed. **I'm not sure; check your notes.** AHRS also steers by the
    magnetometer, which the magnet being mapped disturbs.
18. **"What does the tilt correction do and not do?"** → It rotates each B by the rotation
    taking its gravity vector onto the reference. Pitch/roll only, no yaw. Relative, not
    absolute.
19. **"Why the R4 Minima?"** → No WiFi radio near the magnetometer (RF), and it's the board
    the firmware's Servo-library quirks were checked against.
20. **"How did you test without hardware?"** → `--simulate` (FakeLink/FakeMag/FakeTiltSensor),
    host-compiled firmware modules with g++ test runners, synthetic MATLAB tests. 56 + 35
    pytest tests pass.
21. **"How much of this did you write?"** → See §5. Have an honest, specific answer ready.
22. **"What would you do next?"** → Pot feedback (closed loop), calibration in EEPROM,
    measure the down-pass hysteresis, measure `R_sensor_to_robot`, a wider x grid for the
    dipole test, real Helmholtz-coil scans, a warm-up protocol for the drift.

---

## 7. Weak spots (be ready to justify or admit)

### 7.1 Hard-coded values
- **Serial port** `/dev/cu.usbmodem14101` (`robot_config.py:47`, `FieldScan/scan_config.m:6`)
  and **sensor serial** 302277 (`field_scan.py:68`). There's a `--port` override.
- **Calibration is compiled in** (`config.h:41-45`): one sweep, one day, no EEPROM. A servo
  swap needs a reflash. Limits −20/70° are a "safe margin", not measured stops.
- **TCP −21 mm** (`robot_config.py:42`). The README notes the pen-holder TCP was never
  measured or updated for the bench tests.
- **Duplicated constants:** `SPEED_PER_V_MM_S = 5`, `APPROACH_DZ_MM = 20` copied into
  `field_scan.py:199-200`, and the correction geometry duplicated in the JSON. Guarded by
  `test_config_sync.py` and `geometry_mismatch()`, but still copies.
- **`R_sensor_to_robot = eye(3)`** (`scan_config.m:30`) is *assumed*, never measured. The
  dipole test suggests ~4° of rotation between the ruler, robot and sensor frames.
- **Magic numbers:** `cx_mid` uses a hard-coded 150 mm (`pose_correction.py:131`);
  `LONGEST_MOVE_MM = 600` (`field_scan.py:201`); `UNKNOWN = 1e100` (`field_scan_tilt.py:72`);
  GUI `Z_MAX = −300` (`robot_config.py:40`); firmware dip floor −779 (`config.h:84`).
- **MATLAB vs Python defaults differ:** settle 0.5 s (`FieldScan/scan_config.m:11`) vs 5 s.

### 7.2 Missing or weak error handling
- **Open loop:** nothing detects a stalled or slipped servo. `deg` is commanded, not measured.
- **`e=2` (rise left the workspace) and `e=5` (pulse clamp) still get measured and logged.**
  `move_probe` only treats `e=1` as "skip" (`field_scan.py:233-243`). Of the plots, only
  `fit_dipole` drops `err≠0` (`fit_dipole.m:100`). `plot_field_layers`, `plot_field_map` and
  `compare_runs` ignore `err`. **Every point in every committed scan has `err=0`**, so the
  current results aren't affected, but say it's a gap.
- **GUI upload handshake timeout is broken (upstream):** `receive_time = time.time() − time.time()`
  is 0, then becomes an absolute time, so the 0.2 s wait loop exits after one try
  (`deltagui.py:1472-1477`, `1513-1517`). A missing `OK` for point 0 is never reported
  (`deltagui.py:1479`). Not used by scans.
- **The GUI swallows exceptions** in its poll loop with prints (`deltagui.py:239-250`).
- **The firmware trusts JSON defaults:** missing fields become 0 (`protocol.cpp:16-27`). A
  move without `c` targets (0,0,0) and is rejected as unreachable. Harmless, but silent.
- **Disabling mid joint-move:** in joint mode `xyz_` only updates at the end of the move
  (`motion.cpp:338-346`). If disabled mid-move, `theta_` and `xyz_` disagree, and a later
  *linear* move would interpolate from a stale start. Scans use joint mode, so this is low risk.
- **No host heartbeat:** if the laptop dies the servos hold the last pose (arguably the safe
  choice). Disabling or power loss drops the arms.
- **MATLAB fallback** `delta_move.m:27-33`: no stale-line guard and a fixed 30 s timeout (a
  layer change can take ~36 s). It was never run in MATLAB per the READMEs
  (`FieldScan/HANDOFF.md:69-77`; `FieldTiltScan/README.md:237-246`).
- **Polled sampling** in `field_scan.py` may double-count samples (§4.5). Unverified.

### 7.3 Dead or unused code
- `calculateworkarea.py` (missing input folder), `gyro data.py` and `joint_angle_plot.py`
  (COM4, a different firmware's output). All upstream.
- `deltarobot.py`: `safe_leg_*` (`41-43`), `SafeLegArea`/`checkIfPointInArea` (`350-418`)
  are never called; `validatePoints` is a no-op (`331-337`). The GUI's `CollisionException`
  handlers can't fire.
- GUI: `addRightPrismToPlot`, `saveRefreshTimes`, commented-out code (`deltagui.py:277-279`,
  `1619-1622`, `1998-2004`), the gripper/SD/home buttons (firmware ignores modes 6/7/9),
  "Circular" interpolation (treated as joint), the acceleration field `a` (ignored by the
  firmware), modes 4/5 (parsed, `OK`ed, never acted on).
- `Motion::isApproaching()` is only used by tests.
- `DeltaApp/` is a full duplicate of the older version.

### 7.4 Bugs I found while reading (minor, display only)
- **The GUI 3D plot draws the arms wrong since the remap.** `calculateAMatrix`
  (`deltarobot.py:262-272`) uses `self.fi[0..2]` (physical order) as if they were geometric
  slots. I checked at (60, 0, −650): the drawn forearms come out 640 / 595 / 640 mm instead
  of 625. **This only affects the picture.** The firmware does its own IK, and the
  FK/reach checks use the remap correctly.
- The "Available pins" menu item is still a bare top-level command (`deltagui.py:160`), so
  it's invisible on macOS. That's the same bug the README says was fixed for the other items.
- **`config.txt` in the working directory silently overrides the TCP, jog step and z limit**
  (`deltagui.py:1114-1128`). A stale file would shift every GUI move.

### 7.5 Documentation that doesn't match the code or data
- **Hysteresis claim vs log:** `config.h:73-78` cites ~1.3°/4.5° up-vs-down, but
  `CALIBRATION_LOG.md:89` says the Down pass wasn't measured and the test sheet is empty
  (§4.3).
- **Reachability:** `DeltaAppCalibrated/README.md` says ~89 % (1501/1690) of the 25 mm grid
  is reachable. With the current geometry I get **84 % (1414/1690)** in effector coordinates.
  The README figure may be from the older geometry. The on-axis range (−540…−786) does
  reproduce.
- **Stale comments:** `motion.h:55` says "placeholder calibration"; `protocol.h:3,22` names
  `tests/test_protocol.cpp` (it's `protocol_test_runner.cpp`); `field_scan.py:80` and
  `FieldScan/HANDOFF.md:20` point to a `Kinematics/` folder that isn't here; upstream
  comments in `deltarobot.py:29-32` mislabel `ub`/`wp`.
- **The 2 Oct `.meta.json` files** show `geometry_mismatch_with_robot_config` (SP 150 vs 75,
  etc.), because the scan PC's `robot_config.py` was old. The firmware was the calibrated
  one: the logged angles match the calibrated IK. I confirmed this for point 1 (§2).
- `requirements.txt` omits numpy (needed for `--correction hybrid`) and scipy (needed for
  `fit_dipole_joint.py`).

### 7.6 Limitations of what has actually been demonstrated
- **No Helmholtz-coil scans are in the repo.** Every dataset is coils-off with a permanent
  magnet. The coil uniformity plot (`plot_field_map.m` fig. 3) has only been run on synthetic
  `make_demo_scan` data. The README says v1 runs **outside** the coil cage.
- **Non-magnetic rule:** the servos have permanent magnets/steel (~0.15 G at the probe); the
  rod ends contain steel balls. This is handled by background subtraction, not eliminated.
- **The correction's validation evidence lives in another repo** (`engr489-REPORT`). Bring
  those numbers and plots if you'll cite 19 → 2.3 mm.
- **The firmware was never compiled with `arduino-cli`** in the dev environment (README).
  It clearly ran on the robot, given the scan data, but the build steps aren't recorded here.
- **The MATLAB→Python sensor link** (`mag_open`/`mag_read`/`mag_settle`) is untested in MATLAB.
- **Absolute accuracy isn't pinned down:** the 33 mm y offset and ~4° rotation in the dipole
  test are unexplained. The x accuracy is limited by the 100 mm-wide grid.
- **Drift ~11 mG per hour ≈ 8 mm of apparent position** at the median gradient
  (`REPEAT_TEST.md:62-72`). The only mitigation is procedural.
- **Workspace:** on-axis −540…−786 mm (effector), versus the planned −450…−750. The shallow
  ~100 mm of the original target is unreachable with −20° as the lower limit.
