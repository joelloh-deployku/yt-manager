# yt-manager

AI-assisted YouTube research and content operations system powered by an always-on Hermes operator and a Codex-maintained codebase.

## Milestone 1: Research foundation
Milestone 1 established deterministic competitor research, a configurable 14-day candidate window, historical channel baselines, outlier scoring, repeated view snapshots, velocity, and Markdown daily research reports stored against SQLite runtime state.

## Milestone 2: Hermes Strategist
Milestone 2 adds source-backed opportunity selection: `prepare_daily_strategy.py` packages the latest research, Hermes delegates one Strategist, and `finalize_strategy.py` validates/persists three ranked opportunities.

## Milestone 3: Human-approved Script Writer
Milestone 3 adds a hard human strategy-to-script approval boundary. `approve_strategy.py` records Joel's exact chosen rank, `prepare_script.py` packages that opportunity, Hermes delegates one Script Writer, and `finalize_script.py` validates a full source-aware script with creator placeholders and verification notes.

## Milestone 4: Thumbnail Director
Milestone 4 turns a validated script into exactly three distinct thumbnail/packaging concepts plus one recommended rank. It validates short thumbnail text, source IDs, distinct visual hooks, creator-asset needs, and render-ready direction. It does **not** generate a thumbnail image.

## Milestone 5: Content QA Gate
Milestone 5 reviews the validated script + thumbnail package as one unit without modifying either asset. QA returns `PASS` or `NEEDS_CHANGES` with structured findings. `PASS` means the generated package is coherent enough for Joel's next human production step; it is not fact-check completion or publishing approval.

Explicit `[JOEL: ...]` placeholders, creator inputs, and verification notes remain visible as open human work.

## Milestone 6: Production Handoff / Delivery
Milestone 6 turns one QA-passed package into a single recording/editing brief:

1. `python scripts/prepare_delivery.py` selects the latest persisted QA report and refuses to continue unless its status is `PASS`.
2. The deterministic input includes the validated script, QA findings, recommended thumbnail concept, creator inputs, verification notes, and approval lineage.
3. Hermes delegates exactly one Delivery Producer using `prompts/delivery-producer.md`.
4. The Delivery Producer sequences recording segments, maps every creator placeholder, carries every verification item, preserves the recommended thumbnail, builds an asset plan, adds editing notes, and creates a pre-recording checklist.
5. `python scripts/finalize_delivery.py ...` validates complete coverage before persisting the handoff and rendering Markdown.

Milestone 6 does not resolve creator inputs or verification notes automatically. It does not generate images, edit video, upload, publish, schedule, or mutate any YouTube account.

## Setup

```bash
git clone https://github.com/joelloh-deployku/yt-manager.git
cd yt-manager
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configure `.env`, then initialize and test:

```bash
python scripts/init_db.py
python -m pytest
```

## Operational flow

### Research and strategy

```bash
python scripts/run_daily_research.py
python scripts/prepare_daily_strategy.py
```

After Hermes produces `outputs/YYYY-MM-DD-strategy-draft.json`:

```bash
python scripts/finalize_strategy.py \
  outputs/YYYY-MM-DD-strategist-input.json \
  outputs/YYYY-MM-DD-strategy-draft.json
```

### Human approval and script

```bash
python scripts/approve_strategy.py --rank 1
python scripts/prepare_script.py
```

After Hermes produces `outputs/YYYY-MM-DD-script-draft.json`:

```bash
python scripts/finalize_script.py \
  outputs/YYYY-MM-DD-script-input.json \
  outputs/YYYY-MM-DD-script-draft.json
```

### Thumbnail direction

```bash
python scripts/prepare_thumbnail.py
```

After Hermes produces `outputs/YYYY-MM-DD-thumbnail-draft.json`:

```bash
python scripts/finalize_thumbnail.py \
  outputs/YYYY-MM-DD-thumbnail-input.json \
  outputs/YYYY-MM-DD-thumbnail-draft.json
```

### Content QA

```bash
python scripts/prepare_qa.py
```

After Hermes produces `outputs/YYYY-MM-DD-qa-draft.json`:

```bash
python scripts/finalize_qa.py \
  outputs/YYYY-MM-DD-qa-input.json \
  outputs/YYYY-MM-DD-qa-draft.json
```

### Production handoff / delivery

```bash
python scripts/prepare_delivery.py
```

The deterministic input is `outputs/YYYY-MM-DD-production-input.json`. After the real Hermes Delivery Producer writes `outputs/YYYY-MM-DD-delivery-draft.json`:

```bash
python scripts/finalize_delivery.py \
  outputs/YYYY-MM-DD-production-input.json \
  outputs/YYYY-MM-DD-delivery-draft.json
```

Canonical delivery outputs are:
- `outputs/YYYY-MM-DD-delivery.json`
- `outputs/YYYY-MM-DD-delivery.md`

Reports are written to `outputs/`. Runtime state is stored in `data/yt_manager.db`. Both are ignored by Git.

## Delivery invariants
- Production handoff requires persisted QA status `PASS`.
- Every creator placeholder must appear exactly once in the recording plan.
- Every verification-note item must appear exactly once in the verification plan.
- The recommended thumbnail rank, concept name, text, and creator-assets list must remain unchanged.
- Required thumbnail assets must be present in the asset plan.
- The Delivery Producer does not rewrite upstream script, thumbnail, or QA assets.

## Key workflow files
- `workflows/daily-research.md`
- `workflows/daily-strategy.md`
- `workflows/script-writing.md`
- `workflows/thumbnail-direction.md`
- `workflows/content-qa.md`
- `workflows/delivery-handoff.md`
- `prompts/strategist.md`
- `prompts/script-writer.md`
- `prompts/thumbnail-director.md`
- `prompts/qa.md`
- `prompts/delivery-producer.md`
- `schemas/strategist-output.schema.json`
- `schemas/script-writer-output.schema.json`
- `schemas/thumbnail-director-output.schema.json`
- `schemas/qa-output.schema.json`
- `schemas/delivery-output.schema.json`

## Division of responsibility
- **Hermes:** operational execution and focused Strategist, Script Writer, Thumbnail Director, QA, and Delivery Producer delegation.
- **Codex:** engineering, tests, integrations, migrations, debugging, and maintainability.
- **Deterministic Python:** API ingestion, scoring, approvals, context construction, gates, validation, persistence, and reports.
- **Joel:** chooses the strategy opportunity, supplies real creator evidence/assets, resolves verification work, records/edits content, and controls any later image generation or publishing action.

## After Milestone 6
Later layers may cover human-reviewed metadata/editing workflows, explicit publishing approvals/integrations, analytics, additional research agents, and the weekly channel audit. None of those actions are authorized by a Milestone 6 delivery report.
