---
type: attested-computation
title: <What this computes>
description: <one-line: the value produced and whose definition it follows>
aliases: []
tags: []
status: stable                      # draft | stable | deprecated  (OKF §5.4)
runtime: <bigquery | postgres | dbt | python | …>   # REQUIRED for this type (OKF §10.2)
parameters:
  - { name: <param>, type: <integer|string|date|…>, required: true }
executor:                           # how a run happens, and what evidence it must return
  resource: ../../raw/<topic>/<run-instructions-or-code>
  receipt: [<job_id>, <executed_sql>, <result>]
attester:                           # deterministic (no-LLM) code that checks a receipt
  resource: ../../raw/<topic>/<attester>.py
# computation: ../../raw/<topic>/<query>.sql   # use instead of the body fence for long/generated code
generated: { by: <actor>, at: <YYYY-MM-DDTHH:MM:SSZ> }
# verified: { by: human:<id>, at: <YYYY-MM-DDTHH:MM:SSZ> }
# stale_after: <YYYY-MM-DDTHH:MM:SSZ>
sources:
  - id: <source-id>
    resource: <policy / definition URL>
    title: <the definition this computation implements>
---

# <What this computes>

## Computation

    <the single sanctioned computation — one fenced block; parameters bound by name>

<Prose explaining what it implements, attributed to the defining source.>[^source-id]

## Notes

An agent may supply **values** for the declared `parameters` only — it must not author or
edit the computation (OKF §10.3). Concepts that need the value link here rather than
restating it. Delete this template if the vault has no attested computations; the type is
optional.

[^source-id]: <the definition this computation implements>
