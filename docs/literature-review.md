# Literature review — MindWeave-R

Working document for the IEEE paper draft. Twenty-five references, grouped into five
themes, each entry stating what the work establishes, what it does **not** do, and
what role it plays in our argument.

**Search method.** Records were checked against publisher pages, DOI records, DBLP,
ACL Anthology, arXiv and institutional repositories. Every entry below was confirmed
on at least one readable record page; nothing here was reconstructed from memory or
from a search snippet alone. Two entries carry a flagged metadata discrepancy (see
§6) — fix these before submission.

**Inclusion criteria.** (i) Peer-reviewed venue, or a widely cited systems report
with a stable arXiv identifier; (ii) relevance to at least one of: workflow
orchestration, data-contract validation, agent reliability, automated repair,
auditability; (iii) 1999–2025, with older work admitted only when it is the
canonical reference for a mechanism we build on.

---

## 1. Workflow orchestration and fault tolerance

**[deelman]** E. Deelman, K. Vahi, M. Rynge, R. Mayani, R. Ferreira da Silva,
G. Papadimitriou, and M. Livny, "The evolution of the Pegasus workflow management
software," *Computing in Science & Engineering*, vol. 21, no. 4, pp. 22–36, 2019.
DOI: 10.1109/MCSE.2019.2919690

- *Establishes:* separating workflow description from execution; mapping an abstract
  DAG onto heterogeneous execution environments; two decades of production use.
- *Does not:* constrain the semantic content of the data crossing a dependency.
- *Role:* canonical evidence that DAG orchestration is mature infrastructure, so our
  contribution must be about **what flows on the edges**, not about scheduling.

**[li2021]** Z. Li, V. Chang, H. Hu, H. Hu, C. Li, and J. Ge, "Real-time and dynamic
fault-tolerant scheduling for scientific workflows in clouds," *Information Sciences*,
vol. 568, pp. 13–39, 2021. DOI: 10.1016/j.ins.2021.03.003

- *Establishes:* replication, checkpointing, rescheduling after host failure, and
  dynamic resource adjustment for workflow tasks.
- *Does not:* treat a task that *succeeded* but produced unacceptable output as a
  fault at all.
- *Role:* defines the boundary of "fault tolerance" in the systems sense. Our faults
  are semantic, and they are invisible to this entire literature.

**[baylor]** D. Baylor *et al.*, "TFX: A TensorFlow-based production-scale machine
learning platform," in *Proc. 23rd ACM SIGKDD*, 2017, pp. 1387–1395.
DOI: 10.1145/3097983.3098021

- *Establishes:* an end-to-end pipeline architecture (analysis, validation, training,
  evaluation, serving) at production scale.
- *Does not:* decide what to do when validation fails beyond stopping the pipeline.
- *Role:* the closest industrial analogue to our architecture; useful for arguing
  that validation is already accepted practice, while *repair selection* is not.

**Synthesis.** This literature solves availability: retry, replicate, reschedule.
None of it addresses a step that completed successfully and emitted data that
violates a downstream expectation. That is the gap we occupy, and it is why a
throughput- or uptime-based evaluation would show no difference between our system
and a plain orchestrator.

---

## 2. Data validation, contracts and provenance

**[schelter]** S. Schelter, D. Lange, P. Schmidt, M. Celikel, F. Biessmann, and
A. Grafberger, "Automating large-scale data quality verification," *Proc. VLDB
Endow.*, vol. 11, no. 12, pp. 1781–1794, 2018. DOI: 10.14778/3229863.3229867 (Deequ)

- *Establishes:* declarative, expectation-based constraints computed at scale —
  "unit tests for data."
- *Does not:* propose a repair; it reports violations.
- *Role:* supplies the vocabulary our contract fields borrow (completeness,
  conformance, and threshold-style expectations).

**[caveness]** E. Caveness, P. Suganthan G. C., Z. Peng, N. Polyzotis, S. Roy, and
M. Zinkevich, "TensorFlow Data Validation: Data analysis and validation in continuous
ML pipelines," in *Proc. ACM SIGMOD*, 2020, pp. 2793–2796. DOI: 10.1145/3318464.3384707

- *Establishes:* schema inference and validation at pipeline boundaries, with skew
  detection between training and serving data.
- *Does not:* model per-connection expectations as first-class configuration, nor
  couple a violation to a recovery action.
- *Role:* anchors the "schema" code in our failure taxonomy.

**[tu]** D. Tu, Y. He, W. Cui, S. Ge, H. Zhang, S. Han, D. Zhang, and S. Chaudhuri,
"Auto-Validate by-History: Auto-program data quality constraints to validate recurring
data pipelines," in *Proc. 29th ACM SIGKDD*, 2023, pp. 4991–5003.
DOI: 10.1145/3580305.3599776

- *Establishes:* learning validation constraints from historical executions of
  recurring pipelines.
- *Does not:* operate per-edge at runtime, nor rank remedies under a budget.
- *Role:* the strongest recent argument that constraints should be **generated**,
  which is a natural extension of our hand-authored contracts.

**[curino]** C. A. Curino, H. J. Moon, and C. Zaniolo, "Graceful database schema
evolution: the PRISM workbench," *Proc. VLDB Endow.*, vol. 1, no. 1, pp. 761–772,
2008. DOI: 10.14778/1453856.1453939

- *Establishes:* managing schema change, propagating effects, migrating data,
  preserving legacy queries.
- *Does not:* concern itself with agent-to-agent handoffs or runtime repair choice.
- *Role:* background for why schema mismatch is a *repairable* class of failure
  rather than a fatal one.

**[rupprecht]** L. Rupprecht, J. C. Davis, C. Arnold, Y. Gur, and D. Bhagwat,
"Improving reproducibility of data science pipelines through transparent provenance
capture," *Proc. VLDB Endow.*, vol. 13, no. 12, pp. 3354–3368, 2020.
DOI: 10.14778/3415478.3415556

- *Establishes:* capturing system- and application-level provenance transparently
  enough to reproduce a pipeline run.
- *Does not:* use provenance as an *executable precondition* on an edge.
- *Role:* the closest prior work to our `provenance_required` contract field; our
  use is narrower (presence and lineage propagation, not full reproducibility).

**Synthesis.** Validation is well studied and increasingly automated, but the
literature treats a violation as a terminal event: log it, alert, halt. The decision
*what to do next* is left to a human or to a retry. Enforcement is also a deployment
policy rather than a specified decision procedure. We make the post-detection
decision explicit, budgeted, and recorded.

---

## 3. Reliability of LLM-based agents and multi-agent systems

**[yao]** S. Yao, J. Zhao, D. Yu, N. Du, I. Shafran, K. Narasimhan, and Y. Cao,
"ReAct: Synergizing reasoning and acting in language models," in *Proc. ICLR*, 2023.
arXiv:2210.03629

- *Establishes:* the interleaved reason-act-observe loop that underlies most agent
  frameworks.
- *Does not:* coordinate several agents or check handoffs.
- *Role:* defines the unit our nodes wrap.

**[wu]** Q. Wu, G. Bansal, J. Zhang, *et al.*, "AutoGen: Enabling next-gen LLM
applications via multi-agent conversation," arXiv:2308.08155, 2023.

- *Establishes:* customizable conversable agents and reusable conversation patterns
  as an orchestration primitive.
- *Does not:* impose schemas, budgets, or post-hoc verification on messages.
- *Role:* representative of the conversation-centric paradigm we deliberately do not
  follow — we constrain the *edge*, not the dialogue.

**[hong]** S. Hong, M. Zhuge, J. Chen, *et al.*, "MetaGPT: Meta programming for a
multi-agent collaborative framework," in *Proc. ICLR*, 2024.

- *Establishes:* role specialisation with standardised operating procedures, and
  explicitly discusses cascading hallucination when intermediate outputs go
  unverified.
- *Does not:* verify intermediate artifacts against a declared contract, nor recover
  from a failed check.
- *Role:* the strongest motivation in the literature for our problem statement.

**[cemri]** M. Cemri, M. Z. Pan, S. Yang, *et al.*, "Why do multi-agent LLM systems
fail?" in *Proc. NeurIPS Datasets & Benchmarks*, 2025.

- *Establishes:* an empirical taxonomy (MAST) of fourteen failure modes, grouped into
  system design, inter-agent misalignment, and **task verification**.
- *Does not:* propose a runtime mechanism to prevent or repair those failures.
- *Role:* the empirical warrant for building a verification boundary. Note that its
  "task verification" category is precisely what our contracts operationalise.

**[shinn]** N. Shinn, F. Cassano, E. Berman, A. Gopinath, K. Narasimhan, and S. Yao,
"Reflexion: Language agents with verbal reinforcement learning," in *Proc. NeurIPS*,
2023. arXiv:2303.11366

**[madaan]** A. Madaan, N. Tandon, P. Gupta, *et al.*, "Self-Refine: Iterative
refinement with self-feedback," in *Proc. NeurIPS*, 2023. arXiv:2303.17651

- *Establish:* that an agent can improve its own output using feedback, without
  weight updates.
- *Do not:* establish that self-assessment is reliable — in both cases the critic is
  the same model that produced the output.
- *Role:* motivates an *external* check. Our contract checker does not ask the agent
  whether it did well, which is the methodological point of the system.

**[gou]** Z. Gou, Z. Shao, Y. Gong, Y. Shen, Y. Yang, N. Duan, and W. Chen, "CRITIC:
Large language models can self-correct with tool-interactive critiquing," in *Proc.
ICLR*, 2024. arXiv:2305.11738

- *Establishes:* grounding critique in external tools rather than self-assessment.
- *Role:* closest in spirit to our checker; ours differs by being a static predicate
  over artifact metadata plus a *repair decision*, not an extra model call.

**[ruan]** Y. Ruan, H. Dong, A. Wang, *et al.*, "Identifying the risks of LM agents
with an LM-emulated sandbox," in *Proc. ICLR*, 2024. arXiv:2309.15817

- *Establishes:* systematic risk identification for tool-using agents in an emulated
  environment.
- *Does not:* enforce anything at runtime.
- *Role:* supports our claim that agent risk is usually studied at evaluation time
  rather than at execution time.

**Synthesis.** This body of work improves the *agent*: better reasoning, better
self-critique, better tool use. It is largely silent on the *composition* level,
where an artifact produced by one agent becomes the premise of the next. Our
contribution is orthogonal and composable: we do not change any agent, we constrain
its handoffs.

---

## 4. Automated repair of code, plans and processes

**[legoues]** C. Le Goues, M. Pradel, and A. Roychoudhury, "Automated program
repair," *Communications of the ACM*, vol. 62, no. 12, pp. 56–65, 2019.
DOI: 10.1145/3318162

- *Establishes:* the standard APR pipeline — fault localisation, patch generation,
  validation against a test oracle — and its open problems (overfitting, patch
  correctness).
- *Does not:* address data artifacts, spend budgets, or privacy constraints.
- *Role:* the structural template for our pipeline, and the source of our caution:
  APR's central lesson is that "passes the oracle" is not "correct," which is exactly
  the trap our own results fall into (§VII).

**[zhang]** Q. Zhang, C. Fang, Y. Ma, *et al.*, "A survey of learning-based automated
program repair," *ACM Trans. Softw. Eng. Methodol.*, vol. 33, no. 2, art. 55, 2024.
DOI: 10.1145/3631974

- *Establishes:* the current taxonomy of learning-based repair and its evaluation
  practices.
- *Role:* situates repair-candidate ranking as a mature idea in code, which is why we
  do not claim ranking itself as novel — only its instantiation over artifacts with
  privacy and residual-risk terms.

**[scala]** E. Scala, "Plan repair for resource constrained tasks via numeric macro
actions," in *Proc. ICAPS*, vol. 24, no. 1, 2014, pp. 280–288.
DOI: 10.1609/icaps.v24i1.13624

- *Establishes:* repairing plans that carry numeric resource constraints, using macro
  actions.
- *Does not:* operate on data artifacts, nor consider privacy.
- *Role:* the closest formal precedent for "repair under a resource bound." Our budget
  constraint is the same idea with a monetary wallet as the resource.

**[fahland]** D. Fahland and W. M. P. van der Aalst, "Model repair — aligning process
models to reality," *Information Systems*, vol. 47, pp. 220–243, 2015.
DOI: 10.1016/j.is.2013.12.007

**[polyvyanyy]** A. Polyvyanyy, W. M. P. van der Aalst, A. H. M. ter Hofstede, and
M. T. Wynn, "Impact-driven process model repair," *ACM Trans. Softw. Eng. Methodol.*,
vol. 25, no. 4, art. 28, 2016. DOI: 10.1145/2980764

- *Establish:* repairing a *process model* so that it agrees with observed behaviour,
  with an explicit notion of repair impact.
- *Do not:* repair a single execution at runtime; they are offline, log-driven
  operations.
- *Role:* distinguishes structural repair (change the graph) from artifact repair
  (change the data). We implement the latter and describe the former as future work,
  which is a cleaner scope than conflating them.

**Synthesis.** Three mature repair traditions — code, plans, process models — share a
pipeline shape we reuse, and none of them targets a runtime artifact crossing a
declared contract, under a spend budget, with privacy as a first-class cost. That
combination is where our contribution sits, and we are careful to claim the
combination, not the components.

---

## 5. Provenance, auditability and human oversight

**[moreau]** L. Moreau, P. Groth, J. Cheney, T. Lebo, and S. Miles, "The rationale of
PROV," *Journal of Web Semantics*, vol. 35, pp. 235–257, 2015.
DOI: 10.1016/j.websem.2015.04.001

- *Establishes:* the design rationale behind the PROV family — entities, activities,
  agents, and the derivation relations between them.
- *Role:* our provenance field is a deliberately minimal subset of PROV's idea; this
  is the citation that keeps us honest about not reinventing an ontology badly.

**[schneier]** B. Schneier and J. Kelsey, "Secure audit logs to support computer
forensics," *ACM Trans. Inf. Syst. Secur.*, vol. 2, no. 2, pp. 159–176, 1999.
DOI: 10.1145/317087.317089

- *Establishes:* tamper-evident logs built from hash chaining, and a precise account
  of what such a construction does and does not guarantee without a trusted
  time source or secret key.
- *Role:* the basis for our certificate section. This paper is why we state
  explicitly that a Merkle root proves integrity only, and not authenticity or
  completeness.

**[green]** B. Green, "The flaws of policies requiring human oversight of government
algorithms," *Computer Law & Security Review*, vol. 45, art. 105681, 2022.
DOI: 10.1016/j.clsr.2022.105681

- *Establishes:* that mandating a human in the loop does not by itself produce
  meaningful review; oversight can be nominal.
- *Role:* constrains our claims. We implement an approval gate; we do not claim it
  constitutes effective oversight, and we say so.

**[cobbe]** J. Cobbe, M. S. A. Lee, and J. Singh, "Reviewable automated decision-making:
A framework for accountable algorithmic systems," in *Proc. ACM FAccT*, 2021.
DOI: 10.1145/3442188.3445921

- *Establishes:* reviewability as a system property — the ability of an outside party
  to reconstruct and interrogate a decision.
- *Role:* gives us the vocabulary for why a per-decision certificate matters: the
  record of *why this repair was chosen* is the reviewable object, not just the final
  output.

**Synthesis.** Auditability is usually treated as logging. Our narrower, checkable
claim is that the *decision* to repair — the failure codes, the candidate pool, the
selected operator, the before/after hashes — should be hash-committed so it can be
replayed and contested later.

---

## 6. Gap statement (what the paper claims)

Across all five themes, three things are consistently absent:

- **G1 — Runtime, per-edge enforcement as a decision.** Validators detect; they do
  not decide. Contracts are configured per pipeline, not per connection, and
  enforcement is a deployment policy.
- **G2 — Repair selection for artifacts under joint constraints.** Repair exists for
  code, plans and process models. No prior work selects among artifact-level repair
  operators subject to a hard spend budget together with privacy and residual-failure
  risk.
- **G3 — A committed record of the repair decision.** Provenance and tamper-evident
  logging exist separately from repair. Coupling them — so that the *choice* is
  auditable, not only the outcome — is what we implement.

What we explicitly do **not** claim: a novel repair algorithm; that repairs restore
information; that contract satisfaction implies validity; or any patentable novelty.

---

## 7. Metadata to fix before submission

Four entries have a discrepancy or an unchecked field. None affects the argument;
all should be resolved against the publisher record before the reference list is
final.

| Ref | Issue |
|---|---|
| [zhang] | ACM record was not directly fetchable; issue number, article number and page range need a publisher-side check. |
| [polyvyanyy] | Accessible repository record omits pages. Commonly cited as art. 28, 28:1–28:60, and sometimes dated 2017 rather than 2016. |
| [schneier] | The ACM record gives vol. 2, no. 2; the author's own page gives vol. 1, no. 3. We use the ACM metadata. |
| [hong] | ICLR lists the third author as J. Chen; arXiv lists J. Chen / J. Chen variants across versions. Verify against the camera-ready. |

Also note: [wu], [shinn], [madaan] are cited as arXiv preprints or NeurIPS
proceedings. If a journal version exists by submission time, cite that instead.
