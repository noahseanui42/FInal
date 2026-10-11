"""Sample counts in the 4 Oct full-box background (1044 USB drop at point 78) and its metadata."""
import json
import pandas as pd
T = 'FieldTiltScan/data/'
b = pd.read_csv(T + 'full25-4z_corr-hybrid_none_20261004_155505.csv')
print('n_samples value counts:\n', b.n_samples.value_counts().to_string())
print('NaN field rows (idx):', b[b.Bx_G.isna()].idx.tolist(), '; first row with <20 samples:', int(b[b.n_samples < 20].idx.min()))
m = json.load(open(T + 'full25-4z_corr-hybrid_none_20261004_155505.meta.json'))
print('meta: started', m.get('started'), 'finished', m.get('finished'), 'points_done', m.get('points_done'),
      'sensor_reconnected_at_points', m.get('sensor_reconnected_at_points'), 'sensor.algorithm', m['sensor'].get('algorithm'))
mm = json.load(open(T + 'full25-4z_corr-hybrid_under_combined_20261003.meta.json'))
print('combined magnet scan:', {k: mm[k] for k in ('note', 'started', 'finished', 'points_done') if k in mm})
