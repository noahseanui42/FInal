# report_extract.md — evidence extracted from this repo for the ENGR489 report

Built from: `Report.md` (the skeleton), `ENGR489_Literature_Notes.md` (sources.md), every tracked file in the repo,
`git log --reverse --stat`, and the CSV/JSON scan data. There is no `CLAUDE.md` in this repo.

**How to read the citations**
- `path:line` = a line in a tracked file (paths are from the repo root). `commit abc1234` = a commit message.
- **[recomputed]** = not stated anywhere in the repo; I recalculated it from the committed CSVs/code with the scripts in
  `report_extract_checks/` (run from the repo root, e.g. `python3 report_extract_checks/check3_repeat_settle_replaced.py`; see Appendix B). Treat these as
  "the data support / don't support this", not as numbers the repo itself reports.
- "rationale not recorded" = the repo shows *what* was done but not *why*.
- Units: scan CSVs are in gauss. 1 G = 100 µT = 100 000 nT, so 1 mG = 100 nT (FieldScan/README.md:149-150).

## 0. What this repo does and does not contain (read first)

The repo is the **software + data** side of the project: robot firmware/GUI, scan runners, MATLAB/Python analysis, and
the scans from 2–6 Oct 2026. It does **not** contain:

- Any CAD, drawings, bill of materials, costs, supplier info, or mechanical design notes. Nothing about the $500 budget,
  the gantry → delta change, rod-end balls, the S3306MG servo, or Wilson's cage (`grep` for budget/gantry/S3306/Futaba/
  rod end/Wilson finds nothing in tracked files).
- Any **coils-on** scan of the Helmholtz cage. Every scan is coils-off with a permanent magnet or none
  (FieldScan/data/INDEX.md:3; DIPOLE_TEST.md:11; REPEAT_TEST.md:9). `coil_current_A` is `null` in the metadata I opened.
- The pen-and-ruler position data, the single-servo step test, the correction-model fitting (`refit_v2.py`) or the MATLAB
  workspace model. These live in other repos that are only *named* here: `noahseanui42/engr489-REPORT`
  (pose_correction.py:16-19; pose_correction_hybrid.json:27; FieldScan/README.md:83) and `noahseanui42/Matlab`
  (FieldScan/HANDOFF.md:6; it also refers to `Kinematics/` and `Simulink/` folders, FieldScan/HANDOFF.md:19-20,141-143,
  which are not in this repo). Results from those tests appear here only as summary numbers in comments/READMEs.
- Git history before 2 Oct 2026: the first five commits are whole-folder imports within 7 minutes
  (commit e27edff … 86a651c). Earlier events (26 Sep – 1 Oct) are known only from README/log text.
- Any citation of a `sources.md` entry (see §8).

Also note: the upstream commit hashes the docs mention (`a185b44`, `ffe256b`, `48a8038`) and the branch names
(`claude/amazing-lovelace-onixrv`, `claude/gallant-planck-stiamj`, `claude/brave-edison-mui291`) are not in this repo's
history; `git log` shows only the 38 commits listed in §2.

## 1. Repo purpose and active date range

**Purpose.** "Code and data for the ENGR489 capstone (VUW): a delta robot that moves a Phidget 1044 magnetometer probe
through a grid to map the magnetic field inside a Helmholtz coil." (README.md:3-5). Folder table: README.md:7-14. Supervisor named as Dr Christopher
Hollit (DeltaApp/README.md:3-4). Five folders:

| Folder | Role |
|---|---|
| `DeltaApp/` | Original (pre-calibration) servo firmware + patched upstream GUI + tests; "kept for comparison" (README.md:38). |
| `DeltaAppCalibrated/` | Same software with measured geometry, refitted servo calibration, upward-approach backlash handling and `tools/servo_sweep/`. README.md:12: "Use this one on the robot." |
| `FieldScan/` | MATLAB serial link, MATLAB-only fallback scan, and all 2 Oct 2026 scans. |
| `FieldTiltScan/` | FieldScan plus tilt/gyro logging; tilt scans, full-box scans, dipole test, 5-run repeat test. |
| `FieldPlots/` | MATLAB (and one Python) analysis and plotting. |

Also tracked: `ENGR489 Literature Notes.pdf` (added in commit 8dbb1ff, message "Add files via upload" / body "Source Notes").

**Active date range (git).** First commit e27edff on 2026-10-02 10:32 UTC; last commit 8dbb1ff on 2026-10-09 18:11 +1300
(the literature-notes PDF). Last *code/analysis* commit 23357dc, 2026-10-07 00:49 UTC. Last scan data: 2026-10-06
(repeat_none, `FieldTiltScan/data/repeat_none_20261006_192127.meta.json`, started 19:21 local). 38 commits:
21 by "Claude", 11 by "noahseanui42", 6 by "Noah-Seā Nui" (`git log --format=%an`). Four merged PRs (#1–#4:
968b204, 8e282af, c6d0af3, 6a9e996).

**Active range per documents (not git).** Work is dated back to **2026-09-26** (single-arm limits pass,
DeltaApp/README.md:75; also 81 "confirmed same day") and **2026-09-29/30** (CALIBRATION_LOG.md:3,21,63), with the
correction refit dated **2026-10-01** (pose_correction_hybrid.json:27). So: **repo work ≈ 26 Sep – 9 Oct 2026**, git
history only 2–9 Oct.

Timestamp caution: commit times mix UTC (`+0000`, Claude sessions) and NZDT (`+1300`, the user's own commits); scan
file names and `.meta.json` times are NZ local time. Example: ee59332 is dated "2026-10-03 01:35 +1300" but the scan
it adds ran 00:24–01:29 local on 3 Oct (`…under_combined_20261003.meta.json`, `started`/`finished`).

## 2. Timeline of key changes

Commits (hash, author date as recorded, one line). Rows marked † are not in git — taken from document text.

| Date | Commit | What |
|---|---|---|
| 2026-09-26 † | — | Pass 1 single-arm limits, then Pass 2 full-assembly limits −20°…70° (DeltaApp/README.md:73-95). |
| 2026-09-29 † | — | Arm 2 (D10) re-swept with ruler; `centre_us` 1385→1350, `us_per_deg` 10.0481→9.51; ~5 mm play at corner found (CALIBRATION_LOG.md:3-18). |
| 2026-09-30 † | — | Assembled on-axis protractor sweep (15 points × 3 arms); refit to D9 1456/9.8315, D10 1373/9.7664, D11 1393/9.6658 (CALIBRATION_LOG.md:63-90; sweep_2026-09-30_up.csv). Geometry "confirmed by user 2026-09-30" (joint_angle_calibration_test.xlsx, Setup!C14). |
| 2026-10-01 † | — | Hybrid pose-correction coefficients fitted in the other repo (pose_correction_hybrid.json:27). |
| 2026-10-02 10:32 UTC | e27edff | Import `DeltaApp/` (original, pre-calibration: SP 150, L_UP 180). |
| 2026-10-02 10:32 UTC | 2119617 | Import `DeltaAppCalibrated/`: SP 75, L_UP 177, GEOM_TO_PHYS remap, refit servo cal, upward approach, `tools/servo_sweep`. |
| 2026-10-02 10:34 UTC | d27e9a5 | Import `FieldPlots/` (maps, repeatability, tilt, dipole fit + synthetic tests). |
| 2026-10-02 10:34 UTC | 5dddaee | Import `FieldScan/` with the 2 Oct scans (background, magnet x±/under, off vs hybrid, aborted/check runs). |
| 2026-10-02 10:39 UTC | 86a651c | Import `FieldTiltScan/` (adds accel/gyro/pitch-roll per point) + first tilt run. |
| 2026-10-02 10:40 UTC | 2e753bc | Top-level README. |
| 2026-10-02 11:26 UTC | 2bfc796 | Tilt scan prints Bx,By,Bz per point. |
| 2026-10-02 11:44 UTC | 70c5070 | **Move timeout scales with move length** — fixed 30 s failed on the full-box grid (≈360 mm layer change, ≈40 s). |
| 2026-10-03 +1300 | ee59332 | Full-box 25 mm tilt scan, layer 1 and layers 2–4 (magnet logged as `xpos`). |
| 2026-10-04 02:30 UTC | 11ad578 | Join the two partial runs into one 260-point CSV. |
| 2026-10-04 02:31 UTC | 9bac831 | Rename: the magnet was *under* the grid, not +x. |
| 2026-10-04 16:58 +1300 | 4846d66 | Full-box no-magnet background scan. |
| 2026-10-04 04:02 UTC | 96988c4 | **Recover when the 1044 reconnects mid-scan** (background scan dropped at point 78). |
| 2026-10-04 17:47–19:25 +1300 | 10919c2, f0ce353, c9530d1 | Dipole known-position scans: floor, stand y0/±100, x±50. |
| 2026-10-04 06:01 UTC | d2af0be | DIPOLE_TEST.md + `fit_dipole_joint.py`; runs renamed. |
| 2026-10-04 06:26–06:27 UTC | 302648f, 8b06908 | Refit with x±50 runs; magnet height 260 mm above floor recorded. |
| 2026-10-05 01:45–01:51 UTC | a0da67a, 1fc8ec6 | `plot_field_layers` "Figures" option; `fit_dipole_joint.py --plot` → `dipole_joint_fit.png`. |
| 2026-10-06 19:38 +1300 | a33ede2 | 5-run repeatability test + no-magnet reference. |
| 2026-10-06 06:40–06:50 UTC | e2405e5, 21a8d36, baf2a6e, 1439c68 | REPEAT_TEST.md results; magnet height 270 mm; per-run tilt vs drift table. |
| 2026-10-06 23:57 UTC | f1fdef5 | `compare_heatmaps.m`. |
| 2026-10-07 00:14–00:49 UTC | 2711bf1, 3ec5507, cc40216, 03cf278, 6119016, 23357dc | `repeatability_heatmaps.m`, `compare_repeat_heatmaps.m`, file picker, mG units. |
| 2026-10-09 18:11 +1300 | 8dbb1ff | Literature-notes PDF added. |

## 3. Design decisions: chosen, rejected, why

"Where" gives the evidence. Where the repo records no reason I say so.

| # | Decision | Chosen | Rejected / alternative | Why (as recorded) | Where |
|---|---|---|---|---|---|
| 1 | Robot type | Delta robot, 3 hobby servos | Gantry (stated only in the skeleton, not in repo) | **rationale not recorded**; no gantry mention in tracked files | README.md:3-5 |
| 2 | Firmware base | New servo firmware on Arduino UNO R4 Minima, **same serial protocol** as upstream so the upstream GUI works with patches | Upstream stepper firmware (`grzesiek2201/Delta-Robot`) | Reason for servos over steppers **not recorded**; keeping the protocol = keep the GUI | DeltaApp/README.md:3-9 |
| 3 | MCU variant | UNO R4 **Minima** | R4 WiFi | "to avoid RF near the sensor" | FieldScan/HANDOFF.md:15-16 |
| 4 | Where the 1044 connects | Host PC over USB, "not into the Arduino" | Through the Arduino | Reason **not recorded** (skeleton's "keep field data off the control link" is not in the repo) | FieldScan/HANDOFF.md:24-25 |
| 5 | Control mode | **Open loop**, outside the coil cage (v1) | Pot feedback on A0–A2, closed-loop trim | Deferred as future work; reason **not recorded** (skeleton's "needs open-loop baseline first / pot can't see play" not in repo) | DeltaApp/README.md:11-12, 305-309 |
| 6 | Geometry convention | SB/SP are triangle **side** lengths through joint centres; forearm 625 mm | Radii; forearm 600/700 mm "the planning doc had flagged" | Confirmed with the user | DeltaApp/README.md:57-61 |
| 7 | Platform size SP | **75 mm** (inner triangle through forearm ball-joint centres, circumradius 43.3) | 150 mm (the plate outline) used first | The 75 mm triangle is what the ball joints sit on | DeltaAppCalibrated/delta_servo/config.h:14-16; DeltaApp/delta_servo/config.h:14 |
| 8 | Bicep L_UP | 177 mm | 180 mm | **rationale not recorded** (README calls SB "measured", not L_UP) | DeltaAppCalibrated/delta_servo/config.h:17 vs DeltaApp/delta_servo/config.h:15 |
| 9 | Arm numbering | Fix in software: `GEOM_TO_PHYS = [2, 0, 1]` | Re-bolt the base plate or re-wire pins | Marks came out rotated exactly 120° in the pen test; base plate's extra mounting-hole options let arms be bolted 120° round; software fix leaves per-servo calibration untouched. Revert to [0,1,2] if re-bolted | DeltaAppCalibrated/README.md:204-226; config.h:48-60 |
| 10 | Joint limits | −20°…70° from the **full 3-arm assembly** | Single-arm limits (≈−16…−25° / 26.5…29.5°) | Single-arm numbers "falsely tight": slack plate sags/tilts and hits early. −20/70 is "a safe margin", not the mechanical stop | DeltaApp/README.md:73-95; config.h:33-39 |
| 11 | Servo calibration method | Assembled on-axis sweep with digital protractor on each bicep; fit measured = s·cmd + o, then `us_per_deg /= s`, `centre_us -= o·new us_per_deg` | Per-arm ruler sweep (D10, 29 Sep); single-arm driving | Arms disagreed by up to ~10° and platform tilted before the refit; D9's first-run 11.8231 was the biggest error | CALIBRATION_LOG.md:63-90; config.h:24-31 |
| 12 | Backlash handling | **Upward final approach**: a move that ends with any bicep going down first dips 20 mm and rises into the target | Direct moves | Servos land differently going up vs down (≈1.3°, servo 2 ≈4.5°); all track within ≈0.5° when the last motion lifts. Cost ≈40 mm extra travel per move. `APPROACH_DZ_MM=0` disables | config.h:73-84; DeltaAppCalibrated/README.md:293-316 |
| 13 | Unreachable moves | IK returns false, **whole move rejected**, no partial angle writes; error code `e=1` | (clamping is the implied alternative) | Comment says "no partial writes to thetaDeg on failure"; skeleton's "clamping one servo would move the platform somewhere nobody commanded" is **not recorded** | delta_servo/kinematics.cpp:83-86; DeltaApp/README.md:141-145 |
| 14 | Position correction | Open-loop Jacobian-based "hybrid" (cx, cy, cx_mid), send = FK(IK(p) − Δθ), **no firmware change** | v1 centring model (corners identical); a v2 | Geometry deliberately stored **with** the coefficients, not read from `robot_config.py`, so a later geometry change can't silently invalidate the fit. Why hybrid beat v1/v2 (skeleton: LORO error 3.15 vs 3.76/3.35 mm) is **not in this repo** | pose_correction.py:9-28; pose_correction_hybrid.json:27 |
| 15 | Who runs the scan | `field_scan.py` (Python) drives robot + sensor and writes the CSV; MATLAB only post-processes | MATLAB-only `run_field_scan.m` (kept as fallback); GUI program mode with data log (removed) | Only one program can hold the serial port; GUI's 50-point program cap does not apply to Python; delta-app data log removed | FieldScan/HANDOFF.md:78-107; field_scan.py:4-8 |
| 16 | 1044 access from MATLAB | MATLAB's Python interface (`py.` calls to `Phidget22`) | Phidget22 MATLAB/C library | "so the user doesn't need Xcode" | FieldScan/HANDOFF.md:48 |
| 17 | 1044 channel | **Spatial** channel (field + accel + gyro in one event) | Separate Magnetometer/Accelerometer/Gyroscope channels | "don't open on our board" | field_scan_tilt.py:13-14 |
| 18 | Pitch/roll filter | `imu` default; "Use `imu`, not `ahrs`" | AHRS | AHRS steers by the magnetometer, which the magnet being mapped disturbs | FieldTiltScan/README.md:112-116 |
| 19 | Tilt correction input | Gravity vector from the accelerometer | Board's pitch/roll numbers | Same information at rest; independent of the board's angle order/signs; minimal rotation g→g_ref | FieldTiltScan/README.md:205-211 |
| 20 | Settling | Fixed **5 s** after the move (plus gyro-based option, off by default) | 0.5 s | Arms "keep swinging for a few s"; 0.5 s vs 5 s compared on the same magnet (§4) | field_scan.py:63; INDEX.md:53-57; FieldTiltScan/README.md:118-121 |
| 21 | Dipole fit | **Joint** fit: one shared moment, one position per run | Per-run fit | At this depth moment tilt and position trade off; single-run shifts came out 114/117 mm for 100 mm moves | DIPOLE_TEST.md:97-103; commit d2af0be |
| 22 | Dipole-test magnet placement | Magnet on a stand | On the floor (first attempt) | Floor magnet ≈500 mm below bottom layer; field too flat, fit ±40–110 mm. Kept as record, not used | DIPOLE_TEST.md:24 |
| 23 | Sensor mapping to robot axes | `R_sensor_to_robot = eye(3)` | Measured rotation | "Leave as eye(3) if mounted parallel"; sensor/robot alignment never verified (DIPOLE_TEST later finds ≈4° turn) | FieldScan/scan_config.m:28-30; DIPOLE_TEST.md:81-85 |
| 24 | Keep servos powered during/after scan | Yes | Power down (as in [19]) | "disabling lets the arms drop" | FieldScan/README.md:50-51 |
| 25 | Materials | PLA, carbon fibre, aluminium, nylon only near probe | — | "Hard rule: nothing magnetic near the probe". Nothing else about materials is in the repo (no rod-end, bearing or fastener mention) | FieldScan/HANDOFF.md:13-15 |
| 26 | Supply | "separate 6 V AA pack" / "4×AA supply" | — | **Not a bench supply** (skeleton III-E says bench supply). Sag is a named suspect if the stream stops | FieldScan/HANDOFF.md:17; DeltaAppCalibrated/README.md:396-398 |
| 27 | Folder structure | `FieldTiltScan` is a *clone* of `FieldScan` | Modify FieldScan | "`FieldScan/` itself is unchanged" | FieldTiltScan/README.md:3-6 |
| 28 | Host-testable firmware | Only `delta_servo.ino` touches Arduino APIs; `kinematics`, `protocol`, `motion` compile with plain g++ | — | Unit-testable on host | DeltaApp/README.md:49-51 |

**Not found anywhere in the repo** (so any rationale in the skeleton for these is unsupported by the repo):
gantry-vs-delta decision; S3306MG choice/torque check; rod-end exception; $500 budget; laser-cut plate; PLA hole
correction; frame alternatives; "from-scratch control stack with layered safety" (grep for heartbeat/slew/from-scratch
finds nothing — the skeleton's `[CHECK: cite the commit or cut]` should be **cut** unless the commit lives in another repo).

## 4. Quantitative results and parameters

Status column: **F** final/in use; **S** superseded (see §10); **D** documented in repo text only (underlying data not
in repo); **R** recomputed by me from committed data.

### 4.1 Geometry, limits, motion (firmware, `DeltaAppCalibrated/` unless stated)

| Parameter | Value | Cite | St. |
|---|---|---|---|
| SB (base triangle side) | 175 mm | delta_servo/config.h:13; delta_app/robot_config.py:11 | F |
| SB inradius w_b | 50.5 mm "measured" | README.md:117-118 | D |
| SP (ball-joint triangle side) | 75 mm; circumradius 43.3 mm; plate outline 150 mm | config.h:14-16; robot_config.py:12-14 | F |
| L_UP (bicep) | 177 mm | config.h:17; robot_config.py:15 | F |
| L_LO (forearm) | 625 mm | config.h:18; robot_config.py:16 | F |
| TCP offset | (0, 0, −21) mm, probe below effector ball-joint axis | robot_config.py:42 | F |
| Elbow joint width (plot only) | 35 mm | robot_config.py:45 | F |
| Joint limits | −20° … +70°, all three arms | config.h:42-44; robot_config.py:26 | F |
| Pulse clamp | 830–2170 µs | config.h:46 | F |
| Z guard / Z limit (probe) | −300 / −800 mm | robot_config.py:40-41 | F |
| Servo pins | D9, D10, D11 | config.h:42-44 | F |
| Arm remap | GEOM_TO_PHYS = [2, 0, 1] | config.h:60; robot_config.py:38 | F |
| Servo cal D9 / D10 / D11 (`centre_us`, `us_per_deg`) | 1456 / 9.8315; 1373 / 9.7664; 1393 / 9.6658 | config.h:42-44 | F |
| Same, before refit | D9 1460 / 11.8231; D10 1385 / 10.0481 (→1350 / 9.51 on 29 Sep); D11 1410 / 10.5544 | DeltaApp/delta_servo/config.h:35-37; config.h:29-31; CALIBRATION_LOG.md:7-9 | S |
| Planner tick / status stream | 20 ms / 20 ms | config.h:63-64 | F |
| Speed | 5 mm/s per `v` step (v 1–10 → 5–50 mm/s); default v = 2 (→ 10 mm/s) | config.h:66-67; FieldScan/README.md:63 | F |
| Joint-speed cap, min move time | 90°/s; 200 ms | config.h:68-69 | F |
| Move duration | T = max(dist/speed, max Δθ/90°/s, 200 ms) | delta_servo/motion.cpp:128-132 | F |
| Easing | smoothstep s = 3u² − 2u³ | motion.cpp:316 | F |
| Program points | 50 | config.h:70 | F |
| IK singularity guard | \|G−E\| < 1e-6 rejected | kinematics.cpp:24,38-40 | F |
| On-axis home height | z_home(θ=0) = −597.2 mm (platform centre) | tests/test_kinematics.py:37 (−597.2345…) | F |
| Upward approach | dip 20 mm; trigger 0.1°; floor −779 mm (= −800 − (−21)) | config.h:79-84 | F |
| Approach cost | ≈40 mm extra travel; ≈4 s at 10 mm/s (v2); 8 s at 5 mm/s | DeltaAppCalibrated/README.md:311-313 | D |
| Backlash | ≈1.3° per servo; servo 2 ≈4.5° ("≈4.6" is **not** in the repo); ≈0.5° when last motion is upward | config.h:73-76; README.md:296-299 | D |
| Servo 2 play | ≈5 mm at corner (~1.5°); 1° on one arm ≈ 9 mm sideways at z ≈ −700 | CALIBRATION_LOG.md:12-14 | D |
| Probe z per bicep degree | ≈3 mm/° near bottom (log); 3.1 mm/° assumed, 3.0–3.2 across −730…−620 (workbook) | CALIBRATION_LOG.md:73-74; joint_angle_calibration_test.xlsx Setup!B40,C40 | D |
| Probe z per degree, all 3 arms moving, at (0,0,−650) | 3.21 mm/° (1.07 mm/° per arm) | [recomputed] check6 (`pose_correction.jacobian`) | R |
| Reachable on-axis z | −540 … −788 mm (platform-centre z); θ=−20° → −539.9, θ=70° → −787.6 | DeltaAppCalibrated/README.md:166-171; [recomputed] check7 | F/R |
| Reachable fraction of 25 mm grid x,y ∈ ±150, z −790…−565 | "~89% (1501/1690)" in README — **that is the old SP150/L_UP180 geometry**; calibrated geometry gives 1414/1690 = 83.7% | DeltaAppCalibrated/README.md:172; DeltaApp/README.md:106; [recomputed] check7 | S/R |
| R2 box (x ±50, y ±150, z −600…−700 probe) reachable | all corners and a 10 mm dense grid reachable (probe z → platform z −21) | [recomputed] check7 | R |
| Old reachable range | z ≈ −550 … −793 | DeltaApp/README.md:102-103 | S |
| Planning-doc scan target | z ≈ −450 … −750 mm | DeltaAppCalibrated/README.md:166 | S |

### 4.2 Calibration sweep (30 Sep) — numbers in the repo vs recomputed

| Item | Value | Cite | St. |
|---|---|---|---|
| Sweep design | on-axis, probe z −740 lead-in then −730 → −590 in 10 mm steps, moving up, no Home between; digital protractor, positive = down | CALIBRATION_LOG.md:65-70; sweep_2026-09-30_up.csv:1-17 | F |
| Points | 15 per arm × 3 = 45 (lead-in excluded) | sweep csv rows 3-17 | R |
| Pre-refit error at −730 | D9 +7.2°, D10 −2.4°, D11 +4.9° | CALIBRATION_LOG.md:71-72 (matches csv row 3) | D |
| Pre-refit rms, all arms | **3.43°**; per arm 4.13 / 2.81 / 3.20°; max 7.16 / 3.86 / 4.86°; within ±1°: 4 of 45 = 9% | [recomputed] check6 (sweep csv, `meas − cmd`) | R |
| Max between-arm spread | 9.8° (at −720: 38.7 − 28.9) | sweep csv row 4 | R |
| Fit | D9 s 1.203 o +0.37°; D10 s 0.974 o −2.38°; D11 s 1.092 o +1.73°; max residual 1.0 / 1.3 / 0.5° | CALIBRATION_LOG.md:78-82; config.h:42-44 | D |
| New gains | all ≈ 9.7–9.8 µs/° | CALIBRATION_LOG.md:84 | D |
| **Post-refit** error | **No post-refit sweep is in the repo.** The log lists it as "Next" (lines 91-94) and "Down pass … not measured yet" (line 89). In-sample fit residual: rms 0.46° (0.49° dof-corrected), per arm 0.48 / 0.58 / 0.25°, max 1.04 / 1.25 / 0.50°, 42 of 45 (93%) within ±1° | [recomputed] check6 | R |
| Target for re-test | every arm within ±0.5°; rule of thumb "< ~0.3°" | CALIBRATION_LOG.md:94; joint_angle_calibration_test.xlsx Analysis!A9 | D |
| Wiggle noted | at −590 D9, D10 read ≈2° above trend | CALIBRATION_LOG.md:87-88 | D |

### 4.3 Position correction

| Item | Value | Cite | St. |
|---|---|---|---|
| Uncorrected shortfall | ≈13% of distance from centre, towards the axis; ≈19 mm rms at box corners | pose_correction.py:3-5; FieldScan/README.md:73-75 | D |
| Corrected | corner error ≈19 → 2.3 mm rms; box spans 100 × 299 mm at z −650 | pose_correction.py:20-21; FieldScan/README.md:79-80 | D |
| Repeatability (pen) | 2–2.5 mm | FieldScan/README.md:81 | D |
| Residual centre error at z −650 | ≈5 mm, attributed to platform tilt | FieldScan/README.md:81-82 | D |
| Model | Δθ = β_x f_cx + β_y f_cy + β_mid f_cx(1 − (y/150)²); f = Jᵀ(−x,0,0) or (0,−y,0) "in degrees"; send = FK(IK(p) − Δθ) | pose_correction.py:9-14,126-131,148-158 | F |
| β | β_x = β_y = 5.387484e-07; β_mid = 2.677471e-07 | pose_correction_hybrid.json:9-11 | F |
| Units of β | Features are computed in **degrees** (`np.degrees`, pose_correction.py:129-131); `predict_offset_deg` (line 145) returns degrees; `compensate` converts with `np.radians` (line 154). So β output is degrees | pose_correction.py:126-154 | F |
| Δθ magnitude | at (50, 0, −650): 0.79° / −0.82° / 0.00° (D9/D10/D11); at (50, 150, −700): 1.48° / 0.48° / −2.18° | [recomputed] check6 (`PoseCorrection.predict_offset_deg`) | R |
| Validity box | x ±50, y ±150, z −700…−600 (probe); script warns outside | pose_correction_hybrid.json:13-26; field_scan.py:331-343 | F |
| Fit data | "v1 centring on protractor runs 2, 5, 6; mid-box x term on pen-and-ruler box and midpoint tests, runs 10–19" | pose_correction_hybrid.json:27 | D |
| Correction actually applied (sent − target) | centre 0; x = ±50, y = 0: 8.3–11.5 mm (layer-dependent); corners (±50, ±150): **17.5–26.6 mm** (xy part 16.9–25.7 mm); max over 260 points 26.6 mm | [recomputed] check6, from `full25-4z_corr-hybrid_under_combined_20261003.csv` columns `sent_*` − target | R |

### 4.4 Sensor and scan settings

| Item | Value | Cite |
|---|---|---|
| Sensor | Phidget 1044_0 "PhidgetSpatial Precision 3/3/3 High Resolution", serial 302277 | FieldScan/HANDOFF.md:24; `…meta.json` `sensor.name`, `sensor.serial` (e.g. repeat_under-run1_20261006_180203.meta.json:56-57) |
| Range (read from board) | max field **5.6 G** per axis, accel 8 g, rate 2000 °/s | same meta.json `sensor.max_field_G`; resolves HANDOFF.md:26-28 where ±8 G was unconfirmed |
| Data interval, samples | 20 ms; 20 readings averaged per point | meta.json:58; field_scan.py:69-70 |
| Settle | 5.0 s (Python); MATLAB fallback default still 0.5 s | field_scan.py:63; FieldScan/scan_config.m:11 |
| Park | (0, 0, −650) | field_scan.py:64 |
| Default grid | x ±50, y ±50, z −700…−600, 5 each | field_scan.py:65-67; FieldScan/README.md:62 |
| Speed | v = 2 (10 mm/s) | field_scan.py:61 |
| Move timeout | 30 s + (distance + 2·20 mm)/(5 mm/s × v) | field_scan.py:62,204-218 |
| Expected local Earth field | 0.55–0.6 G | FieldScan/HANDOFF.md:30-31 |
| Scan-time per point | ≈13.5 s median (full-box background) | [recomputed] check2 (`t_s` diff) |

### 4.5 Scan results stated in repo docs

| Result | Value | Cite |
|---|---|---|
| 2 Oct main set | 5 × 5 × 3 = 75 pts, x,y ±50, z −675/−650/−625; magnet on +x side | FieldScan/data/INDEX.md:34-35 |
| Magnet-under repeat pair | median difference 0.005 G per point; first placement differs by ≈0.06 G median | INDEX.md:70-72 |
| Close magnet | 1.1 G at (+50, 0, −650), peak 1.87 G | INDEX.md:55 |
| Full-box (3 Oct magnet; 4 Oct background) | 260 pts, 25 mm in x/y; 4 z layers | commit 11ad578; `…under_combined_20261003.meta.json` (`note`, `points_done` 260) |
| Dipole test grid | 3 × 7 × 2 = 42 pts (x −50/0/50; y −150…150 step 50; z −700, −600); 5 s settle, 20 readings, speed 2, ≈10 min/run | DIPOLE_TEST.md:12-16 |
| Dipole: magnet-only field | 0.04–0.25 G (median ≈0.1 G), ≈250× sensor noise; all 210 pts reached | DIPOLE_TEST.md:37-39 |
| Dipole joint fit | positions (y0 (4.6, −32.7, −981.2); y+100 (12.3, 68.0, −978.5); y−100 (1.6, −133.0, −981.9); x−50 (−35.1, −29.2, −980.3); x+50 (60.1, −38.8, −977.1)) mm; 1σ ≈ (3.9–4.0, 2.7–2.9, 1.9–2.0); moment 2.71 A·m², 7.8° from vertical; residual rms 0.0125 G over 210 pts | DIPOLE_TEST.md:57-65 |
| Dipole moves | y0→y+100: 100 → 101.1 (+1.1, 1σ 3.8); y0→y−100: 100 → 100.3 (+0.3, 4.0); y−100→y+100: 200 → 201.3 (+1.3, 4.0); y0→x−50: 50 → 39.9 (−10.1, 5.5); y0→x+50: 50 → 55.9 (+5.9, 5.5); x−50→x+50: 100 → 95.7 (−4.3, 5.5) mm | DIPOLE_TEST.md:67-74. Per-move 1σ (3.8 / 4.0 / 4.0 / 5.5 / 5.5 / 5.5 mm, the skeleton's Table VIII column) is printed only by the `--plot` table (fit_dipole_joint.py:143-147), not by DIPOLE_TEST.md (≈4 mm per position, ≈5.5 mm per difference, lines 78-79). Re-running the joint fit [recomputed] reproduces the positions, moment (2.71 A·m², 7.8°), residual (0.0125 G) and lengths to ±0.1 mm |
| Dipole: rotation | y moves 3.0°, x moves 5.8° clockwise from above → ruler ≈4° off robot axes or sensor turned in holder | DIPOLE_TEST.md:81-85 |
| Dipole: absolute offset | magnet at mark fits (5, −33) mm; 3 Oct magnet-under scan fitted y ≈ −31 mm | DIPOLE_TEST.md:88-91 |
| Dipole: depth | ≈280 mm below bottom layer (planned 150); magnet 260 mm above floor → floor ≈ z −1240 | DIPOLE_TEST.md:92-95 |
| Dipole: single-run fits | ±7 mm (1σ); moment tilt 10–28°; 100 mm moves read 114 and 117 mm | DIPOLE_TEST.md:99-102 |
| Repeat test grid | 5 × 7 × 2 = 70 pts (x −50…50 step 25; y −150…150 step 50; z −700, −600); 5 s settle; ≈14 min/run; 18:05–19:18 | REPEAT_TEST.md:10-12 |
| Repeat: reached | all 70 pts, `err` 0, 20 readings each; two 1044 USB reconnects (run 4 before pt 1, run 5 before pt 54) | REPEAT_TEST.md:26-29 |
| Repeat: field spread | per-point 1σ of \|B\| over 5 runs: 2.0 mG median, 4.8 mG p95; after per-run uniform offset: 1.9 / 4.0 mG; one-point sensor noise ≈0.2 mG per axis → spread ≈10× noise | REPEAT_TEST.md:37-42 |
| Repeat: drift | ≈11 mG (1.1 µT) over the hour, uniform; run 5 vs run 1 = (+9.3, −4.9, +1.1) mG, size 10.6 mG | REPEAT_TEST.md:50-56,62-63 |
| Repeat: tilt | mean pitch 1.04→1.13°, roll −0.50→−0.43° over the runs; Δ +0.094° pitch, +0.074° roll by run 5; "explains about 17%" of the drift | REPEAT_TEST.md:50-56,64-66 |
| Repeat: gradient | 1.16 mG/mm median → 11 mG ≈ 8 mm apparent position | REPEAT_TEST.md:70-72,117-118 |
| Repeat: σ_pos | 2.2 mm median (2.8 p75, 4.9 p95); 1.7 mm with uniform drift removed; "matches the 2–2.5 mm from the pen-and-ruler tests" | REPEAT_TEST.md:76-79 |
| Repeat: fitted magnet position | with per-run offset: agree to 0.7 (x), 0.2 (y), 1.1 (z) mm 1σ, all within 2.1 mm of mean; without offsets x walks 10.6 mm | REPEAT_TEST.md:79-83 |
| Repeat: heat-map differences | consecutive runs 1.5–1.9% mean per point (max 9.2%); vs run 1 grows 1.7% → 3.1%; in mG 1.4–1.9 mG median (2.3–3.1 RMS, max 11.7) | REPEAT_TEST.md:107-113 |
| Repeat: magnet height | 270 mm above floor; fitted depth ≈ −975…−990 | REPEAT_TEST.md:13-18 |
| First tilt run (2 Oct) | script prints tilt/ΔB statistics for `magnet_tilt_20261002_223300` | FieldTiltScan/figures/magnet_tilt_20261002_223300/make_correction_change.py:55-58 (output not stored) |
| Reduced averaging after reconnect | 4 Oct background: 1044 dropped at point 78; two points got no data and the remaining 181 got 11–12 readings (256 ms) instead of 20 | commit 96988c4 |

### 4.6 Recomputed from the committed CSVs

All via `report_extract_checks/` (repo root). Numbers marked ✓ agree with the skeleton; ✗ do not.

| Quantity | Recomputed | Skeleton says | |
|---|---|---|---|
| Per-axis SD of the 20 samples (pooled over rows with 20 samples, 5727 values) | median 72 nT, max 426 nT (per-file medians 64–86 nT) [check1] | 76 nT, max 430 | ≈ ✓ (median 72 vs 76) |
| Background \|B\| (2 Oct 5×5×3 no-magnet) | 71.2–72.9 µT (median 72.0) | 71.2–72.9 µT | ✓ for that scan only |
| Background \|B\| (4 Oct full-box) / (6 Oct repeat ref) | 68.1–70.8 µT / 68.4–71.2 µT | — | different from the 2 Oct range |
| Full-box map, bottom layer peak / top | 53.5 µT at (0, −25) / 16.8 µT at (0, −25); layer peaks 53.5, 33.9, 23.5, 16.8 µT | 54 → 17 µT, peak y ≈ −25 | ✓ |
| Full-box durations | magnet 64.5 min; background 57.5 min | 57–64 min | ✓ |
| Probe tilt vs grid centre, full-box | median 1.19° (bg) / 1.22° (magnet); max 2.55° / 2.67°; median at \|y\|=150 ≈ 2.0–2.1° vs 0.48° at y=0 | median 1.2°, max 2.7°, rises with \|y\| | ✓ |
| Tilt repeatability (3 Oct vs 4 Oct, 258 pts) | r = 0.96; median \|difference\| **0.11°** | r = 0.96, median 0.19° | r ✓, difference ✗ |
| First tilt-corrected run (75 pts) | tilt median 0.87°, max 1.92°; ΔB median 1.61 µT, max 4.23 µT, max 3.3% of \|B\| | 1.6 µT median, 4.2 max, 3.3% | ✓ |
| Drift run 5 vs run 1 | (+931, −492, +107) nT | +940, −490, +110 | ✓ |
| Tilt-predicted drift | (−132, +107, +29) nT; cosine with observed −0.95; ≈ 1/6 of size (mean \|pred\| 276 nT vs 1058 nT) | opposite sign, ≈1/6 | ✓ — **contradicts** REPEAT_TEST.md:64-66 ("explains about 17%") |
| 5-run spread of \|B\| | median 202 nT; 186 nT after per-run vector-offset removal; p95 481 / 406 [check3] | **180 nT** | ✗ (repo doc 200 / 190 nT; recompute 202 / 186) |
| σ_pos from 5-run spread (spread ÷ gradient of the run-mean \|B\|, as `compare_runs.m` does; median gradient 116 nT/mm) | 2.15 mm raw; 1.72 mm offset-removed [check3] — **agrees with REPEAT_TEST.md:76-78 (2.2 / 1.7 mm)**. Using the gradient of the magnet-only field (median 126 nT/mm) gives 1.84 / 1.47 mm | ≈1.5 mm | ✗ for the repo method; ≈1.5 only with the magnet-only gradient and offset removal |
| Settle 0.5 s vs 5 s (same magnet, 75 pts) | median difference 816 nT, max 1711 nT; run times 8.2 vs 13.8 min | 820 / 1700 nT; 13.8 min | ✓ |
| Magnet re-placed (first placement vs replaced) | median 5958 nT ≈ 6 µT; replaced1 vs replaced2 483 nT | 6 µT, ">30× repeatability" | ✓ vs 6 Oct repeatability (≈0.19 µT → 31×); only 12× vs the 2 Oct pair (0.48 µT) |
| Exact-zero mean components | 54 of 6276 (0.86%) over 2092 rows | 0.8% | ✓ |
| In-situ check (2 Oct 5×5×3, off vs hybrid, two runs each, gradient by 25 mm finite difference of "off" map, e = sent − target) | k = 1.13, r = 0.93, n = 225; residual rms 291 nT; run-to-run rms difference 234 nT (off), 243 nT (hybrid); max \|e\| 10.7 mm | k 1.13, r 0.93, 225 values, 280 nT residual, 230 nT run scatter | ✓ (residual 291 vs 280). **No script for this analysis is in the repo** (mine: check4). |
| Magnet field at (+50, 0, −675) / (−50, 0, −675), 2 Oct, background-subtracted | 23.7 µT / 7.3 µT | 24 µT / 6 µT | + ✓ / ≈ (7.3 vs 6) |

## 5. Test procedures and methods actually used

Evidence-backed (data or documented run) unless marked *planned*.

1. **Joint-angle calibration, assembled** (30 Sep). On-axis (x=y=0) up-pass, probe z −730→−590 step 10 mm, joint mode,
   no Home between, digital protractor on a flat face of each bicep, linear fit, update CAL (CALIBRATION_LOG.md:65-90;
   sweep_2026-09-30_up.csv). Bench sketch `tools/servo_sweep/servo_sweep.ino` drives a raw pulse
   (servo_sweep.ino:1-8). Earlier: ruler-and-height method on arm 2 (CALIBRATION_LOG.md:5-11; `servo2_angles.xlsx`:
   R = 18.5 cm, shaft 10 cm below top wood, corner 9 cm flat).
2. **Planned, no recorded data:** play test on arms 1 and 3 (CALIBRATION_LOG.md:30-34), ruler sweeps on D11/D9
   (lines 36-43), assembled flat check (47-51), verify step with targets "drift ≤ ±5 mm over −550…−790, pen gap ±2 mm"
   (53-57). `joint_angle_calibration_test.xlsx` is a **blank template**: up pass −730→−570 then down pass (34 rows),
   repeatability 3 points × 3 repeats going Home between, off-axis check at (±60, 0) and (0, ±60) for pin order.
   `servo_calibration_sheet.xlsx` is also blank (templates for D9/D10/D11).
3. **Pen-holder bench test.** Marker in a printed holder marks each commanded point on paper; marks measured against the
   grid; outside the coil so the non-magnetic rule doesn't apply to the holder. It exposed the 120° arm mismatch with a
   9-point test. TCP offset for the pen was **not yet measured** when this was written (DeltaAppCalibrated/README.md:180-226).
   Results are summarised only (§4.3); raw data is in the other repo.
4. **Kinematic/Jacobian step test, box tests, leave-one-run-out validation:** referenced by the skeleton, **not in this repo**.
5. **Host-side software tests** (pytest + g++): FK/IK round trip and on-axis regression; C++↔Python IK parity;
   protocol parser (10 cases); motion planner (17 cases incl. approach dip/rise); config sync
   (DeltaAppCalibrated/README.md:400-415; DeltaApp/README.md:261-273). Tolerances: FK/IK round trip loosened to 0.2 mm
   because upstream `calculateFPK` nudges z by ±0.01 mm on equal-angle poses (bias up to ≈0.17 mm)
   (README.md:416-424); parity test skips ill-conditioned points (README.md:425-431).
   **Test count I got** [recomputed, pytest installed]: `DeltaAppCalibrated/tests` 39 collected, 39 pass;
   `DeltaApp/tests` 35 pass; `FieldTiltScan` 17 collected, 14 pass and 3 fail only because `Phidget22` is not installed
   here (`ModuleNotFoundError`). The skeleton's "27" is not reproducible; the repo's own counts are 17 (HANDOFF.md:98,
   at that time), "17 tests" (FieldTiltScan/README.md:240), 11 → 17 motion cases (DeltaApp vs Calibrated README).
   Default `--simulate` mode with `FakeLink`/`FakeMag` runs scans with no hardware (HANDOFF.md:90-92).
6. **MATLAB side tested in Octave only** on synthetic data (`test_tilt_correct.m`, `test_fit_dipole.m`,
   `test_compare_tilt_runs.m`): FieldTiltScan/README.md:239-245; commit a0da67a ("Checked in Octave"). HANDOFF.md:69
   says "none of the `.m` files has been run in MATLAB" (at hand-off time); FieldTiltScan/README.md:245-246 repeats that
   the MATLAB→Python link had not been run. Whether the plots in `figures/` came from MATLAB or Octave is **not recorded**.
7. **Bench dry runs** of the scanner: 3×3×3 (x,y ±25) dry run, 2-point magnet checks (INDEX.md:79-85).
8. **Magnet repeatability, correction off vs hybrid** (2 Oct): 5 × 5 × 3 grid, runs alternating off/hybrid (times
   18:00, 18:28, 18:44, 18:58 per file names) so drift averages; background `nomagnet_corr-off_run1_20261002_172221`.
   Analysis via `compare_runs.m` (σ of \|B\| per point ÷ \|∇\|B\|\| → σ_pos, noise floor subtracted in quadrature)
   (compare_runs.m:2-25; FieldScan/README.md:116-132).
9. **Settle-time comparison:** same magnet position, 0.5 s vs 5 s (INDEX.md:53-57).
10. **Magnet re-placement:** take the magnet away and put it back (INDEX.md:59-72).
11. **Full-box map:** 260 points, 25 mm x/y, four z layers, magnet under grid (3 Oct) and no-magnet background (4 Oct).
12. **Dipole known-position test** (4 Oct): magnet on a stand moved by ruler distances along x and y; joint dipole fit;
    shifts independent of how the floor mark is aligned (DIPOLE_TEST.md:1-8).
13. **5-run repeatability test** (6 Oct): back-to-back runs with nothing touched, then magnet removed
    (REPEAT_TEST.md:1-6).
14. **Tilt/gyro logging**: gyro zeroed at park position; fixed settle wait (`settle_mode: fixed`, meta.json `tilt`);
    pitch/roll from the accelerometer because the board's IMU filter was refused (§6).
15. **Dipole model:** B = µ0/(4π)(3(m·u)u − m)/\|r\|³ with least-squares fit from three start heights × three x-moment
    guesses (fit_dipole_joint.py:20, 58-62). 1σ from the fit covariance with independent residuals assumed, "so lower
    bounds" (fit_dipole_joint.py:21).

## 6. Problems hit and workarounds

| Problem | Workaround / outcome | Where |
|---|---|---|
| R4 USB CDC gave no data until DTR asserted | `SERIAL_DTR = True`; set before `open()` | DeltaAppCalibrated/README.md:323-326; robot_config.py:48; field_scan.py:120 |
| R4 `Servo.writeMicroseconds()` is a no-op before `attach()`; `attach()` writes 1500 µs | Call `attach()` then `writeMicroseconds()` straight after; 1500 µs is inside the 830–2170 range | DeltaApp/README.md:152-167 |
| macOS Dark Mode white-on-white labels; missing Program/COM menus; window clipped on 1440×900 | `option_add` colours; moved menu items into cascades; window sized to screen, 3D plot 6→4.8 in | DeltaApp/README.md:179-208 |
| Single-arm joint limits were falsely tight (plate sag) | Re-measured with all three arms | DeltaApp/README.md:73-95 |
| Large initial calibration error (arms disagreed ≤ ~10°, platform tilted) | Assembled sweep + linear refit | CALIBRATION_LOG.md:71-86 |
| Servo 2 has ≈5 mm play; servos land differently up vs down (≈1.3°, 4.5°) | Upward final approach | CALIBRATION_LOG.md:12; config.h:73-84 |
| Pen test marks rotated exactly 120° | `GEOM_TO_PHYS = [2,0,1]` in firmware and GUI | DeltaAppCalibrated/README.md:204-226 |
| Paper plate off level → pen higher on −x | Levelled | CALIBRATION_LOG.md:19 |
| Servos give way off-centre (≈13%, ≈19 mm at corners) | Jacobian-based open-loop correction | pose_correction.py:3-14 |
| ~5 mm centre error remains at z −650 | Attributed to platform tilt; "no servo-angle correction can remove" | FieldScan/README.md:81-82 |
| **`--speed` silently ignored**: sent as JSON float `2.0`; ArduinoJson `doc["v"] \| 0` reads a float as 0, firmware falls back to `V_DEFAULT` | Send as int; `--speed` is int 1–10; regression test | FieldScan/HANDOFF.md:93-98 |
| Upstream GUI FK biased by ±0.01 mm z-nudge; IK ill-conditioned near small (G−E) (float32 vs float64) | Loosened tolerance; skip those points in parity test; not a port bug | DeltaApp/README.md:275-291 |
| Upstream operator-precedence bug | Fixed in `deltarobot.py` | deltarobot.py:162 |
| `arduino-cli compile` against the real target was never run (downloads.arduino.cc blocked in that container) | Compiled against a hand-written `Arduino.h`/`Servo.h` stand-in with `-Wall -Wextra`, 0 warnings; user told to compile before flashing | DeltaApp/README.md:293-303; DeltaAppCalibrated/README.md:434-443 |
| 1044 not detected on user's M2 MacBook Air via USB-C adapter | Moved to another Mac ("Rochelle's MacBook Pro"); scan machine | FieldScan/HANDOFF.md:36-38 |
| Status stream backs up when nobody reads it → stale `en=0` / `mv=0` lines fooled enable/arrival checks | Background reader thread; `flush_input()`; ignore lines < 100 ms after a command | field_scan.py:104-111, 220-222 |
| Fixed 30 s move timeout failed on the full-box grid | Timeout = move duration + 30 s margin | commit 70c5070; field_scan.py:204-218 |
| Full-box scan stopped at a layer change (two partial runs) | Re-run layers 2–4, joined into one 260-point CSV; originals kept | commits ee59332, 11ad578 |
| Magnet mislabelled: scan started with `--magnet xpos` but magnet was under the grid | Renamed; originals keep recorded label + `renamed_from` / `magnet_actual` | commit 9bac831 |
| `dipole_x+50` started with `--magnet x-50`; an empty aborted x−50 start | Renamed; aborted run moved to `checks/` | commit 302648f |
| **1044 dropped off USB mid-scan** (background scan, point 78): Phidget22 reopened it with defaults → two points no data, 181 points with 11–12 readings at 256 ms instead of 20 | Script now restores interval/filter, re-reads once after 5 s, logs `sensor_reconnected_at_points`. **The 4 Oct background scan itself was not re-run**: it has 138 pts with 12, 42 with 11, 1 with 7, 2 with 0 samples; only 77 have 20 [recomputed]. That background is used for the full-box map and the dipole test. Its per-axis SD (median 23 nT) is not comparable with the 20-sample scans (72 nT) [check1, check5] | commit 96988c4; FieldTiltScan/README.md:251-255 |
| Gyro zero lost after a reconnect (gyro columns biased) | Field and accel unaffected; run 4 gyro ≈1.2 °/s high | FieldTiltScan/README.md:253-255; REPEAT_TEST.md:28-29 |
| Board's IMU/AHRS filter refused: `PhidgetException 0x14 (Operation Not Supported)` | `pitch_deg`/`roll_deg` are NaN in these scans; `acc_pitch_deg`/`acc_roll_deg` and the gravity vector are used. `sensor.algorithm` is `"none"` in the meta.json even though `config.algorithm` is `"imu"` and README says imu is the default | repeat_under-run1_20261006_180203.meta.json:50-55; full25-4z_corr-hybrid_none_20261004_155505.meta.json:54-55; field_scan_tilt.py:126-129 |
| Dipole single-run fits unreliable (moment tilt trades off with position) | Joint fit with shared moment | DIPOLE_TEST.md:97-103 |
| Floor magnet too far for a fit | Stand | DIPOLE_TEST.md:24 |
| Dipole depth ≈280 mm, deeper than planned 150 mm | Noted; x grid only 100 mm wide so x poorly pinned | DIPOLE_TEST.md:77-79,92-95 |
| Uniform field drift ≈1.1 µT/h ≈ 8 mm apparent position | Per-run offset in fits; background close in time; warm-up; cause unresolved ("likely thermal", "30 min fixed-point log would separate") | REPEAT_TEST.md:62-72 |
| `gradient()` dimension-order bug in `compare_runs.m` | `[Gy,Gx,Gz] = gradient(V, ys, xs, zs)`; `prctile` replaced | FieldScan/HANDOFF.md:114-121 |
| MATLAB↔Python (`pyenv`) risk; 1044 events arrive on a Python thread | Run Python out-of-process | HANDOFF.md:69-76; FieldTiltScan/README.md:229-232 |
| Phidget22 reports unknown / out-of-range values as 1e300 | Treated as unknown (`UNKNOWN = 1e100`) | field_scan_tilt.py:72 |
| Run metadata placeholder: `"note": "repeatability run 1 of 5, magnet fixed at ___"` | Unfilled; magnet height added later in meta | repeat_under-run1_20261006_180203.meta.json (`note`); commit baf2a6e |
| `out_dir` in metadata is `/Users/rochelle/engr489-delta-robot/host/Matlab-tiltscan/FInal/…` (scans were run on another user's Mac) | — | meta.json `config.out_dir` |

## 7. Figures: which script makes which plot, from which data

| Skeleton figure | Generated by | Data | In repo? |
|---|---|---|---|
| Fig 1 architecture | — (diagram; ASCII version only) | DeltaAppCalibrated/README.md:53-111 | text only |
| Fig 2/3 geometry, reachable workspace | MATLAB workspace model — **not in repo**. `calculateworkarea.py` is upstream code that reads a `working area/contours_light.txt` file that isn't tracked (calculateworkarea.py:70) | — | **no** |
| Fig 4/5 CAD / wiring | — | — | **no** |
| Fig 6 correction vectors | `FieldPlots/plot_correction_map.m` (arrows sent − target per z layer, `'Save'`→`<name>_correction.png`) | any `--correction hybrid` CSV, e.g. `FieldScan/data/magnet-xpos_corr-hybrid_run1_20261002_182828.csv`, `FieldTiltScan/data/full25-4z_corr-hybrid_under_combined_20261003.csv` | script yes, PNG not stored |
| Fig 7 bicep error vs height before/after | none | `sweep_2026-09-30_up.csv` (before only) | **no script**; after-refit data not in repo |
| Fig 8 box tests (pen) | none | other repo | **no** |
| Fig 9 in-situ correction check | none (my recompute is `report_extract_checks/check4.py`) | off/hybrid runs 1–2 in `FieldScan/data` | **no script** |
| Fig 10 dipole fitted vs ruler | `FieldPlots/fit_dipole_joint.py --plot` → `FieldTiltScan/data/dipole_joint_fit.png` (command in DIPOLE_TEST.md:45-55) | `full25-4z_corr-hybrid_none_20261004_155505.csv` (bg) + 5 dipole runs | **yes (PNG tracked)** |
| Fig 11 full-box map | `plot_field_layers.m` (heat, direction, side, 3D; `"Figures"` option from a0da67a) and `plot_field_arrows3d.m` | `…under_combined_20261003.csv` minus `…none_20261004_155505.csv` | script yes, PNG not stored |
| Fig 12 repeatability heat map | `repeatability_heatmaps.m` → `compare_heatmaps.m`; or standalone `compare_repeat_heatmaps.m`; σ_pos maps via `compare_runs.m` + `plot_repeatability_layers.m` | `repeat_under-run1…5` minus `repeat_none_20261006_192127` | script yes, PNG not stored |
| Fig 13 drift | no dedicated plot; table in REPEAT_TEST.md:50-57 | `repeat_*` | table only |
| Fig 14 probe tilt | `plot_tilt.m` (tilt map, gyro settling, pitch/roll maps, board-vs-accel check) | scans with accelerometer columns, e.g. `full25-4z_…` | script yes, PNG not stored for the full-box scan |
| (extra) first tilt run | `plot_field_layers/plot_tilt/plot_field_arrows3d` → `raw_fig1-4.png`, `tilt_fig1-3.png`, `tiltcorr_fig1-4.png`; `make_correction_change.py` → `correction_change.png` | `magnet_tilt_20261002_223300.csv` and `…_tiltcorr.csv` | **yes (PNGs tracked)** |

Only 13 PNGs are tracked (12 for the first tilt run, 1 dipole fit). Tilt-correction maths: `tilt_correct.m`, `apply_tilt.m`
(rotate field so measured gravity matches a reference, FieldTiltScan/README.md:205-211).

## 8. External code, libraries, papers — flagged against sources.md

`sources.md` (the literature notes) indexes **23** keys (wang2002improved … futaba2010s3306mg;
ENGR489_Literature_Notes.md:9-49). **None of them is cited or named anywhere in the repo's tracked text files** (case-insensitive grep over
`.md/.py/.m/.h/.cpp/.ino/.json` for author names, product names and cite-key stems — Wang, Sobko, Senis, Metrolab/HallinSight, Nogiec/Mu2e, Clavel,
Williams, Bentaleb, Tira-Thompson, Pollak, Uscategui, Cervettini, Alken, Tsekos, Farooq, Yang, Omelyanchik, Futaba — returns no hits outside this file).
The PDF `ENGR489 Literature Notes.pdf` is the notes themselves.

Used in the repo and **NOT in sources.md** (⚑):

| Item | Where used | Licence / note |
|---|---|---|
| ⚑ `grzesiek2201/Delta-Robot` @ `48a8038` (Jakub Wrona, Grzegorz Radziwiłko) — GUI, IK, three-sphere FK, protocol | every ported file header, e.g. delta_app/main.py:1-2; DeltaApp/README.md:16-23 | **GPL-3.0**; old stepper firmware header also "FOR NON-COMMERCIAL USE ONLY"; repo is public so GPL applies. This is the skeleton's [9] — needs a source entry |
| ⚑ ArduinoJson **v7.2.1** (vendored `third_party/ArduinoJson`) | DeltaApp/README.md:25-27 | MIT |
| ⚑ `ArduinoCore-renesas` Servo library behaviour (`src/renesas/Servo.cpp`) | DeltaApp/README.md:152-167 | no version recorded |
| ⚑ Arduino UNO R4 Minima; `arduino-cli` (built from source; blocked from the board index) | DeltaApp/README.md:293-303 | — |
| ⚑ Phidget22 Python package, Phidget Control Panel, PhidgetSpatial Precision 3/3/3 1044_0 | requirements.txt:4; HANDOFF.md:22-31; meta.json `sensor` | the skeleton's [14] datasheet is not in sources.md |
| ⚑ pyserial, matplotlib, pandas (requirements.txt:1-3); NumPy (pose_correction.py:35; README.md:51 "only for hybrid"); SciPy `least_squares` (fit_dipole_joint.py:30); tkinter GUI | requirements.txt; code imports | no versions pinned |
| ⚑ pytest, g++ (host tests) | DeltaApp/README.md:49,263-264 | — |
| ⚑ MATLAB (`serialport`, `readtable`, `gradient`); GNU Octave for tests | FieldPlots/*.m; FieldTiltScan/README.md:239-245 | MATLAB version not recorded |
| ⚑ Biot–Savart demo (Helmholtz pair R = 0.3 m, 50 A-turns) | HANDOFF.md:54,66-67 | demo only; centre field 1.4986 G vs formula 1.4985 G |
| ⚑ Other repos used as sources of data: `noahseanui42/engr489-REPORT` (`analysis/refit_v2.py`, `analysis/error_model_coeffs_hybrid.json`, `calibration/2026-10-01_*.md`), `noahseanui42/Matlab` | pose_correction.py:16-19; FieldScan/README.md:83; HANDOFF.md:6 | not reachable from this repo |
| ⚑ Point-dipole field model (µ0/4π …) | fit_dipole_joint.py:20; fit_dipole.m | skeleton wants a dipole-localisation citation `[TODO]` (Report.md:151) — only a pending to-do for S. Wang et al. in sources.md Flags |
| ⚑ Absent from sources.md entirely (0 hits, even as an "Add to Zotero" to-do): `grzesiek2201/Delta-Robot` [9]; Phidget 1044 datasheet / Phidget22 [14]; ArduinoJson / Arduino Servo library; Wilson 2025 ENGR489 report [18] (sources.md mentions "Wilson's cage" in prose only, e.g. lines 106, 122, 344, but has no entry for the report); "Nguyen 2022" (only a Nguyen 2015 candidate, ENGR489_Literature_Notes.md:1894). ISO 230-2 [26] appears once in a note (line 848) with no entry | Report.md:138,147,176-178  | no entry at all |
| ⚑ Only a pending "Add to Zotero" item in sources.md Flags (lines 1856-2152), not in the Index: Renaudin et al. 2010 (line 1988); S. Wang 2019/2018 dipole-localisation papers; GNS Eyrewell (line 2080); IGRF-14 paper (sources.md has `alken2021international` = IGRF-13, expired; and `noaa_magcalc` = a saved form with no result, lines 38-39); Gosselin 1990 for τ = Jᵀf (lines 2102-2104) | Report.md:151,454,456,490  | pending to-do only |

In sources.md but with **no trace in the repo**: all 23. The nearest links are conceptual — Williams (three-sphere FK, E cosθ + F sinθ + G = 0)
for the IK/FK that the upstream GUI implements (deltarobot.py, kinematics.cpp:28-55 use that form); Clavel for the delta
architecture; Tsekos/Farooq for non-magnetic robot design (HANDOFF.md:13-15 states the rule but cites nothing); Futaba datasheet for
the servo (the repo never names the servo model). Williams' sign convention (positive θ moves the arm down, θ = 0 arm horizontal; ENGR489_Literature_Notes.md:498,602) is
the same as the repo's "θ > 0 = bicep DOWN" (config.h:21), with z home −597.2 mm at θ = 0 (test_kinematics.py:37).

## 9. Mapping: skeleton section → evidence in this repo

Strength: **Strong** = repo data/code/docs support it; **Partial** = some; **None** = not in repo.

| Skeleton section | Evidence in repo | Strength | Gaps / notes |
|---|---|---|---|
| I opening, I-A background (CubeSat, ADCS, cage, Wilson) | none | None | all literature/context; repo only says "Helmholtz coil" (README.md:3-5) |
| I-A problem statement (point-by-point 3D map) | FieldScan/README.md:3-10 | Partial | no Wilson numbers (2.7% vs 0.6%) |
| I-B solution + key findings | §4.2–4.6 | Partial | see Appendix A for which key findings reproduce |
| I-B design change gantry→delta | none | None | |
| I-C R1 non-magnetic | HANDOFF.md:13-17 (materials list, R4 Minima) | Partial | rod-end steel, magnet test, parts not in repo |
| I-C R2 scan volume | validity box pose_correction_hybrid.json:13-26; reach DeltaAppCalibrated/README.md:163-176; full-box scan | Strong | 100×300×100 = x ±50, y ±150, z −600…−700 matches |
| I-C R3 automated scanning | field_scan.py; FieldScan/README.md:41-51; CSV columns :146 | Strong | 260-pt scans ran, one restart; USB reconnect handling |
| I-C R4 position accuracy | §4.3, §4.5 | Partial | pen data not in repo; accuracy numbers are summaries |
| I-C R5 repeatable maps | REPEAT_TEST.md | Strong | |
| I-C R6 budget | none | None | no BOM |
| I-D SDGs | none | None | |
| II-A…II-G background/lit | none (see §8) | None | |
| II-H tools | requirements.txt; pytest; Git; Arduino; SolidWorks/DXF not in repo | Partial | no SolidWorks files; "every scan records its firmware version" = a hand-typed string in the JSON (`geometry.firmware`, pose_correction_hybrid.json:52), not read from the board |
| III-A architecture/interfaces | DeltaAppCalibrated/README.md:53-111; protocol DeltaApp/README.md:114-150; field_scan.py | Strong | "mode byte + JSON payload, status every 20 ms" confirmed (README.md:228-262) |
| III-B workspace/geometry | config.h:13-18,42-44; README.md:163-176; numbers recomputed | Partial | MATLAB model, sweep ranges, frame window absent; **1501/1690 is the old geometry** |
| III-C kinematics | kinematics.cpp; pose_correction.py (Newton FK, Jacobian); deltarobot.py; tests | Strong | Eq. numbers are in your skeleton, not repo |
| III-D mechanical | HANDOFF.md:13-15; elbow width 35 mm (robot_config.py:45); platform 150 mm outline | Partial | almost nothing |
| III-E electronics/power | pins D9–D11; DeltaApp/README.md; HANDOFF.md:15-17; 830–2170 µs | Partial | 6 V is an AA pack, not a bench supply; no e-stop mentioned |
| III-F firmware | motion.cpp:128-132,316; config.h:63-84; README.md:293-316 | Strong | 4.5° (not 4.6°) |
| III-G calibration/correction | CALIBRATION_LOG.md; config.h; pose_correction.py; JSON | Strong (method) / Partial (data) | β units resolved (§4.3); post-refit data missing |
| III-H scan software | field_scan.py; FieldScan/README.md:41-51; HANDOFF.md:78-107 | Strong | |
| III-I post-processing | FieldPlots/*.m; tilt_correct.m; fit_dipole_joint.py | Strong | tilt correction uses minimal rotation (Rodrigues not named in repo) |
| III-J sustainability | none (GPL obligations: DeltaApp/README.md:14-23) | Partial | |
| IV-A metrics | REPEAT_TEST.md; DIPOLE_TEST.md | Partial | Table VII rows for protractor/pen/known-shift mostly external |
| IV-B joint cal + hysteresis | CALIBRATION_LOG.md; sweep csv; config.h:73-76 | Partial | no post-refit or down-pass data |
| IV-C kinematic model | host tests; 0.97 ± 0.04 step test not in repo | Partial | |
| IV-D position accuracy/drift | FieldScan/README.md:79-82; pose_correction.py:3-5,20-21 | Partial | summary only |
| IV-E in-situ magnetometer check | 2 Oct off/hybrid data; INDEX.md:34-45 | Partial | data yes, **analysis script no** |
| IV-F dipole test | DIPOLE_TEST.md; fit_dipole_joint.py; dipole_joint_fit.png | Strong | Table VIII matches doc |
| IV-G field map + repeatability | full-box files; REPEAT_TEST.md | Strong | 180 nT / 1.5 mm differ slightly from the doc (§4.6) |
| IV-H measurement chain | meta.json; REPEAT_TEST.md; commit 96988c4 | Strong | background-scan degradation not in skeleton |
| IV-I requirements assessment | — | Partial | no BOM → R6 |
| IV-J critical analysis | — | n/a | interpretive |
| IV-K limitations | DIPOLE_TEST.md:105-111 (still to record); REPEAT_TEST.md | Partial | |
| IV-L sustainability impact | none | None | |
| V conclusion/future | HANDOFF.md:125-137 next steps; DeltaApp/README.md:305-316 out-of-scope list | Partial | |

## 10. Superseded values

| What | Earlier | Later / current | Evidence |
|---|---|---|---|
| Platform SP | 150 mm (plate outline) | 75 mm (ball-joint triangle) | DeltaApp/delta_servo/config.h:14 → DeltaAppCalibrated/delta_servo/config.h:16 |
| Bicep L_UP | 180 mm | 177 mm | DeltaApp config.h:15 → Calibrated config.h:17 |
| Forearm | 600 / 700 mm (planning doc, flagged unresolved) | 625 mm | DeltaApp/README.md:59-61 |
| Servo cal D9 | 1460 µs / 11.8231 µs/° | 1456 / 9.8315 | config.h:29-31,42 |
| Servo cal D10 | 1385 / 10.0481 → 1350 / 9.51 (29 Sep) | 1373 / 9.7664 | CALIBRATION_LOG.md:7-9; config.h:43 |
| Servo cal D11 | 1410 / 10.5544 | 1393 / 9.6658 | config.h:44 |
| Joint limits | single-arm ≈ −16…−25° / 26.5…29.5° (26 Sep) | −20°…70° (full assembly) | DeltaApp/README.md:73-95 |
| Reachable on-axis z | −550 … −793 mm | −540 … −788 mm | DeltaApp/README.md:102 → Calibrated README.md:168 |
| Reachable fraction | 1501/1690 = 89% (old geometry) | 1414/1690 = 83.7% [recomputed, same grid, platform-centre z]. **The Calibrated README keeps the old "1501/1690" text** (line 172) | recomputed |
| Scan-volume target | z ≈ −450…−750 (planning doc) | R2 box z −600…−700, probe coords | Calibrated README.md:166 → pose_correction_hybrid.json:13-26 |
| Z reference | README reach figures are platform-centre z; scan box is probe z (21 mm lower). On-axis reach in probe z is −561…−808 | mixed usage in the docs | robot_config.py:41-42; config.h:81-84 [recomputed] |
| Settle time | 0.5 s (MATLAB `scan_config.m:11`; early 2 Oct runs `…settle0p5s`) | 5 s (Python; FieldTiltScan/scan_config.m) | INDEX.md:3,53-57 |
| Move timeout | fixed 30 s | 30 s + move duration | commit 70c5070 |
| Speed field | JSON float `"v":2.0` (silently = default 2) | int | FieldScan/HANDOFF.md:93-98 |
| Scan control | delta-app data log (`scan_logger.py`, `compile_scan.m`, `make_program.m`) | `field_scan.py` | HANDOFF.md:99-101 |
| MATLAB-only fallback | `run_field_scan.m` (no correction) | Python scans; MATLAB kept as fallback | FieldTiltScan/README.md:223-227 |
| Python scan variant | `field_scan.py` | `field_scan_tilt.py` (imports it) | FieldTiltScan/README.md:3-6 |
| Test count | "All 17 tests pass" (HANDOFF) / 11 motion cases (DeltaApp) | 17 motion cases; 39 pytest items (Calibrated) | HANDOFF.md:98; READMEs; [recomputed] |
| Dipole joint fit | three-run fit: y moves 100.2, 99.5, 199.6 mm | five-run fit: 101.1, 100.3, 201.3 mm | commit d2af0be → DIPOLE_TEST.md:69-71 |
| Magnet label, full-box | `xpos` | `under` | commit 9bac831 |
| Magnet label, dipole x+50 | `x-50` | `x+50` | commit 302648f |
| Dipole magnet depth | planned 150 mm | actual ≈280 mm below bottom layer | DIPOLE_TEST.md:92-93 |
| Repeat-test magnet height | blank | 270 mm (dipole test 260 mm) | commits baf2a6e, 8b06908 |
| Drift attribution | "about 17% from tilt" (same direction implied) | recompute: tilt-predicted drift opposite in sign, ≈ 1/6 size | REPEAT_TEST.md:64-66 vs [recomputed] |
| Tilt filter | `imu` configured and README default | board refused it; `sensor.algorithm = "none"`, pitch/roll NaN | §6 |
| Sensor range | "±8 G quoted from the current 1044_1 spec, unconfirmed" | 5.6 G per axis read from the board | HANDOFF.md:26-28 vs meta.json |
| Active scan area/time | HANDOFF.md says repo `noahseanui42/Matlab`, branch `brave-edison-mui291`, "no PR opened yet" | this repo; PRs #1–#4 merged | HANDOFF.md:6-8 |
| Skeleton "Old 450/18/180/600 values" | — | Only **SP 150, L_UP 180** (and planning-doc L_LO 600/700) are traceable. "450" and "18" are not in any tracked file as a geometry value (the only "18.5 cm" is the ruler radius on arm 2, `servo2_angles.xlsx`) | grep of the repo |

## Appendix A. Skeleton claim audit (key findings and flagged items)

| Skeleton claim | Result against repo |
|---|---|
| Joint calibration 3.4° → 0.51° rms, 98% within ±1° (0.38° dropping first point); per arm D9 4.1/7.2→0.3/0.7, D10 2.8/3.9→0.5/0.9, D11 3.2/4.9→0.6/2.3 | **"Before" reproduces** (3.43° rms, 9% within ±1°; per arm rms 4.13 / 2.81 / 3.20 and max 7.16 / 3.86 / 4.86). **"After" does not**: the only post-fit numbers possible from the repo are in-sample residuals (0.46° rms, 93%; per arm rms 0.48 / 0.58 / 0.25, max 1.04 / 1.25 / 0.50). The "before" is also the assembled sweep with the *old* CAL values, not "each arm measured on its own" as the skeleton words it (CALIBRATION_LOG.md:65-70). A post-refit sweep must exist elsewhere or be redone. |
| Compliance ≈13%, ≈19 mm rms corners | Text only (pose_correction.py:3-5); pen data not in repo. |
| Correction vectors: 0 at centre, ~10 mm at x = ±50, **up to 12.8 mm at corners** (Fig 6) | Centre ✓, x = ±50: 8.3–11.5 mm ✓. **Corners ✗: 17.5–26.6 mm** in the logged `sent_*` columns (xy part 16.9–25.7 mm). 12.8 mm is not found in the repo. |
| β_x = β_y = 5.39e-7, β_mid = 2.68e-7 | ✓ (pose_correction_hybrid.json:9-11). Units: **degrees** (not rad). The "[CHECK: ~0.5° per servo]" doesn't hold: Δθ reaches ≈0.8° at x = ±50 and ≈2.2° at the corners. |
| Relative position error 2.3 mm rms vs 2–2.5 mm repeatability | ✓ as text (pose_correction.py:20; FieldScan/README.md:80-81). Leave-one-run-out numbers (3.15 / 3.76 / 3.35 mm) not in repo. |
| Magnetometer check r = 0.93 | ✓ reproduces (k 1.13, r 0.93, n 225); residual 291 nT (skeleton 280), run scatter 234–243 nT (skeleton 230). Script not in repo. |
| Five repeat maps agree to 180 nT median, ≈1.5 mm | Repo doc: 2.0 mG (200 nT) / 1.9 mG after offset; 2.2 mm / 1.7 mm (REPEAT_TEST.md:37-38,76-78). Recompute (same method as `compare_runs.m`): 202 / 186 nT; 2.15 / 1.72 mm. **Neither 180 nT nor 1.5 mm is what the repo or the recompute gives**; 1.5 mm appears only with a magnet-only gradient and offset removal (1.47 mm). Use 190–200 nT and 1.7–2.2 mm, or say exactly how 180 nT / 1.5 mm were obtained. |
| Dipole fit recovers y shifts within 1.3 mm | ✓ (DIPOLE_TEST.md:76). |
| Absolute offset 33 mm, rotation 4° | ✓ (DIPOLE_TEST.md:81-91). |
| "27 host-side tests" | ✗ not reproducible (39 / 35 / 17 pytest items in the three suites). |
| Workspace "89% (1501 of 1690)" and "z ≈ −540 to −788" | z ✓ (README.md:168; platform-centre z). **89% belongs to the old geometry**; calibrated = 83.7% (1414/1690). |
| Home height −597.2 mm | ✓ (test_kinematics.py:37). |
| 3.1 mm of height per degree near −650 | ✓ workbook assumption (Setup!B40); my Jacobian gives 3.21 mm/° at −650 (3.0–3.2 across the range, workbook). |
| Joint limits −20…70, pulse 830–2170, servo-pin D9–D11, speeds 5–50 mm/s, ω_max 90°/s, 200 ms min | ✓ (config.h). |
| Futaba note (sources.md line 2112): "800–2200 µs travel (working ~830–2170 µs), 1520 µs neutral and ~4° output play are your measurements" | Repo: 830–2170 µs ✓ (config.h:46); 1520 µs appears only as the old `centre_us = 1520 + trim_us` comment (DeltaApp/delta_servo/config.h:32, removed in the calibrated copy) and as a mid-sweep point (servo_sweep.ino:14); **"~4° play" is not in the repo** — the repo's play figures are ≈5 mm / ≈1.5° at arm 2's corner (CALIBRATION_LOG.md:12) and 1.3° / 4.5° up-vs-down landing difference (config.h:73-76). 800–2200 µs travel is not in the repo. |
| Backlash "1.3° per servo, ≈4.5° on D10 [use one number: 4.5 or 4.6]" | Repo says **4.5°** (config.h:75; README.md:297) and ≈1.3°. "4.6" (range 4.2–5.1) is not in the repo. D10 is "servo 2" (CAL[1]). The repo's backlash figures came from the 30 Sep sweeps but only the up pass is committed (CALIBRATION_LOG.md:89). |
| Servo supply "6 V bench supply" | ✗ repo: separate 6 V AA pack / 4×AA (HANDOFF.md:17; README.md:398). |
| Sensor range "[TODO from 14]" | Board reports 5.6 G per axis (meta.json). |
| Background \|B\| 71.2–72.9 µT vs 55.4 µT Earth | ✓ for the 2 Oct scan only; 4 Oct and 6 Oct references read 68.1–70.8 and 68.4–71.2 µT. HANDOFF.md:30-31 expects 0.55–0.6 G. |
| Drift +940/−490/+110 nT in 58 min | ✓ (931/−492/107; REPEAT_TEST.md:56). Run 1 start 18:05 → run 5 start 19:03 = 58 min. |
| Sensor scatter 76 nT median, 430 max | median 72 nT pooled (per-file 64–86), max 426 ✓. REPEAT_TEST.md:39's "≈0.2 mG per axis" is the standard error of a 20-sample mean (≈72/√20 ≈ 16 nT), not the same quantity — the "≈10× sensor noise" claim uses that. |
| Settle: 0.5 s vs 5 s differ by 820 nT median | ✓ (816). |
| Dropped readings 0.8% | ✓ (0.86%). |
| "Two USB dropouts recovered automatically" in the 5-run test | ✓ (REPEAT_TEST.md:26-28). Not mentioned in the skeleton: the 4 Oct background has a long degraded stretch (§6). |
| Probe tilt 1.2° median, 2.7° max; r = 0.96 next day | ✓; "median difference 0.19°" recomputes as 0.11°. |
| ≈1.7% component mixing per degree | sin 1° = 1.75% (geometry); not in repo. |
| Tilt correction changed vectors median 1.6 µT, max 4.2 µT, 3.3% | ✓ (first tilt run, 75 pts). Note that scan's tilt (median 0.87°) is smaller than the full-box scans'. |
| "Tilt prediction opposite sign at ≈1/6" | ✓ by recompute, but contradicts REPEAT_TEST.md:64-66; fix one of them. |
| "Re-placing the magnet changes the map by median 6 µT (> 30× repeatability)" | 6.0 µT ✓; ">30×" only against the 6 Oct 0.19 µT figure (12× against the 2 Oct pair). |
| III-H: timeouts scale with move length → 260-point full-box scans ran unattended; IV-G: unattended apart from one restart at the layer change | The timeout fix (70c5070) predates the full-box scans, yet the 3 Oct *magnet* map was still two runs (layer 1, then layers 2–4) joined afterwards (commits ee59332, 11ad578). The 4 Oct background ran 57 min in one run but with the USB reconnect problem (§6). |
| "MATLAB subtracts a background and draws the maps" | Scripts exist and are tested in Octave on synthetic data; repo text says MATLAB runs of the Python link weren't done (§5 item 6). |
| "Servos S3306MG 2.35 N·m, torque check, rod-end GCR15, PLA +0.2 mm hole correction, acrylic/aluminium plate, BOM" | None in the repo. |

## Appendix B. Regenerating the recomputed numbers

Scripts in `report_extract_checks/` (Python 3; numpy + pandas; `check6` also imports `DeltaAppCalibrated/delta_app/pose_correction.py`).
Run from the repo root; they only read files. See also `report_extract_checks/README.md`.

| Script | Produces |
|---|---|
| `check1_sensor_scatter.py` | per-file and pooled sensor scatter; exact-zero mean components |
| `check2_background_fullbox_tilt.py` | background \|B\| ranges; full-box peaks and durations; tilt vs centre; next-day tilt repeat |
| `check3_repeat_settle_replaced.py` | 5-run spread, drift, σ_pos; settle 0.5 s vs 5 s; magnet re-placement |
| `check4_insitu_correction.py` | in-situ k/r regression (2 Oct off vs hybrid); magnet field at x = ±50 |
| `check5_background_degraded.py` | sample counts in the 4 Oct background; metadata of the joined full-box scan |
| `check6_joint_sweep_and_correction.py` | joint-sweep errors before/after the refit (in-sample); Jacobian sensitivity; correction magnitudes (predicted and logged) |
| `check7_workspace_reach.py` | reachable workspace for the original and calibrated geometry |
| `check8_tilt_drift_and_correction.py` | sign/size of the tilt-predicted drift; first tilt run's correction size |

Method notes. Workspace (`check7`): firmware IK (config.h:13-18, kinematics.cpp:59-93), limits −20°/70°, 25 mm grid of
x, y ∈ [−150, 150], z ∈ {−790, −765, …, −565} treated as platform-centre z (1690 points); with SP = 150, L_UP = 180 it gives
exactly 1501/1690, which is what the README quotes. Dipole fit: `python3 FieldPlots/fit_dipole_joint.py` with the command in
DIPOLE_TEST.md:45-51 (needs scipy). Host tests: `pip install pytest numpy`, then `python3 -m pytest DeltaAppCalibrated/tests`
(39 pass), `DeltaApp/tests` (35 pass); `FieldTiltScan` needs `Phidget22` for 3 of its 17 tests.
