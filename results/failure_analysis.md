# Boundaries and negative findings in the supplied paper

- The old CPU cap conflates processor competition with executor-slot supply. The CPU burners hold no Spark slots, yet requests are capped near one executor, suppressing useful Stage-2 growth. No PRISM policy exceeds 37.5% SLA on the loaded eight-query panels.
- The three post-hoc full-compliance official predictors are distinct from the training-selected C-MLP, which meets 90.9% of official query-mean targets. Low reserved core-time under load does not establish equivalent SLA performance.
- Under sharing, no PRISM variant leads on all or any of the displayed best makespan, slowdown or reserved-core metrics. Low normalized slowdown can coexist with poor absolute latency.
- Reaching a checkpoint and issuing a growth request do not prove that additional executors registered in time. Registration delay was not directly measured in the paper.
- Identically allocated policies can differ through timing variation. The eight-query live conditions have one delivery per query and do not estimate repeat variability. Full query-mean compliance is not full individual-execution compliance.
- Baseline profiling and its reuse are explicitly recorded. The artifact keeps recorded rows and provenance rather than fabricating unmeasured results.

These findings are preserved in the repository's published summaries. The later controller corrections and ongoing experiments are outside this artifact.
