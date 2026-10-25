# Architecture

```text
React + React Flow canvas → FastAPI REST API → SQLite
            ↓                  ↓
       contracts/guardrails  NetworkX DAG validation
                               ↓
                      demo agents / execution trace
```

Edges carry schema, confidence, privacy, freshness, and spend constraints. The API blocks invalid DAGs before execution. Human Approval always creates an auditable pause before Final Output.
