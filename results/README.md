# Recorded results

This is the single location for the paper's recorded experimental evidence. Supporting measurements are retained once, with portable source paths. Reorganization removes duplicate copies and local-machine metadata; measured timings, statuses, timeouts, allocation values, query identities and published numbers are preserved.

| Evidence | Scope | Location |
|---|---|---|
| Official idle comparison | 22 queries, 18 policies, three timed repetitions: 1,188 observations | `audit/published_official_metrics.csv`, `audit/official_timed_observations.csv` |
| Broader idle sensitivity | 97 common completed query identities; 141 timed observations per policy | `audit/published_matched_metrics.csv`, `audit/broader_idle_timed_observations.csv` |
| Live idle and CPU pressure | Same eight queries, 23 policies, CPU conditions K=0,4,8 | `audit/published_live_metrics.csv`, `audit/published_query_metrics.csv` |
| Tenant sharing | Eight queries per tenant, 23 policies, one/two/three tenants: 69 mixes | `tenant_summary.csv`, `measurements/tenant_sharing/` |
| Component comparison | Full 150-ID inventory, initial and expanded training, actual fixed/growth trajectories | `components/`, `component_summary.csv` |
| Diagnostic figures | 792 checkpoint records and 264 initial decisions | `figures/`, `audit/stage2_events.csv`, `audit/decision_overhead.csv` |
| Weight sensitivity | 189 reweightings of recorded live outcomes | `audit/live_weight_sensitivity.csv` |
| Training records | Initial 360 and additional 120 training queries | `measurements/training/` |

`summary.csv` and `tenant_summary.csv` provide compact entry points. `tables/` contains plain CSV exports of the reported numerical results. `audit/` contains derived records and source references used by the verification scripts. `measurements/` contains supporting executions, decisions and baseline probe records.

The checkpoint directories `prism/model/initial_training/` and `expanded_training/` represent the two training sizes required by the paper's component comparison. They are substantive experimental conditions.

Use `python tools/verify_artifact.py` from the repository root to verify these records. New measurements are written to `runs/` and do not overwrite this evidence.
