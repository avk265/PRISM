"""Plan or rebuild SF10 using the recorded generator and typed Parquet importer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
REPOSITORY='https://github.com/gregrahn/tpch-kit.git'
COMMIT='852ad0a5ee31ebefeed884cea4188781dd9613a3'

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--raw-dir',type=Path);ap.add_argument('--out',type=Path,default=ROOT/'data/tpch-10gb-parquet');ap.add_argument('--work',type=Path,default=ROOT/'runs/data-rebuild');a=ap.parse_args()
    expected=json.loads((ROOT/'data/tpch_sf10/expected_rows.json').read_text())
    plan=dict(scale_factor=10,generator_repository=REPOSITORY,generator_commit=COMMIT,generator_command=['dbgen','-s','10','-v','-f'],
        provided_raw_directory=str(a.raw_dir) if a.raw_dir else None,output=str(a.out),typed_importer='tools/import_tpch.py',expected_rows=expected,
        distinction='Rebuilt logical dataset; Parquet file names, partitioning and byte hashes may differ from the original. The original manifest is never overwritten.')
    if not a.execute:print(json.dumps(plan,indent=2));return
    if os.name=='nt':raise SystemExit('Use the supplied Docker image or a Linux environment to build the historical dbgen tool.')
    if a.out.exists() and any(a.out.iterdir()):raise SystemExit('Output must be empty; refusing to replace existing dataset files.')
    for program in ['git','make','gcc','java']:
        if not shutil.which(program):raise SystemExit('Missing prerequisite: '+program)
    a.work.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(a.work).free<35*1024**3:raise SystemExit('At least 35 GiB free workspace is required for generation, conversion and shuffle.')
    raw=a.raw_dir.resolve() if a.raw_dir else (a.work/'raw').resolve()
    if a.raw_dir:
        missing=[t for t in expected if not (raw/f'{t}.tbl').is_file()]
        if missing:raise SystemExit('Incomplete supplied flat-file set: '+','.join(missing))
        plan['generator_executed_by_this_command']=False
    else:
        generator=(a.work/'generator').resolve()
        if not generator.exists():subprocess.run(['git','clone','--no-checkout',REPOSITORY,str(generator)],check=True)
        subprocess.run(['git','-C',str(generator),'checkout','--detach',COMMIT],check=True)
        revision=subprocess.check_output(['git','-C',str(generator),'rev-parse','HEAD'],text=True).strip();assert revision==COMMIT
        build=generator/'dbgen';subprocess.run(['make','-C',str(build),'CC=gcc','DATABASE=ORACLE','MACHINE=LINUX','WORKLOAD=TPCH'],check=True)
        raw.mkdir(parents=True,exist_ok=True)
        if any(raw.glob('*.tbl')):raise SystemExit('Raw generation directory is not empty; use a new --work directory.')
        env=dict(os.environ,DSS_CONFIG=str(build),DSS_PATH=str(raw));subprocess.run([str(build/'dbgen'),'-s','10','-v','-f'],cwd=build,env=env,check=True)
        plan['generator_executed_by_this_command']=True
    scratch=(a.work/'scratch').resolve();scratch.mkdir(exist_ok=True)
    env=dict(os.environ,SPARK_LOCAL_IP='127.0.0.1',SPARK_LOCAL_DIRS=str(scratch),PYSPARK_SUBMIT_ARGS='--master local[4] --driver-memory 4g pyspark-shell')
    subprocess.run([sys.executable,str(ROOT/'tools/import_tpch.py'),'--raw-dir',str(raw),'--out',str(a.out.resolve())],env=env,check=True)
    receipt=json.loads((a.out/'TPCH_PARQUET_IMPORT.json').read_text());assert receipt['tables']==expected,('Row-count mismatch',receipt['tables'],expected)
    files=[]
    for p in sorted(a.out.rglob('*.parquet')):
        h=hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda:f.read(1024**2),b''):h.update(block)
        files.append(dict(path=str(p.relative_to(a.out)),bytes=p.stat().st_size,sha256=h.hexdigest()))
    (a.work/'rebuild_receipt.json').write_text(json.dumps(dict(plan=plan,row_counts_verified=True,rebuilt_files=files),indent=2)+'\n')
    print(json.dumps(dict(rebuilt=True,row_counts_verified=True,tables=8,output=str(a.out),receipt=str(a.work/'rebuild_receipt.json'))))

if __name__=='__main__':main()
