# Hermes Workflow: Thumbnail Direction

## Purpose
Turn the latest validated Script Writer report into three original, source-aware thumbnail concepts and one recommended direction. This is Milestone 4. It creates packaging direction only; it does not generate thumbnail images or publish anything.

## Preconditions
- Milestone 3 has produced a validated canonical script report in SQLite.
- The script already traces back to a human-approved strategy opportunity.
- No separate thumbnail approval is required to brainstorm concepts, but any later image generation remains a separate human-triggered action.

## Agent boundary
- Deterministic Python owns script selection, context construction, source IDs, concept-count rules, thumbnail-text limits, validation, persistence, and Markdown rendering.
- One Hermes Thumbnail Director subagent owns creative packaging judgment.
- Competitor source metadata is topic/performance evidence only. There are no competitor thumbnail images in the input.

## Run procedure
1. Change into the `yt-manager` repository and activate its virtual environment.
2. Do not rerun research, strategy, or script writing for this step.
3. Run `python scripts/prepare_thumbnail.py`.
4. Read `outputs/YYYY-MM-DD-thumbnail-input.json` completely.
5. Read `prompts/thumbnail-director.md` and `schemas/thumbnail-director-output.schema.json` completely.
6. Call the built-in `delegate_task` tool exactly once for the Thumbnail Director. Do not invent a thumbnail-generation Python command and do not simulate the subagent yourself.
7. In the delegated context, explicitly provide the project root, prompt path, thumbnail-input path, schema path, and output path.
8. Require JSON-only output written to `outputs/YYYY-MM-DD-thumbnail-draft.json`.
9. Verify the draft file exists and parses as JSON.
10. Run:
    `python scripts/finalize_thumbnail.py outputs/YYYY-MM-DD-thumbnail-input.json outputs/YYYY-MM-DD-thumbnail-draft.json`
11. If finalization fails, give the exact validation error back to the same Thumbnail Director for at most one correction attempt. Do not weaken validation.
12. Only after finalization exits successfully, read `outputs/YYYY-MM-DD-thumbnails.md` and summarize the recommended concept, alternatives, required creator assets, and risks for Joel.

## Concept rules
- Return exactly three concepts with ranks 1, 2, and 3.
- Select exactly one recommended rank.
- Each concept must be a genuinely different packaging hypothesis with a distinct visual hook.
- Thumbnail text may be empty; when used, keep it within the configured word limit.
- Thumbnail text should complement the title rather than repeat it.
- Every concept must cite only source video IDs permitted by the validated script.
- If a concept needs Joel's face, screenshots, terminal output, product UI, or other real assets, list them in `creator_assets_needed`.
- `render_prompt` is a handoff for a later image/design step, not permission to generate an image now.

## Evidence rules
- Do not infer competitor thumbnail visuals from competitor titles.
- Do not claim competitor colors, faces, layouts, or objects performed well; those visuals are not part of this evidence set.
- Competitor performance can support the topic/packaging territory only.
- Preserve the validated script's core promise and strategic angle.

## Guardrails
- No actual thumbnail image generation.
- No image editing.
- No thumbnail upload.
- No video publishing or scheduling.
- No YouTube account mutation.
- No automatic approval of a future generated image.

## Success criteria
A successful Milestone 4 run produces:
- one thumbnail-input JSON built from a validated Script Writer report
- one real delegated Thumbnail Director result
- exactly three validated concepts and one recommended rank
- one canonical thumbnail-direction JSON
- one human-readable Markdown report
- persisted thumbnail report + ranked concepts in SQLite
- explicit creator assets and render prompts for a later human-triggered design step
