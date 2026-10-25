"""Run: python backend/benchmark_repair.py. Produces deterministic 50-run repair data."""
import csv
from pathlib import Path
from app.main import Workflow,execute_graph,sample
OUT=Path(__file__).with_name('repair_benchmark.csv')
with OUT.open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['run','failure','repaired','repair','trace_steps']);w.writeheader()
 for i in range(50):
  data=sample();failure=['confidence','schema','provenance','privacy','freshness','budget'][i%6];edge=data['edges'][1]['data']['contract'];force={}
  if failure=='confidence':force={'confidence':.1};edge['min_confidence']=.8
  if failure=='schema':force={'dropFields':['evidence']};edge['required_fields']=['evidence','citations']
  if failure=='provenance':force={'emptyProvenance':True};edge['provenance_required']=True
  if failure=='privacy':force={'privacy':'confidential'};edge['privacy']='public'
  if failure=='freshness':force={'staleSeconds':10};edge['freshness_seconds']=1
  if failure=='budget':edge['max_cost']=.5
  data['nodes'][1]['data']['forceFailure']=force
  try:trace,_,repairs,_=execute_graph(Workflow(**data),100);w.writerow({'run':i+1,'failure':failure,'repaired':bool(repairs),'repair':repairs[0]['candidate']['id'] if repairs else 'none','trace_steps':len(trace)})
  except Exception as e:w.writerow({'run':i+1,'failure':failure,'repaired':False,'repair':type(e).__name__,'trace_steps':0})
print(OUT)
