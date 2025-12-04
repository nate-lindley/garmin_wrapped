# Garmin Wrapped (unofficial)

Give people their year-end Garmin story without paying for a subscription. This project ingests your full Garmin data export and produces cleaned data plus visualizations.

## What it does right now
- Reads the Garmin summarized activities JSON from your full account export, cleans it, and writes a CSV to `data/clean/`.
- Filters to the 2025 season, drops multisport container rows, normalizes units (distance in cm → km/mi), and applies basic type cleanup.
- Generates charts (weekly distance/time, activity counts, HR distributions/zones) into `data/figures/`.

## Get your data
1. Request a full data export from Garmin: https://www.garmin.com/en-US/account/datamanagement/exportdata
2. Unzip, then locate the summarized activities JSON (e.g., `.../DI_CONNECT/DI-Connect-Fitness/<email>_0_summarizedActivities.json`).
3. Put the path into `.env`:
   ```
   GARMIN_SOURCE_PATH="/full/path/to/<email>_0_summarizedActivities.json"
   ```

## Setup & run
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python main.py
```
Outputs:
- Cleaned CSV: `data/clean/<source_stem>_clean.csv`
- Charts: `data/figures/`
- Console prints key stats for 2025.

## Notes
- Unofficial; not affiliated with Garmin.
- Data stays local. `.gitignore` is set to avoid committing your exports.

## Roadmap ideas
- Generate per-sport and overall totals (time, distance, elevation, calories).
- Find PRs (fastest run, longest ride, biggest climb) and streaks.
- Create “Wrapped” slides/graphics for sharing (PNG/SVG) with a simple theme.
- Allow selecting different years and trimming noisy activities.
- Package as a CLI and later a hosted uploader.
