"""Check prerequisites without creating Spark applications."""
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
java=str(Path(os.environ['JAVA_HOME'])/'bin/java') if os.environ.get('JAVA_HOME') else shutil.which('java')
versions={name:importlib.metadata.version(name) for name in ['pyspark','numpy','pandas','scikit-learn','scipy','joblib','xgboost','lightgbm']}
runtime=subprocess.run([java,'-version'],capture_output=True,text=True) if java else None
print(json.dumps(dict(python=sys.version,packages=versions,java=runtime.stderr.strip() if runtime else 'MISSING: install Java 17',
    dataset_ready=(root/'data/tpch-10gb-parquet/lineitem').exists(),native_standalone_supported=os.name!='nt',
    windows='Use the Docker recipe to execute the Unix standalone launcher' if os.name=='nt' else None),indent=2))
if not runtime or runtime.returncode or '17.' not in runtime.stderr:sys.exit('Java 17 is required for fresh Spark measurements. Evidence verification does not require Java.')
