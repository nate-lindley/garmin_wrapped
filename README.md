# Garmin Wrapped (unofficial)

Give people their year-end Garmin story without paying for a subscription. This project ingests the CSV export of your Garmin activities and will grow into a shareable “Wrapped” summary you can email or post.

## What it does right now
- Loads your Garmin `Activities.csv` export (see below) and filters to the 2025 season.
- Cleans up distance values and gets the data ready for analysis/visualization in `main.py`.
- Foundation for generating charts and highlights with `pandas` and `matplotlib`.

## Getting your data
1. Log in to Garmin Connect (web), go to **Activities** → **All Activities**.
2. Use the gear icon to **Export CSV** (or use the full account export and grab `Activities.csv`).
3. Save the file as `data/Activities.csv` in this repo. (The `data/ex.txt` file is just a placeholder.)

## Running it
```bash
pip install pandas matplotlib
python main.py
```
The script currently filters the 2025 rows and normalizes distances. Add your own analysis/plots in `main.py` to experiment, or follow the roadmap below.

## Roadmap ideas
- Generate per-sport and overall totals (time, distance, elevation, calories).
- Find PRs (fastest run, longest ride, biggest climb) and most consistent streaks.
- Create “Wrapped” slides/graphics for sharing (PNG/SVG) with a simple theme.
- Allow selecting different years and trimming noisy activities.
- Package as a small CLI and later a hosted version with upload support.

## Notes
- Unofficial; not affiliated with Garmin. The goal is to bypass the paywall and let anyone enjoy their own Wrapped.
- CSVs are ignored by git via `.gitignore`, so your activity data stays local.
