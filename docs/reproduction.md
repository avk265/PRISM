# Reproduction paths

## 1. Recompute the supplied paper's evidence

`python tools/verify_artifact.py` uses only the standard library. It verifies imported hashes, the frozen C-MLP selection, all experiment scopes, the 499 numeric table cells and the raw source links. It does not need Parquet data, Java or Spark. `pdftotext` allows the supplied PDF to be re-extracted rather than using the bundled extraction.

Reported table values are stored as plain CSVs in `results/tables/`. The verification scripts check these values against the underlying measurements and supplied PDF. The diagnostic SVGs and their numerical inputs remain in `results/`.

## 2. Install the captured runtime

Run `setup.sh` or `setup.ps1` with Python 3.14 and Java 17. Dependencies are pinned in `requirements.lock`; the model files record scikit-learn 1.9.0. Setup creates a local virtual environment and installs libraries without running experiments. Docker provides Python and Java together and is the execution path for the historical Unix Spark launcher on Windows. Docker/native installation on another operating system is a recipe, not a claimed platform-validation result.

Large Parquet inputs are not shipped. `python tools/rebuild_data.py --execute` rebuilds SF10 using the recorded generator and typed importer, validates all eight row counts and records fresh output hashes. It requires Git, make, GCC, Java 17, the installed Python dependencies and 35 GiB free working space. Docker includes those tools. The original input-file hashes remain in `data/tpch_sf10/manifest.json`; `python tools/dataset.py verify --root PATH` can check an exact original-data copy. Rebuilt Parquet bytes may differ. Run `python tools/verify_models.py` to check all frozen bundles' load/inference contracts; this is not a new effectiveness experiment.

## 3. Remeasure the paper's studies

Every launcher defaults to printing commands. Add `--execute` intentionally, on an otherwise dedicated host. New output is confined to `runs/`; published data are not overwritten.

```
python tools/run_experiments.py --study official --execute
python tools/run_experiments.py --study live --execute
python tools/run_experiments.py --study concurrency --execute
python tools/run_experiments.py --study fixed-grid --execute
python tools/run_experiments.py --study growth --execute
```

`official` uses all 22 queries, 18 policies, three repetitions. `live` uses the same eight IDs across all 23 policies and K0/K4/K8, one delivery per condition, and collects real baseline probes separately at each load. `concurrency` uses 23 policies and one/two/three tenants, with actual shared applications and the frozen query catalogue. It requires the fresh idle profiles produced by `live` or `profiles`; it never silently substitutes the archived profiling costs.

The original shared-run command metadata record **1 GB driver memory per tenant**, whereas the paper's general platform paragraph states a 2 GB driver. The settings in `configs/paper.json` preserve 1 GB for that study; single-query execution uses 2 GB. This discrepancy is disclosed rather than silently changing measured settings. Shared allocation wait is 15 seconds. Timing/resource comparisons on a new host remain a separate replication.

Fresh launcher spill and JVM temporary directories are explicitly disk-backed under `runs/`, so multi-query batches do not overflow RAM-backed `/tmp`. The recorded executor and driver settings are retained in the experiment configuration. Allocate enough free disk for transient shuffle data; a fresh measurement command may fail if the host cannot accommodate its workload.

## 4. Training and component analyses

```
python tools/run_experiments.py --study train --execute
python tools/run_experiments.py --study components --execute
```

`train` refits from the bundled 360+120 measured sweeps into `runs/fresh/trained_models/`, then selects a primary configuration on training queries only. It does not overwrite the frozen manuscript checkpoints. The historical auxiliary all-query CV export must not be confused with train-only primary selection. `training-sweeps` prints/runs the real four-count labelling collection if new host-specific training is wanted.

`components` follows the paper's measured-path analysis over all four cohorts and both training sizes, disabling feedback and fallback. It uses actual grow-a-to-b measurements rather than substituting static-b latency. Changing shuffled scoring orders does not create independent physical repetitions. The 189 weight settings in the paper revalue stored live outcomes; they are not 189 remeasurements or 189 newly trained models.

The paper's SLA is `1.15 * same-query, same-load Static-4 mean`. Official compliance averages repetitions within each query; live compliance scores a single delivery. Published total core-hour ratios weight long queries differently from equally weighted mean latency. Probe resources are charged in live allocation/waste but not delivered query latency; tenant profiles are acquired before the mix. Preserve these definitions when analyzing fresh runs. The original calculation and raw provenance are executable in the bundled numeric/SLA verifiers.
