# Wiki Update Log

> Change history for this bundle (OKF `log.md`, §9). Date-grouped, **newest first**,
> ISO `## YYYY-MM-DD` headings. Entries lead with a bold kind — `**Ingest**`, `**Update**`,
> `**Query**`, `**Lint**`, `**Schema**`, `**Creation**`, `**Deprecation**` — by convention.

## 2026-09-23

* **Schema**: Aligned the vault with [OKF v0.2](../OKF.md) — `timestamp` → `generated: { by, at }`,
  provenance moved to `sources`, added `status`/`stale_after`/`verified`, reserved `status`
  for the OKF lifecycle vocabulary (project and experiment state moved to `stage`), and
  reshaped `index.md` and `log.md` to §8/§9.
* **Schema**: Added type `attested-computation` (`templates/attested-computation.md`, OKF §10).

## 2026-07-13

* **Initialization**: Scaffolded the starter vault with example pages.
