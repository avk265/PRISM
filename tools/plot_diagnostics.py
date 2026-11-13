"""Rebuild two nonredundant vector result figures from bundled, audited data."""
from pathlib import Path
import csv,json,ast,statistics,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parents[1]/'results';A=D/'audit'
(D/'build').mkdir(exist_ok=True)
def read(p):
 with Path(p).open() as f:return list(csv.DictReader(f))
plt.rcParams.update({'font.family':'serif','font.size':8,'axes.labelsize':8,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':6.7,'pdf.fonttype':42,'ps.fonttype':42,'axes.linewidth':.65,'savefig.facecolor':'white','svg.hashsalt':'prism-20261102-r2'})
L={'random_forest':'RF','xgboost':'XGB','lightgbm':'LGBM','ridge':'Ridge','svr':'SVR','mlp':'MLP'}
events=read(A/'stage2_events.csv');metrics=[]
for st in sorted({x['strategy'] for x in events}):
 g=[x for x in events if x['strategy']==st];n=len(g);f=sum(x['stage2_fired']=='True' for x in g);b=sum(x['stage2_applied']=='True' for x in g)
 metrics.append({'strategy':st,'observations':n,'fired_pct':100*f/n,'requested_pct':100*b/n})
with (A/'stage2_plot_values.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=metrics[0]);w.writeheader();w.writerows(metrics)
fig,ax=plt.subplots(figsize=(3.48,2.12));x=np.arange(6);width=.19
for offset,mode,event,color,hatch,label in [(-1.5,'','fired_pct','#a9cee8','//','C: triggered'),(-.5,'','requested_pct','#246a99',None,'C: requested'),(.5,'_lm','fired_pct','#ffd3a4','//','L: triggered'),(1.5,'_lm','requested_pct','#bb5b16',None,'L: requested')]:
 vals=[next(z[event] for z in metrics if z['strategy']==f'prism_{k}{mode}_two_stage') for k in L]
 ax.bar(x+offset*width,vals,width=width,label=label,color=color,edgecolor='black',linewidth=.35,hatch=hatch,zorder=3)
ax.set_xticks(x,list(L.values()));ax.set_ylabel('Timed deliveries (%)');ax.set_ylim(0,139);ax.set_yticks([0,25,50,75,100]);ax.grid(axis='y',alpha=.25,zorder=0);ax.legend(loc='upper right',ncol=2,frameon=True,framealpha=1,edgecolor='.6',columnspacing=.8,handlelength=1.4,borderpad=.4)
ax.spines[['top','right']].set_visible(False);fig.subplots_adjust(left=.15,right=.985,bottom=.15,top=.98)
fig.savefig(D/'figures/stage2_activation.pdf',metadata={'CreationDate':None});fig.savefig(D/'figures/stage2_activation.svg');fig.savefig(D/'build/stage2_activation.png',dpi=220);plt.close(fig)
# Initial sizing overhead is a distinct controller diagnostic: no table contains this outcome.
decisions=read(A/'decision_overhead.csv');points=[]
fig,ax=plt.subplots(figsize=(3.48,2.12))
for mode,color,style,label in [('C','#246a99','-','C: count policies'),('L','#bb5b16','--','L: latency policies')]:
 v=sorted(float(x['decision_overhead_ms']) for x in decisions if ('_lm_' in x['strategy'])==(mode=='L'))
 assert len(v)==132
 y=np.arange(1,len(v)+1)/len(v)
 points.extend({'mode':mode,'overhead_ms':a,'ecdf':b} for a,b in zip(v,y))
 ax.step(v,y,where='post',label=label,color=color,linestyle=style,linewidth=1.35)
ax.set_xscale('log');ax.set_xlim(1,150);ax.set_xticks([1,2,5,10,20,50,100],['1','2','5','10','20','50','100'])
ax.set_xlabel('Initial sizing decision overhead (ms)');ax.set_ylabel('Fraction of logged decisions');ax.set_ylim(0,1.36);ax.set_yticks([0,.25,.5,.75,1]);ax.grid(alpha=.2)
ax.legend(loc='upper right',frameon=True,framealpha=1,edgecolor='.6',ncol=1,borderpad=.4,labelspacing=.35,handlelength=2)
ax.spines[['top','right']].set_visible(False);fig.subplots_adjust(left=.15,right=.985,bottom=.23,top=.98)
fig.savefig(D/'figures/decision_overhead.pdf',metadata={'CreationDate':None});fig.savefig(D/'figures/decision_overhead.svg');fig.savefig(D/'build/decision_overhead.png',dpi=220);plt.close(fig)
with (A/'decision_overhead_plot_values.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=points[0]);w.writeheader();w.writerows(points)
print('Graph data:',len(events),'balanced two-stage observations;',len(decisions),'initial decisions; no tabulated performance outcomes plotted')
