# report_extract_checks

Scripts that recompute, from the committed CSV/JSON/code, the numbers flagged **[recomputed]** in `../report_extract.md`.
Run each from the repository root, e.g. `python3 report_extract_checks/check3_repeat_settle_replaced.py`.
Needs numpy and pandas (`check6` also imports `DeltaAppCalibrated/delta_app/pose_correction.py`, which needs numpy).
They only read files; nothing is written.
