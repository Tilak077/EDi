from __future__ import annotations
import hashlib,json,os,sqlite3,time,uuid
from datetime import datetime,timezone
from pathlib import Path
from typing import Any,Literal
import networkx as nx
from fastapi import Depends,FastAPI,Header,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,ConfigDict,Field

ROOT=Path(__file__).parents[2]; DB=ROOT/'mindweave.db'; app=FastAPI(title='MindWeave-R API',version='2.0')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173'],allow_methods=['*'],allow_headers=['*'])
PRIVACY={'public':0,'internal':1,'confidential':2}
NODE={
 'topic':('Topic Input','IN',[],['topic'],0),'researcher':('Researcher','RS',['topic'],['evidence','citations'],3),'curator':('Source Curator','SC',['evidence'],['evidence','citations'],2),'validator':('Evidence Validator','EV',['evidence'],['validated_evidence'],2),'writer':('Draft Writer','DW',['validated_evidence'],['draft'],4),'checker':('Fact Checker','FC',['draft'],['checked_draft'],2),'safety':('Safety Guard','SG',['checked_draft'],['safe_draft'],1),'summarizer':('Summarizer','SM',['draft'],['summary'],1),'translator':('Translator','TR',['draft'],['translated_draft'],2),'compressor':('Context Compressor','CC',['draft','evidence'],['optimized_content'],1),'approval':('Human Approval','HA',['draft'],['approved_draft'],0),'output':('Final Output','OUT',['approved_draft'],['final_output'],0),'module':('Workflow Module','WM',[],[],1)}
TEMPLATES={'Evidence Research':['topic','researcher','curator','validator','writer','approval','output'],'Editorial Review':['topic','researcher','writer','checker','safety','approval','output'],'Policy Brief':['topic','researcher','validator','summarizer','writer','approval','output']}

class Strict(BaseModel): model_config=ConfigDict(extra='forbid')
class Credentials(Strict): email:str; password:str=Field(min_length=8,max_length=128); name:str=''
class TopUp(Strict): amount:float=Field(gt=0,le=10000)
class Contract(Strict): required_fields:list[str]=Field(default_factory=list); min_confidence:float=Field(.7,ge=0,le=1); privacy:Literal['public','internal','confidential']='internal'; freshness_seconds:int=Field(259200,gt=0); max_cost:float=Field(20,ge=0); provenance_required:bool=False; fallback:bool=True
class Workflow(Strict): id:str|None=None; name:str; nodes:list[dict[str,Any]]; edges:list[dict[str,Any]]
class Approval(Strict): approved:bool
class Artifact(Strict): kind:str; payload:dict[str,Any]; provenance:list[str]; confidence:float=Field(ge=0,le=1); privacy:Literal['public','internal','confidential']; created_at:float; cost:float=0; hash:str=''
class Failure(Strict): codes:list[str]; detail:dict[str,Any]
class RepairCandidate(Strict): id:str; cost:float; latency:float; privacy_risk:float; residual_failure_risk:float; fixes:list[str]

def now():return time.time()
def canonical(x:Any):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str)
def digest(x:Any):return hashlib.sha256(canonical(x).encode()).hexdigest()
def merkle(leaves:list[str]):
 if not leaves:return digest('')
 layer=leaves[:]
 while len(layer)>1:
  if len(layer)%2:layer.append(layer[-1])
  layer=[digest(a+b) for a,b in zip(layer[::2],layer[1::2])]
 return layer[0]
def db():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def public(r):return {'id':r['id'],'email':r['email'],'name':r['name'],'wallet':r['wallet']}
def init():
 c=db();c.executescript('''CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE,name TEXT,wallet REAL,password_hash TEXT);
 CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id TEXT,created REAL);
 CREATE TABLE IF NOT EXISTS workflows(id TEXT PRIMARY KEY,user_id TEXT,name TEXT,data TEXT,updated TEXT);
 CREATE TABLE IF NOT EXISTS executions(id TEXT PRIMARY KEY,workflow_id TEXT,user_id TEXT,status TEXT,data TEXT,created TEXT);
 CREATE TABLE IF NOT EXISTS artifacts(hash TEXT PRIMARY KEY,data TEXT);
 CREATE TABLE IF NOT EXISTS certificates(id TEXT PRIMARY KEY,execution_id TEXT,user_id TEXT,root TEXT,data TEXT,created TEXT);''')
 try:c.execute('ALTER TABLE users ADD COLUMN password_hash TEXT')
 except sqlite3.OperationalError:pass
 try:c.execute('ALTER TABLE executions ADD COLUMN user_id TEXT')
 except sqlite3.OperationalError:pass
 c.commit();c.close()
init()
def pwhash(p:str,salt:bytes|None=None):
 salt=salt or os.urandom(16);return salt.hex()+'$'+hashlib.pbkdf2_hmac('sha256',p.encode(),salt,200000).hex()
def verify(p:str,stored:str|None):
 if not stored or '$' not in stored:return False
 salt,h=stored.split('$',1);return hashlib.pbkdf2_hmac('sha256',p.encode(),bytes.fromhex(salt),200000).hex()==h
def session_for(user_id:str):
 token=uuid.uuid4().hex;c=db();c.execute('INSERT INTO sessions VALUES(?,?,?)',(token,user_id,now()));c.commit();c.close();return token
def actor(authorization:str|None=Header(None)):
 token=(authorization or '').removeprefix('Bearer ').strip();c=db();r=c.execute('SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=?',(token,)).fetchone();c.close()
 if not r:raise HTTPException(401,'Sign in is required.')
 return dict(r)
def owned(workflow_id:str,user:dict):
 c=db();r=c.execute('SELECT * FROM workflows WHERE id=? AND user_id=?',(workflow_id,user['id'])).fetchone();c.close()
 if not r:raise HTTPException(404,'Workflow not found.')
 return r

def sample(name:str='Evidence Research'):
 kinds=TEMPLATES[name];ns=[];es=[]
 for i,k in enumerate(kinds):
  label,symbol,ins,outs,cost=NODE[k];ns.append({'id':f'n{i}','type':'agent','position':{'x':80+(i%4)*240,'y':120+(i//4)*180},'data':{'kind':k,'label':label,'symbol':symbol,'privacy':'internal','maxPrivacy':'confidential','status':'idle'}})
 for i in range(len(ns)-1):es.append({'id':f'e{i}','source':ns[i]['id'],'target':ns[i+1]['id'],'data':{'contract':Contract(required_fields=NODE[kinds[i]][3]).model_dump()}})
 return {'id':None,'name':name,'nodes':ns,'edges':es}

@app.post('/auth/register')
def register(x:Credentials):
 c=db();
 if c.execute('SELECT 1 FROM users WHERE email=?',(x.email.lower(),)).fetchone():c.close();raise HTTPException(409,'An account with this email already exists. Please log in.')
 uid=str(uuid.uuid4());c.execute('INSERT INTO users VALUES(?,?,?,?,?)',(uid,x.email.lower(),x.name.strip() or 'MindWeaver',100,pwhash(x.password)));c.commit();u=c.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone();c.close();return {**public(u),'token':session_for(uid)}
@app.post('/auth/login')
def login(x:Credentials):
 c=db();u=c.execute('SELECT * FROM users WHERE email=?',(x.email.lower(),)).fetchone();c.close()
 if not u:raise HTTPException(404,'No account exists for this email. Register first.')
 if not verify(x.password,u['password_hash']):raise HTTPException(401,'Incorrect email or password.')
 return {**public(u),'token':session_for(u['id'])}
@app.get('/auth/me')
def me(user=Depends(actor)):return public(user)
@app.post('/auth/top-up')
def topup(x:TopUp,user=Depends(actor)):
 c=db();c.execute('UPDATE users SET wallet=wallet+? WHERE id=?',(x.amount,user['id']));c.commit();u=c.execute('SELECT * FROM users WHERE id=?',(user['id'],)).fetchone();c.close();return public(u)

@app.get('/workflows/templates')
def templates(user=Depends(actor)):return [{'name':n,'workflow':sample(n)} for n in TEMPLATES]
@app.get('/workflows')
def workflows(user=Depends(actor)):
 c=db();rows=c.execute('SELECT * FROM workflows WHERE user_id=? ORDER BY updated DESC',(user['id'],)).fetchall();c.close();return [{**dict(x),'data':json.loads(x['data'])} for x in rows]
@app.post('/workflows')
def save(w:Workflow,user=Depends(actor)):
 wid=w.id or str(uuid.uuid4());
 if w.id:owned(w.id,user)
 data=w.model_dump();data['id']=wid;c=db();c.execute('INSERT OR REPLACE INTO workflows VALUES(?,?,?,?,?)',(wid,user['id'],w.name,canonical(data),datetime.now(timezone.utc).isoformat()));c.commit();c.close();return data
@app.post('/workflows/{workflow_id}/branch')
def branch(workflow_id:str,user=Depends(actor)):
 w=owned(workflow_id,user);data=json.loads(w['data']);data['id']=None;data['name']=data['name']+' branch';return save(Workflow(**data),user)

def contract_for(edge):return Contract(**edge.get('data',{}).get('contract',{}))
def graph_of(w:Workflow):
 g=nx.DiGraph();g.add_nodes_from(n['id'] for n in w.nodes)
 for e in w.edges:g.add_edge(e['source'],e['target'],edge_id=e['id'],contract=e.get('data',{}).get('contract',{}))
 return g
def static_validate(w:Workflow):
 errors=[];ids={n['id']:n for n in w.nodes};g=graph_of(w)
 if not nx.is_directed_acyclic_graph(g):errors.append({'type':'cycle','message':'Circular dependencies are not allowed.'})
 outputs=[n for n in w.nodes if n['data'].get('kind')=='output'];approvals=[n for n in w.nodes if n['data'].get('kind')=='approval']
 for e in w.edges:
  s,t=ids.get(e['source']),ids.get(e['target'])
  if not s or not t:errors.append({'type':'edge','message':'Connection refers to a missing node.'});continue
  try:co=contract_for(e)
  except Exception:errors.append({'type':'contract','message':'Malformed edge contract.'});continue
  kind=s['data'].get('kind');declared=NODE.get(kind,('', '',[],[],0))[3]
  if any(x not in declared for x in co.required_fields):errors.append({'type':'schema','message':f"{s['data'].get('label')} cannot provide {co.required_fields}."})
  if PRIVACY.get(co.privacy,9)>PRIVACY.get(t['data'].get('maxPrivacy','confidential'),2):errors.append({'type':'privacy','message':'Edge privacy exceeds target guardrail.'})
 for out in outputs:
  if not approvals or not any(nx.has_path(g,a['id'],out['id']) for a in approvals):errors.append({'type':'approval','message':'Final Output must be downstream of Human Approval.'})
 return {'valid':not errors,'errors':errors}
@app.post('/validate')
def validate(w:Workflow,user=Depends(actor)):return static_validate(w)
@app.post('/simulate')
def simulate(w:Workflow,user=Depends(actor)):
 v=static_validate(w);cost=sum(NODE.get(n['data'].get('kind'),('', '',[],[],0))[4] for n in w.nodes);return {**v,'estimated_cost':cost,'estimated_tokens':cost*280,'success_probability':round(max(.3,.96-.15*len(v['errors'])),2),'mode':'dry-run'}

def artifact(kind:str,payload:dict,inputs:list[Artifact],cost:float,privacy='internal',confidence=.89):
 a=Artifact(kind=kind,payload=payload,provenance=sum((x.provenance for x in inputs),[]) or [f'demo:{kind}'],confidence=confidence,privacy=privacy,created_at=now(),cost=cost);return a.model_copy(update={'hash':digest(a.model_dump(exclude={'hash'}))})
def run_node(n:dict,inputs:list[Artifact]):
 kind=n['data']['kind'];label,symbol,needed,outputs,cost=NODE[kind]
 if kind=='module':
  inner=n['data'].get('internalNodes',[]);inner_edges=n['data'].get('internalEdges',[])
  if not inner:return artifact('module',inputs[-1].payload if inputs else {},inputs,cost)
  inner_w=Workflow(name='module',nodes=inner,edges=inner_edges);_,last,_,_=execute_graph(inner_w,0,seed=inputs,allow_approval=False);return artifact('module',last.payload,[last],cost,last.privacy,last.confidence)
 joined={k:v for x in inputs for k,v in x.payload.items()};payload={**joined,**{x:f'{kind}:{x}' for x in outputs}}
 if kind=='topic':payload={'topic':n['data'].get('topic','Evidence-backed city brief')}
 if kind=='researcher':payload.update({'evidence':['Deterministic evidence item'],'citations':['demo://source/1']})
 if kind=='validator':payload={'validated_evidence':joined.get('evidence',[]),'citations':joined.get('citations',[])}
 if kind=='writer':payload={'draft':'A traceable draft derived from validated evidence.'}
 if kind=='approval':payload={'approved_draft':joined.get('draft','Approved draft')}
 if kind=='output':payload={'final_output':joined.get('approved_draft','Final output')}
 force=n['data'].get('forceFailure',{});conf=float(force.get('confidence',.89));privacy=force.get('privacy','internal')
 for f in force.get('dropFields',[]):payload.pop(f,None)
 out=artifact(kind,payload,inputs,cost,privacy,conf)
 if force.get('emptyProvenance'):out=out.model_copy(update={'provenance':[]})
 if force.get('staleSeconds'):out=out.model_copy(update={'created_at':now()-float(force['staleSeconds'])})
 return out.model_copy(update={'hash':digest(out.model_dump(exclude={'hash'}))})
def check_contract(a:Artifact,c:Contract,remaining:float):
 codes=[]
 if any(f not in a.payload for f in c.required_fields):codes.append('schema')
 if c.provenance_required and not a.provenance:codes.append('provenance')
 if a.confidence<c.min_confidence:codes.append('confidence')
 if PRIVACY[a.privacy]>PRIVACY[c.privacy]:codes.append('privacy')
 if now()-a.created_at>c.freshness_seconds:codes.append('freshness')
 if a.cost>c.max_cost or a.cost>remaining:codes.append('budget')
 return Failure(codes=codes,detail={'artifact':a.hash,'confidence':a.confidence,'privacy':a.privacy,'cost':a.cost})
def candidates(f:Failure):
 pool=[]
 def add(i,c,l,p,r,fix):pool.append(RepairCandidate(id=i,cost=c,latency=l,privacy_risk=p,residual_failure_risk=r,fixes=fix))
 if 'confidence' in f.codes:add('consensus-check',2,2,.02,.04,['confidence'])
 if 'schema' in f.codes:add('schema-enricher',1,1,.01,.06,['schema'])
 if 'provenance' in f.codes:add('source-curator',1,2,.02,.05,['provenance'])
 if 'privacy' in f.codes:add('privacy-redactor',1,1,.01,.03,['privacy'])
 if 'freshness' in f.codes:add('freshness-refresh',2,3,.02,.04,['freshness'])
 if 'budget' in f.codes:add('context-compressor',.5,1,.01,.09,['budget'])
 return [x for x in pool if set(f.codes).issubset(set(x.fixes))]
def choose(pool:list[RepairCandidate],remaining:float,weights=(1,.2,4,6)):
 feasible=[x for x in pool if x.cost<=remaining]
 if not feasible:return None
 a,b,c,d=weights;return min(feasible,key=lambda x:a*x.cost+b*x.latency+c*x.privacy_risk+d*x.residual_failure_risk)
def repair(a:Artifact,choice:RepairCandidate,contract:Contract):
 p=dict(a.payload)
 for f in contract.required_fields:p.setdefault(f,f'repaired:{f}')
 if 'confidence' in choice.fixes:a=a.model_copy(update={'confidence':max(a.confidence,contract.min_confidence+.05)})
 if 'privacy' in choice.fixes:a=a.model_copy(update={'privacy':contract.privacy})
 if 'provenance' in choice.fixes:a=a.model_copy(update={'provenance':a.provenance+[f'repair:{choice.id}']})
 if 'budget' in choice.fixes:a=a.model_copy(update={'cost':min(a.cost,contract.max_cost)})
 a=a.model_copy(update={'payload':p,'created_at':now(),'hash':''});return a.model_copy(update={'hash':digest(a.model_dump(exclude={'hash'}))})
def execute_graph(w:Workflow,wallet:float,seed:list[Artifact]|None=None,allow_approval=True):
 v=static_validate(w)
 if not v['valid']:raise HTTPException(422,{'message':'Workflow blocked','errors':v['errors']})
 g=graph_of(w);ids={n['id']:n for n in w.nodes};outs={};trace=[];repairs=[];spent=0.;waiting=False
 for nid in nx.topological_sort(g):
  n=ids[nid];incoming=[outs[x] for x in g.predecessors(nid) if x in outs] or (seed or [])
  if n['data']['kind']=='approval' and allow_approval:trace.append({'node':n['data']['label'],'node_id':nid,'state':'waiting_approval','inputs':[x.hash for x in incoming]});waiting=True;break
  out=run_node(n,incoming);spent+=out.cost;trace.append({'node':n['data']['label'],'node_id':nid,'state':'completed','inputs':[x.hash for x in incoming],'output':out.model_dump()})
  for _,target,e in g.out_edges(nid,data=True):
   contract=Contract(**e.get('contract',{}))
   failure=check_contract(out,contract,wallet-spent)
   if failure.codes:
    pool=candidates(failure);choice=choose(pool,wallet-spent)
    if not contract.fallback or not choice:raise HTTPException(422,{'message':'Contract repair unavailable','failure':failure.model_dump(),'candidates':[x.model_dump() for x in pool]})
    before=out;out=repair(out,choice,contract);spent+=choice.cost;repairs.append({'edge':e.get('edge_id'),'failure':failure.model_dump(),'candidate':choice.model_dump(),'before':before.hash,'after':out.hash});trace.append({'node':choice.id,'node_id':f'repair:{nid}:{target}','state':'repaired','output':out.model_dump()})
  outs[nid]=out
 return trace,(list(outs.values())[-1] if outs else artifact('empty',{},[],0)),repairs,waiting
def certificate(execution_id:str,user_id:str,repairs:list,trace:list,final:Artifact):
 leaves=[digest(x) for x in trace]+[digest(x) for x in repairs]+[final.hash];data={'version':'mw-r/1','repairs':repairs,'trace_hashes':[digest(x) for x in trace],'final_artifact':final.hash,'merkle_root':merkle(leaves)};cid=str(uuid.uuid4());c=db();c.execute('INSERT INTO certificates VALUES(?,?,?,?,?,?)',(cid,execution_id,user_id,data['merkle_root'],canonical(data),datetime.now(timezone.utc).isoformat()));c.commit();c.close();return {'id':cid,**data}
@app.post('/workflows/{workflow_id}/run')
def run(workflow_id:str,w:Workflow,user=Depends(actor)):
 owned(workflow_id,user);nominal=sum(NODE.get(n['data'].get('kind'),('', '',[],[],0))[4] for n in w.nodes)
 if user['wallet']<=0 or user['wallet']<nominal:raise HTTPException(402,'Insufficient compute credits. Top up before execution.')
 trace,final,repairs,waiting=execute_graph(w,user['wallet']);eid=str(uuid.uuid4());charge=min(user['wallet'],sum(x.get('output',{}).get('cost',0) for x in trace if isinstance(x.get('output'),dict)))+sum(r['candidate']['cost'] for r in repairs)
 c=db();c.execute('UPDATE users SET wallet=wallet-? WHERE id=?',(charge,user['id']));data={'trace':trace,'repairs':repairs,'final':final.model_dump(),'charge':charge};c.execute('INSERT INTO executions(id,workflow_id,user_id,status,data,created) VALUES(?,?,?,?,?,?)',(eid,workflow_id,user['id'],'waiting_approval' if waiting else 'completed',canonical(data),datetime.now(timezone.utc).isoformat()));c.commit();c.close();cert=certificate(eid,user['id'],repairs,trace,final) if repairs and not waiting else None
 return {'id':eid,'status':'waiting_approval' if waiting else 'completed','trace':trace,'charge':charge,'certificate':cert}
@app.post('/executions/{execution_id}/approval')
def approve(execution_id:str,x:Approval,user=Depends(actor)):
 c=db();e=c.execute('SELECT * FROM executions WHERE id=? AND user_id=?',(execution_id,user['id'])).fetchone()
 if not e:c.close();raise HTTPException(404,'Execution not found.')
 d=json.loads(e['data']);d['trace'].append({'node':'Human Approval','state':'approved' if x.approved else 'rejected'});status='completed' if x.approved else 'rejected'
 if x.approved:d['trace'].append({'node':'Final Output','state':'completed','output':{'final_output':'Approved evidence-backed result'}})
 c.execute('UPDATE executions SET status=?,data=? WHERE id=?',(status,canonical(d),execution_id));c.commit();c.close();return {'id':execution_id,'status':status,'trace':d['trace']}
@app.get('/executions/{execution_id}')
def execution(execution_id:str,user=Depends(actor)):
 c=db();e=c.execute('SELECT * FROM executions WHERE id=? AND user_id=?',(execution_id,user['id'])).fetchone();c.close()
 if not e:raise HTTPException(404,'Execution not found.')
 return {**dict(e),'data':json.loads(e['data'])}
@app.get('/certificates/{execution_id}')
def certificates(execution_id:str,user=Depends(actor)):
 c=db();rows=c.execute('SELECT * FROM certificates WHERE execution_id=? AND user_id=?',(execution_id,user['id'])).fetchall();c.close();return [{**dict(x),'data':json.loads(x['data'])} for x in rows]
