# Hermes Home Server Setup - Milestone 1

## 1. Verify Hermes

Run:

```bash
hermes doctor
hermes
```

Make sure a normal Hermes conversation works before scheduling anything.

## 2. Clone the repository

```bash
git clone https://github.com/joelloh-deployku/yt-manager.git
cd yt-manager
git checkout milestone-1
```

After the Milestone 1 PR is merged, use `main` instead.

## 3. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Configure secrets

```bash
cp .env.example .env
```

Set `YOUTUBE_API_KEY` and `COMPETITOR_CHANNEL_IDS`. Use YouTube channel IDs beginning with `UC`, not display names or @handles.

Never commit `.env`.

## 5. Initialize SQLite

```bash
python scripts/init_db.py
```

## 6. Verify tests

```bash
python -m pytest
```

## 7. First manual research run

```bash
python scripts/run_daily_research.py
```

Confirm a report appears under `outputs/` and the SQLite database exists under `data/`.

## 8. Hermes manual run

Give Hermes the instructions in `workflows/daily-research.md` and have it execute the workflow manually. Do this for several successful runs before adding a schedule.

## 9. Scheduling

Only after manual runs are reliable, create a Hermes scheduled job that runs the daily research workflow. Keep publishing disabled.

## Failure handling

If the pipeline fails, retain the error and run record. Codex on the main machine should investigate and fix the underlying engineering issue through the shared Git repository.
