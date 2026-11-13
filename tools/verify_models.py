"""Load each frozen predictor and exercise its actual feature-column contract."""
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
def main():
    train=pd.read_csv(ROOT/'prism/model/expanded_training/training_table.csv');row=train.iloc[0].to_dict();results=[]
    for folder in ('baseline_models','initial_training','expanded_training'):
        for path in sorted((ROOT/'prism/model'/folder).glob('stage*.joblib')):
            bundle=joblib.load(path);cols=bundle['feature_columns']
            x=pd.DataFrame([[float(row.get(c,1.)) if pd.notna(row.get(c,1.)) else 1. for c in cols]],columns=cols)
            try:y=bundle['model'].predict(x)
            except (TypeError,ValueError):y=bundle['model'].predict(x.to_numpy())
            assert np.isfinite(np.asarray(y,dtype=float)).all(),path
            results.append(dict(model=str(path.relative_to(ROOT)),features=len(cols),prediction=np.asarray(y).tolist()))
    print(json.dumps(dict(passed=True,bundles_loaded=len(results),purpose='Serialization/inference contract; no effectiveness or new benchmark claim',models=results),indent=2))

if __name__=='__main__':main()
