from uuid import uuid4
from fastapi.testclient import TestClient
from backend.app.main import app,Workflow,Contract,execute_graph,merkle,digest,sample
c=TestClient(app)
def account():
 r=c.post('/auth/register',json={'email':f'{uuid4()}@test.local','name':'Test','password':'safe-password'});return r.json(),{'Authorization':'Bearer '+r.json()['token']}
def test_auth_hides_hash_and_rejects_unknown():
 u,h=account();assert 'password_hash' not in u;assert c.post('/auth/login',json={'email':'missing@test.local','password':'safe-password'}).status_code==404
def test_owned_workflow_and_topup():
 u,h=account();w=sample('Evidence Research');saved=c.post('/workflows',json=w,headers=h).json();assert saved['id'];assert c.post('/auth/top-up',json={'amount':50},headers=h).json()['wallet']==150
def test_template_is_valid_for_owner():
 _,h=account();assert c.post('/validate',json=sample(),headers=h).json()['valid']
def test_repair_planner_repairs_low_confidence():
 w=sample();w['nodes'][1]['data']['forceFailure']={'confidence':.1};w['edges'][1]['data']['contract']['min_confidence']=.8
 trace,final,repairs,waiting=execute_graph(Workflow(**w),100);assert waiting;assert repairs[0]['candidate']['id']=='consensus-check';assert final.confidence>=.8
def test_topological_execution_order_is_graph_order():
 w=sample();w['nodes'][0]['position']={'x':999,'y':999};trace,_,_,_=execute_graph(Workflow(**w),100);assert [x['node_id'] for x in trace if x['state']=='completed'][:3]==['n0','n1','n2']
def test_repair_certificate_is_persisted_for_completed_graph():
 u,h=account();w=sample();w['nodes']=w['nodes'][:5];w['edges']=w['edges'][:4];w['nodes'][1]['data']['forceFailure']={'confidence':.1};w['edges'][1]['data']['contract']['min_confidence']=.8
 saved=c.post('/workflows',json=w,headers=h).json();w['id']=saved['id'];run=c.post('/workflows/'+saved['id']+'/run',json=w,headers=h).json();assert run['certificate']['merkle_root'];assert len(c.get('/certificates/'+run['id'],headers=h).json())==1
def test_merkle_root_changes_when_trace_changes():
 assert merkle([digest({'a':1}),digest({'b':2})])!=merkle([digest({'a':2}),digest({'b':2})])
