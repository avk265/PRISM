"""Actual tenant dispatch policies for the common-query concurrency experiments.

The profiled baselines deploy configurations learned by the earlier real idle
profiling campaign. This is an explicitly pre-profiled/steady-state mode, not
profiling the original systems while other tenants interfere.
"""
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import prism.evaluation.honest_benchmark as hb


class TenantPolicies:
    def __init__(self,policy,models_dir,base_models_dir,profiles_dir):
        self.policy=policy
        self.models_dir=Path(models_dir)
        self.base_models_dir=Path(base_models_dir)
        self.profiles_dir=Path(profiles_dir) if profiles_dir else None
        self.bundles=hb.load_bundles(self.models_dir) if policy.startswith('prism') and policy!='prism_base' else {}
        self.base=hb.load_bundles(self.base_models_dir) if policy=='prism_base' else {}
        self.dispatcher=hb.PluggableEnhancedDispatcher() if policy=='prism_base' else None

    def choose(self,q,sql,fv,free_slots):
        p=self.policy
        pool=hb.Pool(4,2,1536,0,'v2')
        config={};stage2=None;profile={}
        if p=='spark_dra':
            return None,config,stage2,profile
        if p.startswith('static_'):
            return int(p.split('_')[1]),config,stage2,profile
        if p=='heuristic':
            n=pool.clamp(fv.plan_features.input_size_bytes/1e9*2.5+1)
        elif p=='lyu_live':
            n=min(4,max(2,math.ceil((fv.plan_features.input_size_bytes+fv.plan_features.estimated_shuffle_bytes)/(256*1024**2))))
        elif p=='rios_live':
            n=min(4,max(1,math.ceil(fv.plan_features.input_size_bytes/(200*1024**2))))
        elif p in ('ernest_profiled','cherrypick_profiled'):
            if self.profiles_dir is None:
                raise RuntimeError('Pre-profiled policy requires its real profiling evidence')
            source=self.profiles_dir/f'{q}_{p.replace("_profiled","_live")}.json'
            profile=json.loads(source.read_text())
            if profile['sql_sha256']!=hashlib.sha256(sql.encode()).hexdigest():
                raise RuntimeError('Profiled SQL differs from concurrent query')
            if not profile['probes'] or not all(r['status']=='SUCCESS' and r.get('checksum')
                and all(math.isfinite(float(r[k])) and float(r[k])>0
                        for k in ('latency_s','alloc_core_s','alloc_mem_gb_s'))
                for r in profile['probes'].values()):
                raise RuntimeError('Incomplete real profiling evidence')
            n=int(profile['selected_executors'])
            if n not in (1,2,3,4):
                raise RuntimeError('Invalid profiled executor count')
            profile={'profile_source':str(source),'preprofiled_core_s':profile['profiling_core_s'],
                     'profile_mode':'dedicated-cluster profiling before mix; no cold-start mix claim'}
        elif p=='prism_base':
            decision,meta=hb.decide('prism_pluggable_enhanced',fv,sql,self.base,self.dispatcher,pool)
            n=decision.num_executors;config=decision.sql_conf
        elif p in ('prism','prism_nocap'):
            n=hb.predict(self.bundles['random_forest_lm']['stage1'],fv)[0]
            if p=='prism':
                n=min(n,free_slots)
        elif p.endswith('_two_stage_cap') or p.endswith('_two_stage_nocap'):
            strategy,cap=p.rsplit('_',1)
            decision,meta=hb.decide(strategy,fv,sql,self.bundles,None,pool)
            n=decision.num_executors;config=decision.sql_conf
            if cap=='cap':
                n=min(n,free_slots)
            bundle=self.bundles[decision.two_stage_model]['stage2']
            if bundle is None:
                raise RuntimeError('Two-stage policy has no trained Stage 2 model')
            stage2={'fv':fv,'bundle':bundle,
                    'pool':hb.Pool(free_slots if cap=='cap' else 4,2,1536,0,'supply')}
        else:
            raise ValueError(f'Unknown live tenant policy: {p}')
        return pool.clamp(n),config,stage2,profile
