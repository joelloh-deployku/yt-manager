# Milestone 6: Production Handoff / Delivery

Milestone 6 starts only after a persisted QA `PASS`.

Its job is to convert the validated content package into one human production brief without changing the underlying creative assets.

## Inputs
- QA PASS and non-blocking findings
- validated script and its exact `[JOEL: ...]` creator inputs
- unresolved verification notes
- validated recommended thumbnail concept and required creator assets
- strategy/approval lineage

## Output
The Delivery Producer returns ordered recording segments, complete creator-input coverage, a verification plan, exact thumbnail handoff, asset plan, editing notes, pre-recording checklist, and risks.

Deterministic validation rejects the handoff if a creator placeholder or verification item is dropped, if the recommended thumbnail changes, or if its required assets disappear.

## Runtime files
- prepared input: `outputs/YYYY-MM-DD-production-input.json`
- delegated draft: `outputs/YYYY-MM-DD-delivery-draft.json`
- canonical JSON: `outputs/YYYY-MM-DD-delivery.json`
- canonical Markdown: `outputs/YYYY-MM-DD-delivery.md`

## State
SQLite stores one `production_reports` row per QA report plus normalized `production_items` for recording, verification, assets, editing, and checklist entries.

The production schema is additive and is created by the delivery preparation/finalization path, so existing research, strategy, script, thumbnail, and QA state is preserved.

## Boundary
This artifact is a human shoot/edit brief. It is not proof of recording completion, image-generation approval, editing completion, publishing approval, upload authorization, or YouTube account mutation.
