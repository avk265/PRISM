# PRISM: Two-Stage Predictive Resource Allocation for Spark SQL

PRISM predicts executor counts for Spark SQL from query-plan features, then applies a grow-only correction at the first completed shuffle checkpoint. This repository contains the implementation, trained models, SQL workloads, experiment settings and recorded results.

| Location | Contents |
|---|---|
| `prism/` | Prediction, calibration, runtime correction, benchmark policies and frozen models |
| `workload/` | 480 training queries, 150 test identities and the eight-query tenant panel |
| `configs/` | Experiment settings, query populations and output checksums |
| `results/` | Numerical summaries, component results, controller diagnostics and supporting measurements |
| `analysis/` | Component re-analysis entry point |
| `tools/` | Verification, data preparation and experiment launchers |
| `data/tpch_sf10/` | Dataset schema, generator information, row counts and reference hashes |

All experimental evidence is organized under **`results/`**. See [its index](results/README.md) for the published scopes and measurement locations.

## Verify recorded results

```bash
python tools/verify_artifact.py
python -m unittest discover -s tests -v
```

These checks use the Python standard library. They verify file hashes, recompute metrics and SLA decisions, trace component scores to measured executions, and check all **499 reported numerical values** in the CSV result tables against their supporting data.

## Install

The captured runtime uses Python 3.14, Java 17 and the versions pinned in `requirements.lock`.

Linux/macOS:

```bash
bash setup.sh
.venv/bin/python tools/verify_models.py
```

Windows PowerShell:

```powershell
.\setup.ps1
.\.venv\Scripts\python.exe tools\verify_models.py
```

The standalone Spark launcher uses Unix scripts. Docker provides a common execution environment on Windows and macOS:

```bash
docker build --platform linux/amd64 -t prism-spark .
docker run --rm --platform linux/amd64 prism-spark python tools/verify_artifact.py
```

The Docker recipe is provided; cross-platform performance equivalence has not been tested.

## Rebuild data and run experiments

Large datasets are excluded. The [data instructions](docs/data.md) explain how to generate TPC-H SF10 with the pinned generator and original typed importer, or verify an existing original-data copy. Generation requires the installed dependencies, Java 17, Git, make, GCC and at least 35 GiB free space.

```bash
python tools/rebuild_data.py
python tools/run_experiments.py --study official
python tools/run_experiments.py --study live
python tools/run_experiments.py --study concurrency
```

These commands print plans. Add `--execute` to perform the work. Fresh output goes under ignored `runs/`. See [reproduction instructions](docs/reproduction.md), the [experiment matrix](docs/experiments.md) and [baseline descriptions](docs/baselines.md).

The results include the observed limitations: loaded PRISM query compliance reaches at most 37.5% in the live panel, and no PRISM variant leads the tenant-sharing metrics. Query-mean compliance differs from individual-execution compliance. See [scope and limitations](docs/methodology.md).
