"""Run unchanged component analysis without a process pool in restricted environments."""
from pathlib import Path
import concurrent.futures, runpy
class SerialPool:
    def __init__(self, **kwargs): pass
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def map(self, fn, items): return map(fn, items)
concurrent.futures.ProcessPoolExecutor=SerialPool
import numpy as np
scope=runpy.run_path(str(Path(__file__).resolve().parents[1]/'prism/evaluation/full_comparison.py'),run_name='panel_analysis')
def fast_bootstrap(per_q, stat, n=2000, seed=0):
    v=per_q.to_numpy(float)
    draws=np.random.default_rng(seed).integers(0,len(v),size=(n,len(v)))
    return np.percentile(stat(v[draws],axis=1),[2.5,97.5])
scope['main'].__globals__['bootstrap_ci']=fast_bootstrap
scope['main']()
