"""Describe the reference dataset or verify an externally supplied original copy."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024**2),b''):h.update(block)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['describe','verify']);ap.add_argument('--root',type=Path,default=ROOT/'data/tpch-10gb-parquet');a=ap.parse_args()
    manifest=json.loads((ROOT/'data/tpch_sf10/manifest.json').read_text());missing=[]
    if a.action=='describe':
        print(json.dumps({k:v for k,v in manifest.items() if k!='files'},indent=2));return
    for number,entry in enumerate(manifest['files'],1):
        relative=PurePosixPath(entry['path'])
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe manifest path')
        dest=a.root/Path(*relative.parts)
        if dest.exists() and dest.stat().st_size==entry['bytes'] and sha(dest)==entry['sha256']:
            print(f"[{number}/{len(manifest['files'])}] verified {entry['path']}",flush=True);continue
        missing.append(entry['path'])
    if missing:raise SystemExit('Missing or mismatched files: '+', '.join(missing))
    print(json.dumps(dict(verified_files=len(manifest['files']),bytes=manifest['total_bytes'],scale_factor=10,tables=8)))

if __name__=='__main__':main()
