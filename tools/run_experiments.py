"""Plan or run Spark SQL experiments using the recorded settings."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
def jobs(config,study,out,data):
    py=sys.executable;hb=str(ROOT/'prism/evaluation/honest_benchmark.py');wrapper=str(ROOT/'scripts/common_campaign/live_extensions.py')
    models=str(ROOT/config['models']);base=str(ROOT/config['base_models'])
    panel=[q for qs in config['panel_by_cohort'].values() for q in qs]
    def measurement(name,folder,queries,policies,reps,load=0,sweep=False):
        args=[py,'-u',wrapper,'--benchmark','tpch','--data-dir',str(data),'--query-dir',str(ROOT/'workload'/folder),
            '--queries',','.join(queries),'--strategies',','.join(policies),'--reps',str(reps),'--timeout','1200',
            '--num-workers','4','--executor-cores','2','--executor-memory-mb','1536','--driver-memory','2g',
            '--contention',str(load),'--calibration','v2','--seed','0','--models-dir',models,'--base-models-dir',base,
            '--profile-dir',str(out/'profiles'/f'k{load}'),'--reference-checksums',str(ROOT/'configs/query_checksums.json'),
            '--out-dir',str(out/name)]
        if sweep:args.append('--sweep')
        if folder!='tpch-queries' or reps==1:args.append('--block-order')
        return name,args
    populations=json.loads((ROOT/'configs/query_populations.json').read_text())
    if study in ('official','all'):
        yield measurement('official','tpch-queries',populations['official'],config['official_policies'],3)
    if study in ('live','all','profiles'):
        loads=[0] if study=='profiles' else config['loads']
        policies=['ernest_live','cherrypick_live'] if study=='profiles' else config['live_policies']
        for load in loads:
            for cohort,queries in config['panel_by_cohort'].items():
                for q in queries:yield measurement(f'live/k{load}/{q}',config['cohorts'][cohort],[q],policies,1,load)
    if study in ('concurrency','all'):
        yield 'concurrency',[py,'-u',str(ROOT/'scripts/common_campaign/concurrent_common.py'),'--data-dir',str(data),
            '--query-dir',str(ROOT/'workload/tenant_panel'),'--queries',','.join(panel),'--streams','1,2,3',
            '--policies',','.join(config['concurrent_policies']),'--reps','1','--grant-wait','15','--driver-memory','1g',
            '--timeout','1200','--models-dir',models,'--base-models-dir',base,'--profiles-dir',str(out/'profiles/k0'),'--out-dir',str(out/'concurrency')]
    if study=='fixed-grid':
        for cohort,folder in config['cohorts'].items():
            yield measurement('fixed-grid/'+cohort,folder,populations[cohort],[f'fixed_{n}e' for n in range(1,5)]+['spark_dra'],3 if cohort=='official' else 1)
    if study=='growth':
        paths=[f'grow_{a}to{b}' for a in range(1,4) for b in range(a+1,5)]
        for cohort,folder in config['cohorts'].items():
            yield measurement('growth/'+cohort,folder,populations[cohort],paths,3 if cohort=='official' else 1)
    if study=='training-sweeps':
        for split,folder in [('train_initial','tpch-generated-queries'),('train_extension','tpch-extension-train')]:
            yield measurement('training-sweeps/'+split,folder,populations[split],[f'fixed_{n}e' for n in range(1,5)],1)
    if study=='train':
        train=[str(ROOT/p) for p in config['training_sweeps']];target=str(out/'trained_models')
        yield 'train-models',[py,'-u',str(ROOT/'prism/model/train_from_sweep.py'),*train,'--test',str(ROOT/'results/measurements/official_idle'),'--out',target]
        yield 'select-primary',[py,'-u',str(ROOT/'prism/model/select_config.py'),'--train',*train,'--models',target,'--folds','5']
    if study=='components':
        tests={'official':['official_idle'],'variants':['fixed_counts/variants','fixed_counts/variants_dynamic'],
            'variants2':['fixed_counts/variants2','fixed_counts/variants2_dynamic'],
            'newfamilies':['fixed_counts/newfamilies','fixed_counts/newfamilies_dynamic']}
        for cohort,test in tests.items():
            for size,label in ((1,'initial_training'),(2,'expanded_training')):
                train=config['training_sweeps'][:size]
                yield f'components/{cohort}_{label}',[py,'-u',str(ROOT/'analysis/serial_comparison.py'),'--train',*[str(ROOT/p) for p in train],
                    '--test',*[str(ROOT/'results/measurements'/p) for p in test],'--models',str(ROOT/'prism/model'/label),
                    '--grow',str(ROOT/f'results/measurements/growth/{cohort}'),'--fb','none','--no-fallback','--seeds','1','--workers','1','--jobs','1','--out',str(out/f'components/{cohort}_{label}')]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--study',required=True,choices=['official','live','profiles','concurrency','fixed-grid','growth','training-sweeps','train','components','all'])
    ap.add_argument('--out',type=Path,default=ROOT/'runs/fresh');ap.add_argument('--data-dir',type=Path,default=ROOT/'data/tpch-10gb-parquet');ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    config=json.loads((ROOT/'configs/experiments.json').read_text());plans=list(jobs(config,a.study,a.out.resolve(),a.data_dir.resolve()))
    if not a.execute:
        print(json.dumps(dict(study=a.study,execute=False,jobs=[dict(name=n,command=c) for n,c in plans]),indent=2));return
    if os.name=='nt':raise SystemExit('Use Docker for the captured Unix standalone worker launcher on Windows.')
    spark_studies=a.study not in ('components','train')
    if spark_studies and not (a.data_dir/'lineitem').is_dir():raise SystemExit('Provide the original formatted data or run python tools/rebuild_data.py --execute first.')
    if a.study=='concurrency' and not all((a.out/'profiles/k0'/f'{q}_{policy}.json').exists() for qs in config['panel_by_cohort'].values() for q in qs for policy in ('ernest_live','cherrypick_live')):
        raise SystemExit('Acquire fresh idle profiles first with --study profiles --execute and the same --out.')
    a.out.mkdir(parents=True,exist_ok=True)
    for name,command in plans:
        if spark_studies and shutil.disk_usage(a.out).free<12*1024**3:raise SystemExit('At least 12 GiB free scratch space required before another batch.')
        local=a.out/'.scratch'/name.replace('/','_');spark=local/'spark';tmp=local/'tmp';spark.mkdir(parents=True,exist_ok=True);tmp.mkdir(exist_ok=True)
        env=dict(os.environ,SPARK_LOCAL_IP='127.0.0.1',SPARK_LOCAL_DIRS=str(spark),TMPDIR=str(tmp))
        env['JAVA_TOOL_OPTIONS']=env.get('JAVA_TOOL_OPTIONS','')+' -Djava.io.tmpdir="'+str(tmp)+'"'
        print(shlex.join(command),flush=True)
        subprocess.run(command,cwd=ROOT,env=env,check=True)
        shutil.rmtree(local)

if __name__=='__main__':main()
