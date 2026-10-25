"""Reproducible experiment harness for the MindWeave-R paper draft.

Run from the repository root:

    ./.venv/Scripts/python.exe -m backend.experiments.paper_experiments

Writes ``results.json`` and four CSV tables next to this file. No network,
no model calls: every agent in the pipeline is the deterministic demo agent,
so repeated runs are byte-identical and the numbers are auditable by hand.

Experiment map
--------------
E1  end-to-end repair success for six injected contract-fault classes
E2  contract-gate ablation: violations that leak downstream when the gate is off
E3  compound faults: behaviour when one artifact violates several codes at once
E4  decision-rule comparison on a constructed multi-fix candidate pool
"""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path

from fastapi import HTTPException

from backend.app import main
from backend.app.main import (
    Contract,
    Failure,
    NODE,
    Workflow,
    candidates,
    check_contract,
    choose,
    execute_graph,
    repair,
    run_node,
    sample,
)

HERE = Path(__file__).parent
REPS = 30
WALLET = 100.0
TEMPLATE = "Evidence Research"

# Fault class -> (forceFailure payload on the Researcher node, contract tightening
# on the Researcher -> Source Curator edge).
FAULTS: dict[str, tuple[dict, dict]] = {
    "confidence": ({"confidence": 0.1}, {"min_confidence": 0.8}),
    "schema": ({"dropFields": ["evidence"]}, {"required_fields": ["evidence", "citations"]}),
    "provenance": ({"emptyProvenance": True}, {"provenance_required": True}),
    "privacy": ({"privacy": "confidential"}, {"privacy": "public"}),
    "freshness": ({"staleSeconds": 10.0}, {"freshness_seconds": 1}),
    "budget": ({}, {"max_cost": 0.5}),
}

FAULT_CLASSES = list(FAULTS)

# A candidate pool with candidates that repair more than one code at a time.
# Used only for E4, which evaluates the scoring rule itself, not the catalogue.
CONSTRUCTED_POOL = [
    {"id": "thorough-recompute", "cost": 3.0, "latency": 1, "privacy_risk": 0.05, "residual_failure_risk": 0.02, "fixes": ["schema", "confidence"]},
    {"id": "cheap-repair", "cost": 0.5, "latency": 1, "privacy_risk": 0.00, "residual_failure_risk": 0.30, "fixes": ["schema", "confidence"]},
    {"id": "slow-reconciler", "cost": 1.0, "latency": 4, "privacy_risk": 0.20, "residual_failure_risk": 0.05, "fixes": ["schema", "confidence"]},
    {"id": "balanced-reconciler", "cost": 1.5, "latency": 2, "privacy_risk": 0.02, "residual_failure_risk": 0.06, "fixes": ["schema", "confidence"]},
    {"id": "privacy-scrubbing", "cost": 1.2, "latency": 2, "privacy_risk": 0.00, "residual_failure_risk": 0.09, "fixes": ["schema", "confidence"]},
]


def poison(cls: str) -> dict:
    """Return a valid Evidence Research workflow with one injected fault."""
    w = deepcopy(sample(TEMPLATE))
    force, tighten = FAULTS[cls]
    w["nodes"][1]["data"]["forceFailure"] = deepcopy(force)
    w["edges"][1]["data"]["contract"].update(deepcopy(tighten))
    return w


def edge_contract(w: dict) -> Contract:
    return Contract(**w["edges"][1]["data"]["contract"])


def nominal_cost(w: dict) -> float:
    return sum(NODE[n["data"]["kind"]][4] for n in w["nodes"])


def first_artifact(w: dict):
    """Run the faulted source node in isolation so we can inspect the artifact."""
    upstream = run_node(w["nodes"][0], [])
    return run_node(w["nodes"][1], [upstream])


def placeholders(art, contract: Contract) -> list[str]:
    """Payload fields that the repair filled with a synthetic placeholder."""
    return [
        f for f in contract.required_fields
        if isinstance(art.payload.get(f), str) and art.payload[f].startswith("repaired:")
    ]


# --------------------------------------------------------------------------- E1
def experiment_1() -> tuple[list[dict], list[dict]]:
    unit, end_to_end = [], []
    for cls in FAULT_CLASSES:
        rows = []
        for _ in range(REPS):
            w = poison(cls)
            contract = edge_contract(w)
            before = first_artifact(w)
            failure = check_contract(before, contract, WALLET)
            pool = candidates(failure)
            picked = choose(pool, WALLET)
            after = repair(before, picked, contract) if picked else None
            residual = check_contract(after, contract, WALLET) if after else None

            trace, final, repairs, waiting = execute_graph(Workflow(**w), WALLET)
            charged = sum(x.get("output", {}).get("cost", 0) for x in trace if "output" in x)
            charged += sum(r["candidate"]["cost"] for r in repairs)
            rows.append(
                {
                    "codes": failure.codes,
                    "pool_size": len(pool),
                    "chosen": picked.id if picked else None,
                    "repair_cost": picked.cost if picked else 0.0,
                    "residual_risk": picked.residual_failure_risk if picked else None,
                    "post_repair_codes": residual.codes if residual else None,
                    "placeholder_fields": placeholders(after, contract) if after else [],
                    "payload_changed": bool(after) and after.payload != before.payload,
                    "confidence_before": round(before.confidence, 4),
                    "confidence_after": round(after.confidence, 4) if after else None,
                    "end_to_end_repaired": bool(repairs),
                    "end_to_end_candidate": repairs[0]["candidate"]["id"] if repairs else None,
                    "trace_steps": len(trace),
                    "credits_charged": round(charged, 2),
                    "final_present": "final_output" in final.payload,
                    "waiting_approval": waiting,
                    "overhead_pct": round(100 * (picked.cost if picked else 0.0) / nominal_cost(w), 1),
                }
            )

        # The pipeline is deterministic, so a class is one behaviour repeated REPS times.
        assert len({json.dumps(r, sort_keys=True) for r in rows}) == 1, f"{cls} is not deterministic"
        r = rows[0]
        unit.append({"fault": cls, **r})
        end_to_end.append(
            {
                "fault": cls,
                "detected_codes": r["codes"],
                "candidates": r["pool_size"],
                "repair_applied": r["end_to_end_candidate"],
                "post_repair_satisfied": r["post_repair_codes"] == [],
                "placeholders": " ".join(r["placeholder_fields"]) or "-",
                "payload_changed": r["payload_changed"],
                "confidence": f"{r['confidence_before']}->{r['confidence_after']}",
                "end_to_end_repaired": r["end_to_end_repaired"],
                "trace_steps": r["trace_steps"],
                "credits": r["credits_charged"],
                "repair_overhead_pct": r["overhead_pct"],
                "rows_agree": REPS,
            }
        )
    return unit, end_to_end# --------------------------------------------------------------------------- E2

def run_with_gate(cls: str, gate_on: bool) -> dict:
    """Execute one poisoned workflow, optionally bypassing contract enforcement.

    The spy always audits with the real checker, so we can count violations in
    both conditions; only in the gated condition is the result acted upon.
    """
    observed: list[Failure] = []
    original = main.check_contract

    def spy(art, contract, remaining, _orig=original):
        verdict = _orig(art, contract, remaining)
        observed.append(verdict)
        return verdict if gate_on else Failure(codes=[], detail={})

    main.check_contract = spy
    try:
        w = poison(cls)
        trace, final, repairs, _ = execute_graph(Workflow(**w), WALLET, allow_approval=False)
    finally:
        main.check_contract = original

    violations = [f for f in observed if f.codes]
    bad = {f.detail["artifact"] for f in violations}
    consumed = any(h in bad for step in trace for h in step.get("inputs", []))
    charged = sum(x.get("output", {}).get("cost", 0) for x in trace if "output" in x)
    charged += sum(r["candidate"]["cost"] for r in repairs)
    return {
        "violations": len(violations),
        "consumed": consumed,
        "repairs": len(repairs),
        "status": "completed" if "final_output" in final.payload else "incomplete",
        "credits": round(charged, 2),
    }


def experiment_2() -> list[dict]:
    out = []
    for cls in FAULT_CLASSES:
        off, on = run_with_gate(cls, False), run_with_gate(cls, True)
        out.append(
            {
                "fault": cls,
                "off_violations": off["violations"],
                "off_consumed": off["consumed"],
                "off_repairs": off["repairs"],
                "off_credits": off["credits"],
                "on_violations": on["violations"],
                "on_consumed": on["consumed"],
                "on_repairs": on["repairs"],
                "on_credits": on["credits"],
                "off_status": off["status"],
                "on_status": on["status"],
            }
        )
    return out


# --------------------------------------------------------------------------- E3
def experiment_3() -> list[dict]:
    """Two simultaneous codes on one artifact: can the catalogue repair it?"""
    out = []
    for force, tighten in (
        ({"confidence": 0.1, "dropFields": ["evidence"]}, {"min_confidence": 0.8, "required_fields": ["evidence", "citations"]}),
        ({"confidence": 0.1, "emptyProvenance": True}, {"min_confidence": 0.8, "provenance_required": True}),
        ({"dropFields": ["evidence"], "privacy": "confidential"}, {"required_fields": ["evidence", "citations"], "privacy": "public"}),
    ):
        w = deepcopy(sample(TEMPLATE))
        w["nodes"][1]["data"]["forceFailure"] = force
        w["edges"][1]["data"]["contract"].update(tighten)
        contract = edge_contract(w)
        before = first_artifact(w)
        failure = check_contract(before, contract, WALLET)
        pool = candidates(failure)
        blocked = False
        message = ""
        try:
            execute_graph(Workflow(**w), WALLET)
        except HTTPException as exc:
            blocked = True
            message = str(exc.detail.get("message", ""))
        out.append(
            {
                "codes": sorted(failure.codes),
                "candidate_pool": len(pool),
                "selection": "none" if not pool else choose(pool, WALLET).id,
                "execution_blocked": blocked,
                "status": "repair unavailable" if blocked else "repaired",
                "message": message,
            }
        )
    return out


# --------------------------------------------------------------------------- E4
def experiment_4() -> list[dict]:
    """Compare the weighted rule against three baselines on a constructed pool."""
    pool = [main.RepairCandidate(**c) for c in CONSTRUCTED_POOL]
    weights = (1, 0.2, 4, 6)
    a, b, c, d = weights
    score = {p.id: a * p.cost + b * p.latency + c * p.privacy_risk + d * p.residual_failure_risk for p in pool}
    rules = {
        "weighted (proposed)": lambda ps: choose(ps, WALLET, weights),
        "least cost": lambda ps: min(ps, key=lambda p: p.cost),
        "least residual risk": lambda ps: min(ps, key=lambda p: p.residual_failure_risk),
        "first feasible (catalogue order)": lambda ps: ps[0],
    }
    rows = []
    for name, rule in rules.items():
        p = rule(pool)
        rows.append(
            {
                "rule": name,
                "selected": p.id,
                "cost": p.cost,
                "latency": p.latency,
                "privacy_risk": p.privacy_risk,
                "residual_failure_risk": p.residual_failure_risk,
                "score": round(score[p.id], 3),
            }
        )
    return rows


# --------------------------------------------------------------------------- E5
def experiment_5() -> dict:
    """False-positive check: a healthy workflow must trigger no repair at all."""
    original = main.check_contract
    rows = set()
    for _ in range(REPS):
        observed: list[Failure] = []

        def spy(art, contract, remaining, _orig=original, _log=observed):
            verdict = _orig(art, contract, remaining)
            _log.append(verdict)
            return verdict

        main.check_contract = spy
        try:
            w = sample(TEMPLATE)
            trace, _, repairs, _ = execute_graph(Workflow(**w), WALLET, allow_approval=False)
        finally:
            main.check_contract = original
        credits = sum(x.get("output", {}).get("cost", 0) for x in trace if "output" in x)
        rows.add((len(repairs), sum(1 for f in observed if f.codes), round(credits, 2)))
    assert len(rows) == 1, f"healthy runs diverge: {rows}"
    repairs, violations, credits = rows.pop()
    return {"healthy_runs": REPS, "repairs": repairs, "violations": violations, "credits": credits}


def main_run() -> dict:
    unit, end_to_end = experiment_1()
    gate = experiment_2()
    compound = experiment_3()
    selection = experiment_4()
    healthy = experiment_5()

    results = {
        "meta": {
            "template": TEMPLATE,
            "fault_classes": FAULT_CLASSES,
            "repetitions_per_class": REPS,
            "wallet": WALLET,
            "nominal_workflow_cost": nominal_cost(poison("budget")),
            "total_injections": REPS * len(FAULT_CLASSES),
        },
        "e1_unit": unit,
        "e1_end_to_end": end_to_end,
        "e2_gate_ablation": gate,
        "e3_compound": compound,
        "e4_selection": selection,
        "e5_healthy": healthy,
    }

    (HERE / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    def write(name: str, rows: list[dict]) -> None:
        with (HERE / name).open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    write("e1_fault_classes.csv", end_to_end)
    write("e2_gate_ablation.csv", gate)
    write("e4_selection.csv", selection)

    print(f"nominal workflow cost: {results['meta']['nominal_workflow_cost']} credits")
    print(f"injections: {results['meta']['total_injections']} (all deterministic)\n")

    print("E1 - per fault class")
    print(f"{'fault':<11}{'repair':<19}{'post':>5} {'payload':>8} {'conf':>12} {'creds':>6} {'over%':>7} {'fill':<10}")
    for r in end_to_end:
        print(f"{r['fault']:<11}{str(r['repair_applied']):<19}{str(r['post_repair_satisfied']):>5} "
              f"{str(r['payload_changed']):>8} {r['confidence']:>12} {r['credits']:>6} "
              f"{r['repair_overhead_pct']:>7} {r['placeholders']:<10}")

    print("\nE2 - gate ablation (violations reaching downstream agents)")
    print(f"{'fault':<11}{'off_v':>6}{'off_cons':>9}{'off_rep':>8}{'on_v':>5}{'on_cons':>8}{'on_rep':>7} {'status':>10}")
    for r in gate:
        print(f"{r['fault']:<11}{r['off_violations']:>6}{str(r['off_consumed']):>9}{r['off_repairs']:>8} "
              f"{r['on_violations']:>5}{str(r['on_consumed']):>8}{r['on_repairs']:>7} {r['off_status']:>10}")

    print("\nE3 - compound faults")
    for r in compound:
        print(f"  {r['codes']} pool={r['candidate_pool']} -> {r['status']}")

    print("\nE4 - decision rule on constructed pool")
    for r in selection:
        print(f"  {r['rule']:<34}{r['selected']:<22}score={r['score']}")

    print(f"\nE5 - healthy control: {healthy['healthy_runs']} runs, repairs={healthy['repairs']}, "
          f"violations={healthy['violations']}, credits={healthy['credits']}")

    return results


if __name__ == "__main__":
    main_run()
