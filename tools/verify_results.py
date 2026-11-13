#!/usr/bin/env python3
"""Verify numerical result CSVs and controller diagnostics against recorded measurements.
"""
from pathlib import Path
from collections import defaultdict
import csv,hashlib,json,math,statistics
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'results';A=D/'audit';checks=0

def read(p):
 with Path(p).open(newline='') as f:return list(csv.DictReader(f))
def equal(a,b,context,tol=1e-8):
 global checks
 assert math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=tol),(context,a,b)
 checks+=1
for f,sha in json.loads((A/'raw_source_manifest.json').read_text()).items():
 assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==sha,f
 checks+=1
names={'fixed_1e':'Static-1','fixed_2e':'Static-2','fixed_3e':'Static-3','fixed_4e':'Static-4','spark_dra':'Spark DRA','heuristic':'Input-size rule','lyu_live':'Lyu rule','rios_live':'RIOS rule','ernest_live':'Ernest','cherrypick_live':'CherryPick','prism_pluggable_enhanced':'Count-only control'}
learn={'random_forest':'RF','xgboost':'XGB','lightgbm':'LGBM','ridge':'Ridge','svr':'SVR','mlp':'MLP'}
def name(st):
 if st in names:return names[st]
 k=st.removeprefix('prism_').removesuffix('_two_stage');return 'PRISM-'+('L' if k.endswith('_lm') else 'C')+'-'+learn[k.removesuffix('_lm')]
expected={};raw_cache={}
def raw(r):
 p=r['source_csv']
 if p not in raw_cache:raw_cache[p]=read(ROOT/p)
 return raw_cache[p][int(r['source_row'])-2]
# Complete official benchmark: no per-policy missing cases or unequal repetition counts.
obs=read(A/'official_timed_observations.csv');official=read(A/'published_official_metrics.csv');assert len(obs)==1188 and len(official)==18
qm={}
for x in obs:
 r=raw(x)
 for f in ['query','strategy','rep','checksum','status']:assert x[f]==r[f]
 assert r['status']=='SUCCESS' and int(r['contention_k'])==0
 if r['strategy'].endswith('_two_stage'):assert r['two_stage']=='True',('official stage mismatch',r['strategy'],r['query'])
 for f in ['latency_s','alloc_core_s','executor_cpu_s']:equal(r[f],x[f],('official raw',f))
for row in official:
 st=row['strategy']
 for q in [f'q{i}' for i in range(1,23)]:
  g=[x for x in obs if x['strategy']==st and x['query']==q]
  assert len(g)==3 and {int(x['rep']) for x in g}=={1,2,3}
  qm[st,q]={f:statistics.mean(float(x[f]) for x in g) for f in ['latency_s','alloc_core_s']}
for row in official:
 st=row['strategy'];g=[qm[st,q] for q in [f'q{i}' for i in range(1,23)]];b=[qm['fixed_4e',q] for q in [f'q{i}' for i in range(1,23)]]
 v=[100*sum(x['latency_s']<=1.15*y['latency_s'] for x,y in zip(g,b))/22,statistics.mean(x['latency_s'] for x in g),sum(x['alloc_core_s'] for x in g)/sum(x['alloc_core_s'] for x in b)]
 for key,x in zip(['sla_pct','mean_latency_s','core_rel'],v):equal(row[key],x,('official aggregate',st,key))
 expected['official_idle.csv',name(st)]=v
# Broader workload sensitivity is independent of the repeated official comparison.
hq=read(A/'historical_idle_query_means.csv');pop=set(json.loads((A/'historical_matched_population.json').read_text()));mat=read(A/'published_matched_metrics.csv');assert len(pop)==97
assert set.intersection(*[{x['query'] for x in hq if x['strategy']==r['strategy']} for r in mat])==pop
for r in mat:
 g=[x for x in hq if x['strategy']==r['strategy'] and x['query'] in pop];b={x['query']:x for x in hq if x['strategy']=='fixed_4e' and x['query'] in pop};assert len(g)==97
 v=[100*sum(float(x['latency_s'])<=1.15*float(b[x['query']]['latency_s']) for x in g)/97,statistics.mean(float(x['latency_s']) for x in g),sum(float(x['core_s']) for x in g)/sum(float(x['core_s']) for x in b.values())]
 for key,x in zip(['sla_pct','mean_latency_s','core_rel'],v):equal(r[key],x,('broader sensitivity',key))
# The 23 live policies use the same eight queries at each of three CPU conditions.
pm=read(A/'published_live_metrics.csv');det=read(A/'published_query_metrics.csv');retained=read(ROOT/'results/measurements/live_executions.csv')
ri={(r['study'],r['load'],r['strategy'],r['query']):r for r in retained};base={(r['load'],r['query']):r for r in retained if r['strategy']=='fixed_4e' and r['study'] in ['idle_coverage','load_baselines']}
for d in det:
 x=ri[d['study'],d['load'],d['strategy'],d['query']];b=base[d['load'],d['query']];probes=[]
 if d['profile_source']:probes=list(json.loads((ROOT/d['profile_source']).read_text())['probes'].values())
 if d['strategy'].endswith('_two_stage'):
  src=x['source_csv']
  if src not in raw_cache:raw_cache[src]=read(ROOT/src)
  actual=[y for y in raw_cache[src] if y['query']==x['query'] and y['strategy']==x['strategy'] and y['rep']==x['rep'] and y['status']=='SUCCESS']
  assert len(actual)==1 and actual[0]['two_stage']=='True',('live stage mismatch',x['strategy'],x['query'],x['load'])
  equal(actual[0]['latency_s'],x['latency_s'],'direct live two-stage identity')
 cost=float(x['alloc_core_s'])+sum(float(p['alloc_core_s']) for p in probes)
 waste=max(0,float(x['alloc_core_s'])-float(x['executor_cpu_s']))+max(0,sum(float(p['alloc_core_s'])-float(p['executor_cpu_s']) for p in probes))
 lr=float(x['latency_s'])/float(b['latency_s']);j=lr+cost/float(b['alloc_core_s'])+waste/(float(b['alloc_core_s'])-float(b['executor_cpu_s']))+10*max(0,lr/1.15-1)
 for f,v in [('latency_s',x['latency_s']),('core_s',cost),('J',j)]:equal(d[f],v,('live raw',f))
design=json.loads((A/'balanced_design.json').read_text());catalogue=set(design['tenant_catalogue']);policy_ids={r['strategy'] for r in official}|{'heuristic','lyu_live','rios_live','ernest_live','cherrypick_live'}
for k in ['0','4','8']:
 for st in policy_ids:
  g=[r for r in det if r['load']==k and r['strategy']==st];assert len(g)==8 and {x['query'] for x in g}==catalogue
  assert all(ri[x['study'],x['load'],x['strategy'],x['query']]['rep']=='1' for x in g)
for r in pm:
 g=[x for x in det if all(x[k]==r[k] for k in ['study','load','strategy'])];assert len(g)==8
 v=[100*sum(x['sla']=='True' for x in g)/8,statistics.mean(float(x['latency_s']) for x in g),sum(float(x['core_s']) for x in g)/sum(float(base[x['load'],x['query']]['alloc_core_s']) for x in g),statistics.mean(float(x['J']) for x in g)]
 for key,x in zip(['sla_pct',None,'core_rel','J'],v):
  if key:equal(r[key],x,('live aggregate',key))
 st=r['strategy'];k=int(r['load'])
 if st not in policy_ids:continue
 if k==0:expected['live_idle.csv',name(st)]=v
 else:
  key='cpu_pressure.csv',name(st);expected.setdefault(key,[0.]*6);offset=0 if k==4 else 3;expected[key][offset:offset+3]=v[:3]
o=json.loads((A/'oracle_metrics.json').read_text());oq=read(A/'oracle_by_query.csv');expected['live_idle.csv','Oracle (hindsight)']=[o['sla_pct'],statistics.mean(float(x['latency_s']) for x in oq),o['core_rel'],o['J']]
# The tenant catalogue and every stream are verified, not just mix-level totals.
cm=read(A/'../tenant_summary.csv');mixes=json.loads((A/'concurrent_design_sources.json').read_text());data={};assert len(cm)==len(mixes)==69
for m in mixes:
 g=[r for src in m['sources'] for r in read(ROOT/src)];want={(j,q) for j in range(m['streams']) for q in catalogue}
 assert len(g)==len(want) and {(int(r['stream']),r['query']) for r in g}==want and all(r['status']=='SUCCESS' for r in g)
 data[m['policy'],m['streams']]=g
for r in cm:
 pol=r['policy'];k=int(r['streams']);g=data[pol,k];b={x['query']:float(x['latency_s']) for x in data[pol,1]}
 for x in g:equal(x['response_s'],float(x['wait_s'])+float(x['latency_s']),'response identity')
 v=[statistics.mean(float(x['response_s'])/b[x['query']] for x in g),max(float(x['t_request'])+float(x['response_s']) for x in g)-min(float(x['t_request']) for x in g),sum(float(x['alloc_core_s']) for x in g)/3600]
 # Epoch subtraction is evaluated to microsecond tolerance, below timestamp float precision.
 for key,x in zip(['mean_slowdown','makespan_s','core_h'],v):equal(r[key],x,('tenant aggregate',key),tol=1e-6 if key=='makespan_s' else 1e-8)
 key='tenant_sharing.csv',r['name'].replace(' (Stages 1+2)','').replace(' (profiled)','');expected.setdefault(key,[0.]*9);expected[key][(k-1)*3:k*3]=v
ab=read(A/'../component_summary.csv');assert sum(int(x['N']) for x in ab)==150
for label,f in [('Training expansion','training'),('Safety margin enabled','margin'),('Runtime correction enabled','stage2'),('Idle capacity cap enabled','cap')]:expected['components.csv',label]=[sum(int(x['N'])*float(x[f]) for x in ab)/150]
# Check all reported numeric values without manuscript formatting dependencies.
seen=set();cells=0
for file in ('official_idle.csv','live_idle.csv','cpu_pressure.csv','tenant_sharing.csv','components.csv'):
 for row in read(D/'tables'/file):
  label,*fields=row
  key=file,row[label]
  assert key in expected and key not in seen,key
  seen.add(key)
  assert len(fields)==len(expected[key]),key
  for field,target in zip(fields,expected[key]):
   text=row[field];decimals=len(text.split('.')[1]) if '.' in text else 0
   equal(float(text),target,('reported value',key,field),tol=.50001*10**(-decimals));cells+=1
assert seen==set(expected) and cells==499
# Verify checkpoint activity and initial-decision overhead against raw measurements.
events=read(A/'stage2_events.csv');assert len(events)==792;counts=defaultdict(lambda:[0,0,0])
for r in events:
 x=raw(r);assert (x['strategy'],x['query'],x['rep'])==(r['strategy'],r['query'],r['rep'])
 for f in ['stage2_fired','stage2_applied']:assert x.get(f,'').lower()==r[f].lower()
 counts[r['strategy']][0]+=1;counts[r['strategy']][1]+=r['stage2_fired']=='True';counts[r['strategy']][2]+=r['stage2_applied']=='True'
assert len(counts)==12 and all(v[0]==66 for v in counts.values())
for r in read(A/'stage2_plot_values.csv'):
 n,f,g=counts[r['strategy']]
 for key,v in [('observations',n),('fired_pct',100*f/n),('requested_pct',100*g/n)]:equal(r[key],v,'activation plot')
dec=read(A/'decision_overhead.csv');points=read(A/'decision_overhead_plot_values.csv');assert len(dec)==len(points)==264 and len({(x['strategy'],x['query']) for x in dec})==264
for r in dec:
 x=raw(r);assert x['strategy']==r['strategy'] and x['query']==r['query'];equal(r['decision_overhead_ms'],x['decision_overhead_ms'],'overhead raw')
for mode in ['C','L']:
 vals=sorted(float(x['decision_overhead_ms']) for x in dec if ('_lm_' in x['strategy'])==(mode=='L'));g=[x for x in points if x['mode']==mode];assert len(vals)==len(g)==132
 for i,(v,r) in enumerate(zip(vals,g),1):equal(v,r['overhead_ms'],'overhead plot x');equal(i/132,r['ecdf'],'overhead plot y')
print(json.dumps({'passed':True,'checks':checks,'published_numeric_cells':cells,'official_queries':22,'official_repetitions':3,'official_policies':18,'cross_condition_queries':8,'cross_condition_policies':23,'tenant_mixes':69,'activation_observations':792,'initial_decisions':264},indent=2))
