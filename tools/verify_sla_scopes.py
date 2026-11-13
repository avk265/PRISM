#!/usr/bin/env python3
"""Audit SLA definitions and stage flags directly from the packaged run files.
No model fitting or experiment execution is performed. Use --write-audit to
save the detailed per-policy report and query-level decisions in audit/.
"""
from pathlib import Path
from collections import defaultdict,Counter
import csv,json,statistics,math,sys,hashlib
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'results';A=D/'audit';cache={};checks=0;query_rows=[];policy_rows=[]
def read(p):
 with Path(p).open(newline='') as f:return list(csv.DictReader(f))
def source(src):
 if src not in cache:cache[src]=read(ROOT/src)
 return cache[src]
def exact(a,b,ctx):
 global checks
 assert math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-8),(ctx,a,b)
 checks+=1
names={'fixed_1e':'Static-1','fixed_2e':'Static-2','fixed_3e':'Static-3','fixed_4e':'Static-4','spark_dra':'Spark DRA','heuristic':'Input-size rule','lyu_live':'Lyu rule','rios_live':'RIOS rule','ernest_live':'Ernest','cherrypick_live':'CherryPick','prism_pluggable_enhanced':'Count-only control'}
learn={'random_forest':'RF','xgboost':'XGB','lightgbm':'LGBM','ridge':'Ridge','svr':'SVR','mlp':'MLP'}
def label(st):
 if st in names:return names[st]
 s=st.removeprefix('prism_').removesuffix('_two_stage');return 'PRISM-'+('L' if s.endswith('_lm') else 'C')+'-'+learn[s.removesuffix('_lm')]
raw_stage_rows=Counter();full={};counts={}
def evaluate(scope,rows,export,load,query_count,expected_reps=None):
 groups=defaultdict(list)
 for r in rows:
  assert r['status']=='SUCCESS' and int(r['contention_k'])==load
  is_final=r['strategy'].endswith('_two_stage')
  assert (r['two_stage']=='True')==is_final,('stage configuration mismatch',scope,r['strategy'],r['query'],r['two_stage'])
  if is_final:raw_stage_rows[scope]+=1
  assert int(r['requested_cores'])==2 and int(r['requested_memory_mb'])==1536
  groups[r['strategy'],r['query']].append(r)
 base={q:statistics.mean(float(x['latency_s']) for x in g) for (st,q),g in groups.items() if st=='fixed_4e'}
 assert len(base)==query_count
 patterns=set();summaries=[]
 for st in sorted({st for st,q in groups}):
  qs={q for s,q in groups if s==st};assert qs==set(base)
  pattern=tuple((q,len(groups[st,q])) for q in sorted(qs));patterns.add(pattern)
  all_rows=[];passed=0;cost=refcost=0
  for q in sorted(qs):
   g=groups[st,q];r0=groups['fixed_4e',q]
   assert len(g)==len(r0) and {int(x['rep']) for x in g}=={int(x['rep']) for x in r0}
   if expected_reps is not None:assert len(g)==expected_reps
   assert len({x['checksum'] for x in g+r0})==1
   latency=statistics.mean(float(x['latency_s']) for x in g);target=1.15*base[q];met=latency<=target;passed+=met;all_rows.extend(g)
   extra=0.0
   if scope.startswith('live_') and st in ['ernest_live','cherrypick_live']:
    detail=next(x for x in read(A/'published_query_metrics.csv') if int(x['load'])==load and x['strategy']==st and x['query']==q)
    probes=json.loads((ROOT/detail['profile_source']).read_text())['probes']
    extra=sum(float(x['alloc_core_s']) for x in probes.values())
   cost+=statistics.mean(float(x['alloc_core_s']) for x in g)+extra;refcost+=statistics.mean(float(x['alloc_core_s']) for x in r0)
   query_rows.append({'scope':scope,'load':load,'strategy':st,'method':label(st),'query':q,'repetitions':len(g),'two_stage_enabled':st.endswith('_two_stage'),'method_query_mean_s':latency,'static4_query_mean_s':base[q],'target_s':target,'query_sla_met':met,'individual_repeats_over_mean_reference_target':sum(float(x['latency_s'])>target for x in g)})
  sla=100*passed/query_count
  old=next(x for x in export if x['strategy']==st);exact(old['sla_pct'],sla,(scope,st,'SLA'))
  exact(old['core_rel'],cost/refcost,(scope,st,'core-hour ratio'))
  summary={'scope':scope,'load':load,'strategy':st,'method':label(st),'queries':query_count,'queries_meeting_target':passed,'sla_pct':sla,'timed_rows':len(all_rows),'two_stage_enabled':st.endswith('_two_stage'),'individual_repeats_over_mean_reference_target':sum(float(x['latency_s'])>1.15*base[x['query']] for x in all_rows),'requested_executor_counts':dict(sorted(Counter(int(x['requested_executors']) for x in all_rows).items())),'checkpoint_evaluations':sum(x.get('stage2_fired')=='True' for x in all_rows),'growth_requests':sum(x.get('stage2_applied')=='True' for x in all_rows)}
  if summary['two_stage_enabled']:assert summary['checkpoint_evaluations']>0,('no observed Stage-2 checkpoint',scope,st)
  summaries.append(summary);policy_rows.append(summary)
 assert len(patterns)==1
 full[scope]=[x['method'] for x in summaries if x['two_stage_enabled'] and x['queries_meeting_target']==query_count]
 counts[scope]={'queries':query_count,'policies':len(summaries),'runs_per_policy':summaries[0]['timed_rows'],'sla_metric':'within-query mean latency' if expected_reps!=1 else 'single delivered query latency','prism_100_percent':full[scope]}
 return summaries
for scope,index,metrics,n,reps in [('official_idle','official_timed_observations.csv','published_official_metrics.csv',22,3),('broader_idle','broader_idle_timed_observations.csv','published_matched_metrics.csv',97,None)]:
 rows=[]
 for r in read(A/index):
  x=source(r['source_csv'])[int(r['source_row'])-2]
  for f in ['query','strategy','rep']:assert x[f]==r[f]
  rows.append(x)
 evaluate(scope,rows,read(A/metrics),0,n,reps)
retained=read(ROOT/'results/measurements/live_executions.csv');metrics=read(A/'published_live_metrics.csv')
for k in [0,4,8]:
 target=[x for x in metrics if int(x['load'])==k];keys={(x['study'],x['strategy']) for x in target};rows=[]
 for r in retained:
  if int(r['load'])!=k or (r['study'],r['strategy']) not in keys:continue
  g=[x for x in source(r['source_csv']) if x['query']==r['query'] and x['strategy']==r['strategy'] and x['rep']==r['rep'] and x['status']=='SUCCESS']
  assert len(g)==1,('ambiguous live source',r['source_csv'],r['strategy'],r['query'])
  exact(g[0]['latency_s'],r['latency_s'],'direct live observation');rows.append(g[0])
 evaluate('live_idle' if k==0 else f'live_cpu_k{k}',rows,target,k,8,1)
assert set(full['official_idle'])=={'PRISM-L-RF','PRISM-L-LGBM','PRISM-L-Ridge'}
assert set(full['live_idle'])=={'PRISM-C-RF','PRISM-L-Ridge'}
assert full['broader_idle']==full['live_cpu_k4']==full['live_cpu_k8']==[]
for st,want in [('prism_random_forest_lm_two_stage',2),('prism_lightgbm_lm_two_stage',0),('prism_ridge_lm_two_stage',1)]:
 r=next(x for x in policy_rows if x['scope']=='official_idle' and x['strategy']==st);assert r['individual_repeats_over_mean_reference_target']==want
for scope in ['official_idle','live_idle']:
 r=next(x for x in policy_rows if x['scope']==scope and x['strategy']=='prism_ridge_lm_two_stage');assert set(r['requested_executor_counts'])=={4} and r['growth_requests']==0
assert 'sla' not in read(A/'../tenant_summary.csv')[0]
# Two-stage status is checked in the physical run record, not inferred only from a label.
for f,sha in json.loads((A/'raw_source_manifest.json').read_text()).items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==sha
report={'passed':True,'checks':checks,'scopes':counts,'two_stage_raw_rows_checked_by_scope':dict(raw_stage_rows),'source_files_read':len(cache),'tenant_sla_reported':False,'stage2_applied_definition':'growth request issued; does not establish executor registration','official_100_percent_definition':'all 22 per-query three-run means satisfy their same-query Static-4 mean reference targets; not every individual execution must pass','individual_repeat_reference':'the same query-mean Static-4 target, not a separately paired repetition','policy_details':policy_rows}
if '--write-audit' in sys.argv:
 (A/'sla_scope_verification.json').write_text(json.dumps(report,indent=2)+'\n')
 with (A/'sla_query_checks.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(query_rows[0]));w.writeheader();w.writerows(query_rows)
print(json.dumps({k:v for k,v in report.items() if k!='policy_details'},indent=2))
