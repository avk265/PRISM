# Methodology and limitations

The recorded evaluation uses TPC-H SF10 and fixed executor shapes of two cores and 1536 MB. The configuration and limitations below define how to interpret the results.

| Component or experiment | Status | Evidence / boundary |
|---|---|---|
| Plan-based count prediction, six learners, C/L formulations | Implemented with frozen checkpoints | `prism/model/expanded_training/`, original training/selection code |
| Asymmetric safety margins | Implemented; stored train-only choices | `manifest.json`, `tuning.csv`, `selected_idle.json` |
| Supply calibration | Implemented as tested | Idle permits four; old CPU-pressure cap is preserved, including its observed weakness |
| First-shuffle, grow-only Stage 2 | Implemented and recorded | REST monitor, 792 official delivery records; a request is not proof of timely registration |
| Official idle comparison | Completed, verified | 22 queries, 18 policies, 3 repetitions; query means determine SLA |
| Broader completed idle comparison | Completed, verified | 97 common identities, same repetition pattern for every policy |
| Live idle/load panel | Completed, verified | 8 queries, 23 policies, K0/K4/K8, one delivery per condition |
| Actual tenant sharing | Completed, verified | 69 complete mixes, eight queries per tenant; separate slowdown/makespan/reservation |
| Component ablations | Completed, measured-trajectory scoring | Full 150-ID inventory, fixed and growth runs; feedback/fallback disabled |
| Weight sensitivity | Completed revaluation | 189 reweightings of existing data; not 189 new physical experiments |

The retained code, models, raw rows and supporting evidence are checksum-indexed. `tools/verify_artifact.py` checks reported numerical values, experiment scopes and provenance without running Spark. A fresh re-measurement need not reproduce identical timings or rankings.

The original code groups CV by query ID. It must not be described as family-held-out CV. The test inventory has 150 IDs and includes normalized SQL aliases; artifact documentation distinguishes identities from unique texts. The eight-query panel was selected by a fixed SQL-content hash, not by selecting the fastest successful cases.

The results report post-hoc full-compliance predictors separately from the training-selected C-MLP. Most live conditions have only one timed delivery per query. Query-mean 100% is not per-execution 100%, and neither establishes perfect future reliability. Latency variation between identically allocated methods is a documented limitation. Reserved core-hours are not actual energy or monetary cost.

The measurements come from one shared host and TPC-H SF10. Generalization to multiple hosts, other scales or other workloads requires new experiments.
