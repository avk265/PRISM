# Paper experiment matrix

| ID | Data / queries | Methods | Timed repetitions | Evidence status |
|---|---|---:|---:|---|
| Training | TPC-H SF10; 360 + 120 training instances | Fixed-count labels; six C/L learners | Recorded training sweeps | Frozen CSVs and 24 main bundles |
| RQ1 official | 22 official queries, idle | 18 | 3 per query/method | Complete; 1,188 delivery rows |
| RQ1 broader | 97 common completed IDs, idle | 18 | Same per-ID pattern across all methods; 141 rows/method | Complete; separate from live panel |
| RQ2 live | Fixed eight-query catalogue, idle | 23 | 1 | Complete |
| RQ3 CPU load | Same eight-query catalogue, K4 and K8 | 23 | 1 per condition | Complete |
| RQ4 tenants | Same eight queries per tenant; 1,2,3 tenants | 23 | One measured mix per method/tenant count | Complete; 69 mixes |
| RQ5 components | Full 150-ID test inventory | Matched component settings, two training sizes | Existing fixed/growth trajectories | Complete scoring; not new live deliveries |
| RQ5 plots | Official two-stage execution and decision logs | 12 PRISM methods | 792 deliveries / 264 decisions | Complete |
| RQ5 weights | Existing live idle observations | Frozen C-MLP vs Static-4 | 189 weight vectors | Revaluation, not re-execution |

All rows describe recorded paper evidence. Fresh commands print plans until `--execute` is supplied and write to `runs/`. They never overwrite these archived results. Timing differences on another device are expected and must be reported as a new replication.
