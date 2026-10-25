from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable

NAVY=colors.HexColor('#12355B');BLUE=colors.HexColor('#2E75B6');TEAL=colors.HexColor('#118C8B');PALE=colors.HexColor('#EEF4F8');LINE=colors.HexColor('#9DB3C7');INK=colors.HexColor('#182534')
class ArchitectureFigure(Flowable):
 def __init__(self):super().__init__();self.width=166*mm;self.height=100*mm
 def draw(self):
  c=self.canv
  def box(x,y,t,d,fill):
   c.setFillColor(fill);c.setStrokeColor(NAVY);c.roundRect(x*mm,y*mm,45*mm,18*mm,3,fill=1,stroke=1);c.setFillColor(NAVY);c.setFont('Helvetica-Bold',8);c.drawCentredString((x+22.5)*mm,(y+11)*mm,t);c.setFillColor(INK);c.setFont('Helvetica',6.5);c.drawCentredString((x+22.5)*mm,(y+5)*mm,d)
  def arr(x1,y1,x2,y2):
   c.setStrokeColor(BLUE);c.setLineWidth(1.2);c.line(x1*mm,y1*mm,x2*mm,y2*mm);c.setFillColor(BLUE);c.circle(x2*mm,y2*mm,1.8,fill=1,stroke=0)
  box(2,68,'1  WORKFLOW DAG','nodes + edge contracts',PALE);box(61,68,'2  CONTRACT CHECK','schema | confidence',colors.HexColor('#E9F6F4'));box(120,68,'3  FAILURE REPORT','violation evidence',colors.HexColor('#FFF5E0'));box(32,25,'4  REPAIR PLANNER','filter + score candidates',colors.HexColor('#EEF3FA'));box(91,25,'5  REPAIR + RECHECK','splice + revalidate',colors.HexColor('#EDF7EF'));box(120,5,'6  CERTIFICATE','hashes + Merkle root',colors.HexColor('#F2EFF8'))
  arr(47,77,61,77);arr(106,77,120,77);arr(142,68,113,43);arr(77,34,91,34);arr(113,25,142,23)
  c.setFillColor(colors.HexColor('#65788A'));c.setFont('Helvetica',7);c.drawString(2*mm,1*mm,'FIGURE 1  Runtime repair architecture - artifact and decision paths are recorded for audit.')
class DecisionFigure(Flowable):
 def __init__(self):super().__init__();self.width=166*mm;self.height=105*mm
 def draw(self):
  c=self.canv
  def b(y,text,fill):
   c.setFillColor(fill);c.setStrokeColor(NAVY);c.roundRect(62*mm,y*mm,43*mm,12*mm,3,fill=1,stroke=1);c.setFillColor(NAVY);c.setFont('Helvetica-Bold',7.5);c.drawCentredString(83.5*mm,(y+4.8)*mm,text)
  for y,t,f in [(82,'FAILED CONTRACT',colors.HexColor('#FFF5E0')),(65,'GENERATE CANDIDATES',PALE),(48,'HARD-CONSTRAINT FILTER',colors.HexColor('#E9F6F4')),(31,'WEIGHTED RANKING',colors.HexColor('#EEF3FA')),(14,'SPLICE + REVALIDATE',colors.HexColor('#EDF7EF'))]:b(y,t,f)
  c.setStrokeColor(BLUE);c.setLineWidth(1.2)
  for y in [82,65,48,31]:c.line(83.5*mm,y*mm,83.5*mm,(y-5)*mm);c.setFillColor(BLUE);c.circle(83.5*mm,(y-5)*mm,1.8,fill=1,stroke=0)
  c.setFillColor(colors.HexColor('#FFF1F0'));c.setStrokeColor(NAVY);c.roundRect(5*mm,47*mm,42*mm,20*mm,3,fill=1,stroke=1);c.setFillColor(NAVY);c.setFont('Helvetica-Bold',7);c.drawString(8*mm,61*mm,'REJECT IF:');c.setFont('Helvetica',6.5)
  for i,x in enumerate(['budget exceeded','privacy conflict','cycle introduced','missing interface']):c.drawString(8*mm,(56-i*3.4)*mm,x)
  c.setFillColor(NAVY);c.setFont('Helvetica-Bold',7);c.drawString(4*mm,4*mm,'J(r) = alpha*C(r) + beta*L(r) + gamma*P(r) + delta*R(r)')
  c.setFillColor(colors.HexColor('#65788A'));c.setFont('Helvetica',6.5);c.drawString(4*mm,1*mm,'C cost   L latency   P privacy risk   R residual failure risk')
class CertificateFigure(Flowable):
 def __init__(self):super().__init__();self.width=166*mm;self.height=82*mm
 def draw(self):
  c=self.canv
  labs=['Artifact','Contract + failure','Candidate set','Repair output','Trace events'];xs=[1,35,69,103,137]
  for x,l in zip(xs,labs):
   c.setFillColor(PALE);c.setStrokeColor(NAVY);c.roundRect(x*mm,51*mm,28*mm,11*mm,3,fill=1,stroke=1);c.setFillColor(NAVY);c.setFont('Helvetica-Bold',7);c.drawCentredString((x+14)*mm,55.5*mm,l);c.setStrokeColor(BLUE);c.line((x+14)*mm,51*mm,83*mm,31*mm)
  c.setFillColor(colors.HexColor('#E9F1F8'));c.setStrokeColor(NAVY);c.roundRect(55*mm,23*mm,56*mm,11*mm,3,fill=1,stroke=1);c.setFillColor(NAVY);c.setFont('Helvetica-Bold',8);c.drawCentredString(83*mm,27.5*mm,'MERKLE ROOT / CERTIFICATE');c.setStrokeColor(BLUE);c.line(83*mm,23*mm,83*mm,14*mm)
  c.setFillColor(colors.HexColor('#EDF7EF'));c.roundRect(52*mm,4*mm,62*mm,10*mm,3,fill=1,stroke=1);c.setFillColor(NAVY);c.setFont('Helvetica-Bold',7);c.drawCentredString(83*mm,8*mm,'PERSISTED EXECUTION RECORD');c.setFillColor(colors.HexColor('#65788A'));c.setFont('Helvetica',7);c.drawString(2*mm,1*mm,'FIGURE 3  Canonical evidence hashes support integrity checks of the recorded repair trace.')

out='MindWeave-R_Patent_Disclosure_Draft.pdf'
doc=SimpleDocTemplate(out,pagesize=A4,leftMargin=20*mm,rightMargin=20*mm,topMargin=18*mm,bottomMargin=18*mm,title='MindWeave-R Patent Disclosure Draft')
st=getSampleStyleSheet()
st.add(ParagraphStyle(name='T',parent=st['Title'],fontName='Helvetica-Bold',fontSize=20,leading=25,textColor=NAVY,alignment=TA_CENTER,spaceAfter=5*mm))
st.add(ParagraphStyle(name='H',parent=st['Heading2'],fontName='Helvetica-Bold',fontSize=14,leading=17,textColor=NAVY,spaceBefore=7*mm,spaceAfter=3*mm,keepWithNext=True))
st.add(ParagraphStyle(name='B',parent=st['BodyText'],fontSize=10.2,leading=14.5,spaceAfter=3*mm,alignment=4,textColor=INK))
st.add(ParagraphStyle(name='S',parent=st['BodyText'],fontSize=8.8,leading=11.5,textColor=colors.HexColor('#555555')))
st.add(ParagraphStyle(name='TH',parent=st['BodyText'],fontSize=7.2,leading=9,textColor=colors.white,fontName='Helvetica-Bold'))
story=[]
def p(x,style='B'): story.append(Paragraph(x,st[style]))
def h(n,x): p(f'{n}. {x}','H')
def items(xs):
 for x in xs:p('• '+x)
def footer(c,d):
 c.saveState();c.setStrokeColor(LINE);c.line(20*mm,14*mm,A4[0]-20*mm,14*mm);c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#6B7C8D'));c.drawString(20*mm,9*mm,'MINDWEAVE-R | INVENTION DISCLOSURE DRAFT');c.drawRightString(A4[0]-20*mm,9*mm,'Page '+str(d.page));c.restoreState()

p('PATENT APPLICATION DISCLOSURE DRAFT','T')
p('Budgeted Contract Repair for Agent Workflows','T')
p('<b>Working draft for review only.</b> This is not legal advice or a filing-ready specification and makes no assertion of novelty or patentability. Personal, applicant, and filing details not supplied are left blank. Confirm all technical statements against the implementation before filing.','S')
story.append(Spacer(1,8*mm))
h(1,'Full name, nationality and address of applicant(s)')
p('Full Name: ______________________________________________')
p('Nationality: _____________________________________________')
p('Address: ______________________________________________________________')
p('_______________________________________________________________________')
h(2,'Full name, nationality, address, email and phone number of inventor(s)')
t=Table([[Paragraph('Full name<br/>(including middle name)',st['TH']),Paragraph('Nationality',st['TH']),Paragraph('Address /<br/>institution',st['TH']),Paragraph('Email',st['TH']),Paragraph('Phone',st['TH']),Paragraph('Gender',st['TH'])],['','','','','',''],['','','','','','']],colWidths=[39*mm,20*mm,42*mm,35*mm,24*mm,17*mm],rowHeights=[17*mm,14*mm,14*mm],repeatRows=1)
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17365D')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),7),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#9AAFC3')),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
story.append(t)
h(3,'Title of the invention')
p('Budgeted Contract Repair for Agent Workflows Using Constraint-Ranked Repair Subgraphs and Verifiable Execution Certificates.')
h(4,'Technical field of the invention')
items(['Computer-implemented orchestration of software-agent and tool workflows represented as directed graphs.','Runtime validation of typed data artifacts against machine-evaluable interface and policy contracts.','Budget-, latency-, privacy-, and risk-aware selection and execution of workflow repairs.','Cryptographic integrity records for workflow execution and repair decisions.'])
h(5,'Prior art')
p('To be completed after a documented patent and non-patent literature search. No specific references or novelty conclusions are asserted here. Search areas: visual workflow orchestration; multi-agent workflow recovery; data/interface contract validation; automated plan or subgraph repair; budget-aware scheduling; and cryptographic provenance or Merkle logging.')
p('Databases, search terms, date, closest references, and differences: ______________________________________________')
h(6,'Objects of the invention')
items(['Detect failed contracts on artifacts flowing between workflow nodes and identify violated constraints.','Select a feasible repair subgraph from candidates by minimizing a weighted objective involving execution cost, latency, privacy risk, and residual failure risk.','Reject candidates exceeding remaining budget or violating graph, privacy, or interface constraints.','Insert a selected repair into a live execution plan while preserving acyclicity, then revalidate its output.','Create a hash-based certificate identifying the artifact, contract, failure, candidate decision, and repair result.','Support later integrity checks and reproducible inspection of the repair decision.'])
h(7,'Synopsis')
p('MindWeave-R is a proposed computer-implemented system for recovering agent workflows when an edge contract fails. A workflow is a directed graph whose nodes transform typed artifacts and whose edges specify requirements such as schema fields, provenance, confidence, privacy classification, freshness, and maximum cost. On failure, the system creates a structured failure report and retrieves candidate repair subgraphs. It filters candidates against hard constraints, including remaining budget, privacy policy, and graph validity, then ranks feasible candidates using configurable weights for cost, latency, privacy risk, and residual failure risk. The selected subgraph is inserted into the active execution plan and its output is checked against the failed contract. The system records cryptographic hashes of the relevant evidence in a repair certificate, optionally organized as a Merkle tree. This is a proposed mechanism; implementation coverage and performance require verification.')
h(8,'Brief description of drawings')
p('Figure 1: Contract failure detection, candidate filtering and ranking, repair execution, revalidation, and certificate generation.')
p('Figure 2: Constrained candidate-selection flow.')
p('Figure 3: Hash structure of a repair certificate. Formal drawings should be prepared and reconciled with the final specification.')
story.append(Spacer(1,3*mm));story.append(ArchitectureFigure());p('Figure 1. Runtime repair architecture for a failed workflow edge.','S')
story.append(PageBreak())
h(9,'Detailed description of the invention')
p('<b>Definitions.</b> A workflow graph G=(V,E) contains agent, tool, or module nodes. An edge carries an artifact and a machine-readable contract. An artifact is structured output with metadata such as schema, provenance, confidence, privacy level, creation time, and execution cost. A repair subgraph is a candidate sequence or DAG of operations intended to address one or more contract violations.')
p('<b>Contract evaluation.</b> Before downstream consumption, an evaluator checks the artifact against edge requirements. A contract may specify required fields or types, provenance, minimum confidence, allowed privacy level, maximum age, and cost ceiling. The evaluator returns a pass or a failure report with violation codes and observed values.')
p('<b>Candidate feasibility.</b> For a failure, the planner retrieves repair subgraphs associated with the failure codes. Candidate metadata can include estimated cost, latency, privacy risk, residual failure risk, and expected fixes. Candidates are excluded when they exceed remaining budget, violate privacy rules, create a cycle, lack required inputs, or breach configured hard constraints.')
p('<b>Ranking.</b> In one embodiment, J(r)=alpha*C(r)+beta*L(r)+gamma*P(r)+delta*R(r), where C is estimated cost, L latency, P privacy risk, R residual failure risk, and the weights are configurable and non-negative. The lowest-score feasible candidate is selected. If none is feasible, execution halts or follows a configured escalation route; the system does not silently treat the failed contract as satisfied.')
story.append(Spacer(1,2*mm));story.append(DecisionFigure());p('Figure 2. Candidate filtering, weighted ranking, repair execution, and contract revalidation.','S')
story.append(PageBreak())
h(9,'Detailed description of the invention continued')
p('<b>Graph splice and revalidation.</b> The selected repair subgraph is inserted between the producer and consumer of the failed edge. The system verifies interface compatibility and acyclicity, executes within the remaining budget, and evaluates the result against the original contract. Downstream execution resumes only on success. Otherwise a bounded alternative may be tried or execution terminates with a structured failure.')
p('<b>Repair certificate.</b> The system hashes canonical representations of the original artifact, contract, failure report, candidate set, selected repair, repaired output, and trace events. Event hashes may be combined into a Merkle tree; a stored root and inclusion proofs can support integrity verification. Hashes establish integrity of recorded data, not truth of model output or completeness of inputs.')
story.append(Spacer(1,3*mm));story.append(CertificateFigure());p('Figure 3. Verifiable repair-certificate evidence and Merkle-root record.','S')
p('<b>Example implementation.</b> A local embodiment may use typed Python services, NetworkX for graph validation and topological execution, SQLite for workflow and trace records, and a visual web canvas. Deterministic demo mode may emulate agent outputs; mock artifacts should be distinguished from real model/tool outputs. These are examples, not limitations.')
h(10,'Best method of performance of the invention')
for i,x in enumerate(['Receive a workflow DAG, node interfaces, edge contracts, candidate repair library, objective weights, and execution budget.','Validate the graph, then execute nodes in topological order while routing upstream artifacts to downstream inputs.','Evaluate each outgoing artifact against schema, provenance, confidence, privacy, freshness, and cost constraints.','On failure, record violation codes and retrieve candidate repair subgraphs associated with those codes.','Filter candidates against budget, privacy, interface compatibility, acyclicity, and retry limits.','Score feasible candidates with the configured objective and select the lowest-scoring candidate.','Insert and execute the selected repair; recheck its output against the original contract.','Resume downstream execution only after a pass; otherwise try a bounded alternative or safely halt.','Hash the inputs, failure, candidate decision, repair output, and trace; persist the certificate and optional Merkle root.'],1): p(f'{i}. {x}')
h(11,'Claims')
claims=['A computer-implemented method for recovering workflow execution, comprising executing nodes of a directed workflow graph; evaluating an artifact at an edge against a machine-readable contract; generating a failure report identifying contract violations; obtaining candidate repair subgraphs; filtering candidates according to at least remaining execution budget and graph validity; ranking filtered candidates using a score comprising weighted cost, latency, privacy risk, and residual failure risk; selecting a candidate; inserting and executing the selected repair subgraph; re-evaluating a resulting artifact against the contract; and recording a cryptographic certificate derived from data identifying the artifact, contract, failure report, selected candidate, and resulting artifact.','The method of claim 1, wherein the contract specifies one or more of required schema fields, provenance, minimum confidence, allowed privacy classification, maximum freshness age, or maximum execution cost.','The method of claim 1, wherein filtering excludes a candidate whose estimated cost exceeds a remaining workflow budget.','The method of claim 1, wherein graph validity includes verification that insertion does not create a directed cycle.','The method of claim 1, wherein the score is J(r)=alpha*C(r)+beta*L(r)+gamma*P(r)+delta*R(r), using configurable non-negative weights.','The method of claim 1, wherein downstream execution resumes only after contract revalidation succeeds, and otherwise the system tries a bounded alternative or halts.','The method of claim 1, wherein the certificate comprises event hashes combined into a Merkle tree and a stored root enabling integrity verification of at least a portion of an execution trace.','A workflow orchestration system comprising processors and memory storing instructions that cause performance of the method of any one of claims 1 to 7.','A non-transitory computer-readable medium storing instructions that cause performance of the method of any one of claims 1 to 7.']
for i,x in enumerate(claims,1):p(f'<b>{i}.</b> {x}')
h(12,'Inventive step (proposed contribution; subject to prior-art review)')
p('The proposed technical contribution is the combination of contract-specific failure diagnosis, feasibility filtering of repair subgraphs under budget and policy constraints, weighted selection using cost/latency/privacy/residual-risk factors, runtime graph insertion followed by contract revalidation, and a cryptographically verifiable record of the repair decision and outcome. Whether this is new, inventive, or patent-eligible requires a prior-art search and qualified legal review. No conclusion of novelty or patentability is made.')
h(13,'Industrial application')
items(['Agent-workflow orchestration in local or enterprise deployments.','Research and evidence-processing pipelines requiring provenance.','Document and content review workflows subject to privacy or policy constraints.','Audited workflows where failed intermediate outputs must not silently pass downstream.','Cloud, on-premises, or edge systems requiring bounded recovery under compute budgets.'])
h(14,'Abstract')
p('A computer-implemented method and system recover an agent workflow when an artifact fails a machine-readable edge contract. The system detects violations involving schema, provenance, confidence, privacy, freshness, or execution budget and obtains candidate repair subgraphs. It excludes candidates that violate constraints such as remaining budget, privacy policy, or graph acyclicity, and ranks feasible candidates using a configurable objective comprising cost, latency, privacy risk, and residual failure risk. A selected repair subgraph is inserted and executed. Downstream execution resumes only after the repaired artifact passes contract revalidation; otherwise a bounded alternative is attempted or execution halts. Cryptographic hashes of the artifact, contract, failure, candidate decision, output, and trace may be combined in a Merkle structure to form an integrity-verifiable repair certificate.')
h(15,'Drawings')
p('Figures 1 to 3 are included within the specification above. Before official filing, redraw the figures according to the applicable patent-office drawing rules and verify that every label and referenced feature is consistent with the final claims.')
review=Table([['Pre-filing review item','Status'],['Applicant and inventor particulars completed','Pending'],['Prior-art search recorded','Pending'],['Technical description checked against implementation','Pending'],['Claims reviewed by a patent professional','Pending'],['Drawing rules checked for filing jurisdiction','Pending']],colWidths=[115*mm,43*mm])
review.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('BACKGROUND',(0,1),(-1,-1),colors.HexColor('#F4F7FA')),('GRID',(0,0),(-1,-1),.4,LINE),('FONTSIZE',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(Spacer(1,4*mm));story.append(review)
p('Applicant/inventor confirmation and filing particulars: ______________________________________________')
p('_____________________________________________________________________________________')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(out)
