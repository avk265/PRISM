# Component evidence

The paper's full 150-ID inventory yields query-weighted SLA changes of approximately **+0.7 pp** for training expansion, **+8.7 pp** for safety margins, **−1.8 pp** for runtime correction and **−11.3 pp** for the idle cap.

`results/audit/combined_ablation.json` records unrounded totals; `results/ablation_by_cohort.csv` records cohort values. `configs/analysis/broad_components/` contains matched per-setting scores and execution paths. Fixed and grow-a-to-b trajectories are real measurements; the component scoring reuses them. Feedback and fallback are disabled. The deltas are not additional physical query executions, nor proof of cost improvements.
