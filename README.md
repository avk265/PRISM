# PRISM: Two-Stage Predictive Resource Allocation for Spark SQL

Code, trained predictors, SQL workloads and recorded experimental results for *PRISM: Two-Stage Predictive Resource Allocation for Spark SQL under Shared-Cluster Contention*.

| Location | Contents |
|---|---|
| `prism/` | Prediction, calibration, runtime correction, benchmark policies and frozen models |
| `workload/` | 480 training queries, 150 test identities and the eight-query tenant panel |
| `configs/` | Paper settings, query populations and output checksums |
| `results/` | Published summaries, tables, diagnostic figures, component results and one copy of supporting measurements |
| `analysis/` | Component re-analysis entry point |
| `tools/` | Verification, data preparation and experiment launchers |
| `data/tpch_sf10/` | Dataset schema, generator information, row counts and reference hashes |
| `paper/` | Supplied manuscript and its text extraction for numerical verification |

All experimental evidence is organized under **`results/`**. See [its index](results/README.md) for the published scopes and measurement locations.

## Verify recorded results

```bash
python tools/verify_artifact.py
python -m unittest discover -s tests -v
```

These checks use the Python standard library. They verify file hashes, recompute published metrics and SLA decisions, check component trajectories and compare all **499 printed numerical table cells** with the supplied PDF. When installed, `pdftotext` extracts the PDF again; otherwise the bundled text is used.

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
docker build --platform linux/amd64 -t prism-paper .
docker run --rm --platform linux/amd64 prism-paper python tools/verify_artifact.py
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

These commands print plans. Add `--execute` to perform the work. Fresh output goes under ignored `runs/`. See [reproduction instructions](docs/reproduction.md), the [experiment matrix](experiments/experiment_matrix.md) and [baseline descriptions](docs/prior_work_and_baselines.md).

The results include the observed limitations: loaded PRISM query compliance reaches at most 37.5% in the live panel, and no PRISM variant leads the tenant-sharing metrics. Query-mean compliance differs from individual-execution compliance. See [scope and limitations](docs/requirements_audit.md).
