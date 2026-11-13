"""Verify recorded results without Spark, fitting models or downloading data."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    verified = 0
    for line in (ROOT / 'checksums.sha256').read_text().splitlines():
        expected, name = line.split('  ', 1)
        path = ROOT / name
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
        verified += 1
    populations = json.loads((ROOT / 'configs/query_populations.json').read_text())
    assert {key: len(value) for key, value in populations.items()} == dict(
        train_initial=360, train_extension=120, official=22,
        variants=44, variants2=44, newfamilies=40)
    data = json.loads((ROOT / 'data/tpch_sf10/manifest.json').read_text())
    assert len(data['files']) == 91 and data['tables'] == 8
    assert sum(entry['bytes'] for entry in data['files']) == data['total_bytes'] == 3447837229
    models = ROOT / 'prism/model/expanded_training'
    assert len(list(models.glob('stage*.joblib'))) == 24
    selection = json.loads((models / 'selected_idle.json').read_text())
    assert selection['n_train_queries'] == 480
    assert selection['selected'] == dict(kind='mlp', mode='label', margin=.5)
    for path in ROOT.rglob('*.py'):
        if not any(part in path.parts for part in ('.git', '.venv', 'runs', '__pycache__')):
            ast.parse(path.read_text())
    reports = {}
    for script in ('verify_results.py', 'verify_sla_scopes.py', 'verify_components.py'):
        result = subprocess.run([sys.executable, str(ROOT / 'tools' / script)],
                                capture_output=True, text=True, check=True)
        reports[script] = json.loads(result.stdout)
    print(json.dumps(dict(passed=True, files_verified=verified,
                         main_model_bundles=24, reports=reports), indent=2))


if __name__ == '__main__':
    main()
