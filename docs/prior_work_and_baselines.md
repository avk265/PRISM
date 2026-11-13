# Baselines represented in the supplied paper

The table below identifies the implementations evaluated in the paper and their limits.

| Method | Artifact implementation | Accounting / limits |
|---|---|---|
| Static 1–4 | Real fixed standalone executor pools | Same 2 cores / 1536 MB executor shape |
| Spark DRA | Actual Spark dynamic allocation with shuffle tracking | Not an emulated executor-count lookup |
| Input-size rule | Count from input bytes, clamped to 1–4 | Local heuristic |
| Lyu-inspired rule | Count from input plus estimated shuffle bytes | Local adaptation; not the full published optimizer |
| RIOS-inspired rule | Input-size count rule | Local adaptation; not a faithful RIOS reproduction |
| Ernest adaptation | Nonnegative fit to full-input probes at counts 1 and 4 | Successful probe resources charged in live cost; tenant profiles acquired before mixes |
| CherryPick adaptation | GP/expected-improvement count search | Trial resources charged; profile reuse explicit for tenant tests |
| Count-only control | No correction/margin, 30 shuffle partitions, three idle executors | Historical dispatcher configuration preserved |
| Oracle | Hindsight choice over measured allocations | Privileged offline bound, not deployable |
| PRISM C/L × six learners | Frozen count/latency bundles with tuned safety margins and Stage 2 | Calibration limitations retained |
| AutoExecutor | Related work only | Not evaluated; no superiority claim |

The implementation files are `prism/evaluation/honest_benchmark.py`, `scripts/common_campaign/live_extensions.py`, `tenant_policies.py`, and `prism/model/train_from_sweep.py`. The experiment launcher selects the conditions reported in the paper.
