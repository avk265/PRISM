"""Process-local dispatch extensions. The production harness file is unchanged.

Named profiling policies actually execute probes here; chosen-count lookup
latencies are never used as their delivered-query measurements.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import signal
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
import prism.evaluation.honest_benchmark as hb


class SafeCluster(hb.StandaloneCluster):
    def __enter__(self):
        try:
            return super().__enter__()
        except BaseException:
            self.__exit__(None,None,None)
            raise


class ObservedMonitor(hb.Stage2Monitor):
    """Preserve monitor failures as evidence instead of a silent thread death."""
    def run(self):
        try:
            super().run()
        except Exception as exc:
            self.info['stage2_monitor_error']=str(exc)


def main():
    # Allows the budget owner to unwind the harness/cluster finally blocks.
    def terminate(signum,frame):
        raise KeyboardInterrupt('Owned measurement cancelled at campaign time boundary')
    signal.signal(signal.SIGTERM,terminate)
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--uncalibrated',action='store_true')
    parser.add_argument('--profile-dir',type=Path)
    parser.add_argument('--reference-checksums',type=Path)
    parser.add_argument('--joint-choices',type=Path)
    parser.add_argument('--feature-cache',type=Path)
    parser.add_argument('--base-models-dir',type=Path)
    extension,remaining=parser.parse_known_args()
    hb.StandaloneCluster=SafeCluster
    hb.Stage2Monitor=ObservedMonitor
    context={}
    extract=hb.extract_submission_features
    decide=hb.decide
    def capture(frame,spark,*args,**kwargs):
        context['spark']=spark
        fv=extract(frame,spark,*args,**kwargs)
        if extension.feature_cache:
            from prism.model.train_from_sweep import STAGE1_FEATURES
            extension.feature_cache.mkdir(parents=True,exist_ok=True)
            path=extension.feature_cache/f'{fv.query_id}.json'
            path.write_text(json.dumps({k:float(getattr(fv.plan_features,k)) for k in STAGE1_FEATURES}))
        return fv
    hb.extract_submission_features=capture
    if extension.uncalibrated:
        hb.calibrated_count=lambda e,c,m,pool:(pool.clamp(e),False)
    choices=json.loads(extension.joint_choices.read_text()) if extension.joint_choices else {}
    joint_models={}
    base_bundles=None
    references=json.loads(extension.reference_checksums.read_text()) if extension.reference_checksums else {}
    if extension.profile_dir:
        extension.profile_dir.mkdir(parents=True,exist_ok=True)

    def dispatch(strategy,fv,sql,bundles,dispatcher,pool):
        nonlocal base_bundles
        q=fv.query_id
        if strategy=='prism_pluggable_enhanced' and extension.base_models_dir:
            if base_bundles is None:
                base_bundles=hb.load_bundles(extension.base_models_dir)
            return decide(strategy,fv,sql,base_bundles,dispatcher,pool)
        if strategy.startswith('joint_'):
            import joblib
            from prism.model.train_from_sweep import STAGE1_FEATURES
            _,mode,kind=strategy.split('_',2)
            if kind not in joint_models:
                joint_models[kind]=joblib.load(extension.joint_choices.parent/f'{kind}.joblib')
            model=joint_models[kind]
            allowed=model.shapes if mode=='joint' else [s for s in model.shapes if tuple(s[1:])==(2,1536)]
            vector=np.array([float(getattr(fv.plan_features,k)) for k in STAGE1_FEATURES])
            shape=model.choose(vector,allowed)
            if tuple(shape[1:])!=(pool.executor_cores,pool.executor_memory_mb):
                raise RuntimeError('Scheduled executor shape differs from live frozen-joint prediction; rescheduling required')
            return hb.Decision(int(shape[0])),{'model':strategy,'raw_prediction':'x'.join(map(str,shape)),
                'decision_source':'live frozen joint predictor on current plan; no measured-test latency used',
                'preplanned_prediction':'x'.join(map(str,choices[q][strategy]))}
        if strategy=='lyu_live':
            n=min(4,max(2,math.ceil((fv.plan_features.input_size_bytes+fv.plan_features.estimated_shuffle_bytes)/(256*1024**2))))
        elif strategy=='rios_live':
            n=min(4,max(1,math.ceil(fv.plan_features.input_size_bytes/(200*1024**2))))
        elif strategy in ('ernest_live','cherrypick_live'):
            if extension.profile_dir is None:
                raise RuntimeError('Profiling output directory required')
            spark=context['spark']
            path=extension.profile_dir/f'{q}_{strategy}.json'
            identity=hashlib.sha256(sql.encode()).hexdigest()
            cached=json.loads(path.read_text()) if path.exists() else {'sql_sha256':identity,'query':q,'strategy':strategy,'probes':{},'attempts':[]}
            if cached['sql_sha256']!=identity:
                raise RuntimeError('Profile SQL identity changed')
            observations=cached['probes']
            prelude,query=hb.split_statements(sql)
            def persist():
                tmp=path.with_suffix('.tmp')
                tmp.write_text(json.dumps(cached,indent=2))
                tmp.replace(path)
            def probe(n):
                key=str(n)
                def good(r):
                    try:
                        return r['status']=='SUCCESS' and r['checksum']==references[q] and all(
                            math.isfinite(float(r[k])) and float(r[k])>0 for k in ('latency_s','alloc_core_s','alloc_mem_gb_s'))
                    except (KeyError,TypeError,ValueError):
                        return False
                if key not in observations or not good(observations[key]):
                    hb.set_pool(spark,n)
                    r=hb.run_once(spark,prelude,query,{},1200,pool.executor_memory_mb,f'profile-{q}-{strategy}-{n}')
                    cached['attempts'].append({'executors':n,**r})
                    observations[key]=r
                    persist()
                r=observations[key]
                if not good(r):
                    raise RuntimeError(f'Profiling failed: {q}/{strategy}/{n}: {r.get("error")}')
                return float(r['latency_s'])
            probe(1);probe(4)
            if strategy=='ernest_live':
                from scipy.optimize import nnls
                features=lambda n:[1,1/n,np.log(n),n]
                weights,_=nnls(np.array([features(1),features(4)]),np.array([probe(1),probe(4)]))
                predictions={n:float(weights@features(n)) for n in range(1,5)}
                n=min(n for n,pred in predictions.items() if pred<=1.15*min(predictions.values()))
            else:
                from scipy.stats import norm
                from sklearn.gaussian_process import GaussianProcessRegressor
                from sklearn.gaussian_process.kernels import Matern,WhiteKernel
                sla=1.15*probe(4)
                while len(observations)<4:
                    seen=sorted(int(k) for k in observations)
                    costs=np.array([k*probe(k) if probe(k)<=sla else 40*sla for k in seen])
                    gp=GaussianProcessRegressor(Matern(nu=2.5)+WhiteKernel(1e-3),normalize_y=True,random_state=0).fit(np.array(seen)[:,None],costs)
                    candidates=np.array([k for k in range(1,5) if str(k) not in observations])
                    mean,std=gp.predict(candidates[:,None],return_std=True)
                    best=costs.min();z=(best-mean)/np.maximum(std,1e-9)
                    improvement=(best-mean)*norm.cdf(z)+std*norm.pdf(z)
                    if improvement.max()<0.10*best:
                        break
                    probe(int(candidates[int(np.argmax(improvement))]))
                feasible=[int(k) for k in observations if probe(int(k))<=sla]
                n=min(feasible or list(map(int,observations)),key=lambda k:k*probe(k) if probe(k)<=sla else 40*sla)
            cached['selected_executors']=int(n)
            cached['profiling_core_s']=sum(float(r['alloc_core_s']) for r in observations.values())
            cached['cost_basis']='successful algorithm probes; infrastructure retry attempts preserved separately'
            persist()
        else:
            return decide(strategy,fv,sql,bundles,dispatcher,pool)
        return hb.Decision(int(n)),{'model':strategy,'raw_prediction':f'{n}x2x1536',
                                  'decision_source':'actual dispatcher; profiling stored separately when applicable'}
    hb.decide=dispatch
    try:
        hb.main(remaining)
    finally:
        if '--out-dir' in remaining:
            out=Path(remaining[remaining.index('--out-dir')+1])
            out.mkdir(parents=True,exist_ok=True)
            metadata={'finished':time.strftime('%F %T %Z'),'harness_args':remaining,
                'uncalibrated':extension.uncalibrated,
                'joint_choices':str(extension.joint_choices) if extension.joint_choices else None,
                'profile_directory':str(extension.profile_dir) if extension.profile_dir else None,
                'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'harness_sha256':hashlib.sha256(Path(hb.__file__).read_bytes()).hexdigest(),
                'profiling_cost_basis':'successful algorithm probes; all retry attempts retained separately'}
            with (out/'dispatch_extension_history.jsonl').open('a') as log:
                log.write(json.dumps(metadata)+'\n')


if __name__=='__main__':
    main()
