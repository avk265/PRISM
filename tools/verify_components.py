"""Trace full-population component scores to actual fixed/growing executions."""
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def verify():
    checks = 0
    ablation = {row['cohort']: row for row in read(ROOT/'results/component_summary.csv')}
    cohorts = {'official': 22, 'variants': 44, 'variants2': 44, 'newfamilies': 40}
    metadata_keys = ('kind', 'mode', 'cal', 's2', 'safe')
    trajectories = 0
    for cohort, count in cohorts.items():
        folders = ['official_idle'] if cohort == 'official' else [f'fixed_counts/{cohort}', f'fixed_counts/{cohort}_dynamic']
        folders.append(f'growth/{cohort}')
        lookup = {}
        for folder in folders:
            for row in read(ROOT/'results/measurements'/folder/'runs.csv'):
                if row['status'] == 'SUCCESS' and int(row['rep']) > 0:
                    key = (row['query'], row['strategy'], int(row['rep']))
                    assert key not in lookup, ('Ambiguous measured trajectory', cohort, key)
                    lookup[key] = row
        scores = {}
        for training in ('initial_training', 'expanded_training'):
            directory = ROOT/'results/components'/f'{cohort}_{training}'
            executions = read(directory/'executions.csv')
            assert len({row['query'] for row in executions}) == count
            query_groups = defaultdict(list)
            for row in executions:
                query_groups[row['policy'], row['query']].append(float(row['latency_s']))
                strategy = 'spark_dra'
                if row['n']:
                    n = int(float(row['n']))
                    start = int(float(row['n_start'])) if row['n_start'] else n
                    strategy = f'grow_{start}to{n}' if n > start else f'fixed_{n}e'
                original = lookup[row['query'], strategy, int(row['round'])]
                for field, source, divisor in (('latency_s','latency_s',1), ('core_h','alloc_core_s',3600),
                                               ('cpu_h','executor_cpu_s',3600), ('mem_gbh','alloc_mem_gb_s',3600)):
                    assert math.isclose(float(row[field]), float(original[source])/divisor,
                                        rel_tol=1e-8, abs_tol=1e-8), (cohort, training, row['query'], field)
                    checks += 1
                trajectories += 1
            means = {key: statistics.mean(values) for key, values in query_groups.items()}
            values = {}
            for metadata in read(directory/'policy_metrics.csv'):
                if metadata['family'] != 'prism':
                    continue
                queries = {query for policy, query in means if policy == metadata['policy']}
                assert len(queries) == count
                sla = 100 * sum(means[metadata['policy'], query] <= 1.15 * means['fixed_4e', query]
                                for query in queries) / count
                key = tuple(metadata[field] for field in metadata_keys)
                assert key not in values
                values[key] = sla
            scores[training] = values
        expanded = scores['expanded_training']
        for component, field in (('safe','margin'), ('s2','stage2'), ('cal','cap')):
            position = metadata_keys.index(component)
            differences = []
            for key, value in expanded.items():
                if key[position] != 'False':
                    continue
                paired = list(key); paired[position] = 'True'; paired = tuple(paired)
                if paired in expanded:
                    differences.append(expanded[paired] - value)
            assert differences
            assert math.isclose(statistics.mean(differences), float(ablation[cohort][field]), abs_tol=1e-8)
            checks += 1
        initial = scores['initial_training']
        differences = [expanded[key] - value for key, value in initial.items() if key in expanded]
        assert differences
        assert math.isclose(statistics.mean(differences), float(ablation[cohort]['training']), abs_tol=1e-8)
        checks += 1
    return dict(passed=True, checks=checks, query_identities=sum(cohorts.values()),
                component_studies=8, measured_trajectories_checked=trajectories)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
