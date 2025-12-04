import json
import os
from pathlib import Path

import pandas as pd

ENV_SOURCE_KEY = "GARMIN_SOURCE_PATH"


def read_activity_records(path: Path) -> list[dict]:
    """Load raw activity export while handling the different export shapes."""
    raw = json.loads(path.read_text())

    if isinstance(raw, list):
        if raw and isinstance(raw[0], dict) and "summarizedActivitiesExport" in raw[0]:
            return raw[0]["summarizedActivitiesExport"]
        return raw

    if isinstance(raw, dict) and "summarizedActivitiesExport" in raw:
        return raw["summarizedActivitiesExport"]

    raise ValueError("Unrecognized summarized activities format")


def _ms_to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, unit="ms", errors="coerce")


def build_clean_dataframe(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records)

    # Simplify nested/irrelevant columns that make the frame hard to scan.
    df = df.drop(
        columns=[
            "summarizedExerciseSets",
            "summarizedDiveInfo",
            "uuidMsb",
            "uuidLsb",
            "rule",
        ],
        errors="ignore",
    )

    # Normalize timestamps into readable datetimes.
    if "startTimeGmt" in df:
        df["start_time_gmt"] = _ms_to_datetime(df["startTimeGmt"])
    if "startTimeLocal" in df:
        df["start_time_local"] = _ms_to_datetime(df["startTimeLocal"])
    if "beginTimestamp" in df:
        df["begin_time"] = _ms_to_datetime(df["beginTimestamp"])

    # Convert durations from milliseconds to minutes.
    duration_map = {
        "duration": "duration_minutes",
        "elapsedDuration": "elapsed_minutes",
        "movingDuration": "moving_minutes",
    }
    for raw_col, clean_col in duration_map.items():
        if raw_col in df:
            df[clean_col] = df[raw_col] / 60000

    # Helpful unit conversions.
    # Garmin distance is in centimeters; convert to km/mi.
    if "distance" in df:
        df["distance_km"] = df["distance"] / 100_000
        df["distance_mi"] = df["distance_km"] * 0.621371
    if "avgSpeed" in df:
        df["avg_speed_mph"] = df["avgSpeed"] * 2.23694  # m/s -> mph
    if "calories" in df and "duration_minutes" in df:
        df["calories_per_min"] = df["calories"] / df["duration_minutes"].replace(
            {0: pd.NA}
        )

    # Reorder for a quick scan of the most useful columns first.
    preferred_order = [
        "activityId",
        "name",
        "activityType",
        "sportType",
        "start_time_local",
        "start_time_gmt",
        "duration_minutes",
        "moving_minutes",
        "distance_km",
        "distance_mi",
        "avg_speed_mph",
        "avgHr",
        "maxHr",
        "steps",
        "calories",
        "calories_per_min",
        "trainingEffectLabel",
        "moderateIntensityMinutes",
        "vigorousIntensityMinutes",
        "totalSets",
        "totalReps",
    ]
    existing = [c for c in preferred_order if c in df.columns]
    remaining = [c for c in df.columns if c not in existing]

    return df[existing + remaining]


def tidy_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prune sparse/constant columns and normalize types for readability."""
    null_frac = df.isna().mean()
    sparse_cols = [c for c in df.columns if null_frac[c] > 0.9]
    constant_cols = []
    for col in df.columns:
        try:
            if df[col].nunique(dropna=False) == 1:
                constant_cols.append(col)
        except TypeError:
            # Columns holding dict/list objects cannot be hashed; leave them in.
            continue

    boolean_like = [
        "parent",
        "pr",
        "elevationCorrected",
        "decoDive",
        "purposeful",
        "autoCalcCalories",
        "favorite",
        "atpActivity",
    ]
    for col in boolean_like:
        if col in df.columns:
            df[col] = df[col].astype(bool)

    id_cols = ["activityId", "userProfileId", "deviceId", "eventTypeId", "timeZoneId"]
    for col in id_cols:
        if col in df.columns:
            df[col] = df[col].astype("Int64")

    df = df.drop(columns=sparse_cols + constant_cols, errors="ignore")
    return df


def main() -> None:
    source_path = resolve_source_path()
    output_path = Path("data/clean") / f"{source_path.stem}_clean.csv"

    clean_df = clean_summarized_activities(source=source_path, output=output_path)

    # Run exploratory analysis/visualization on the cleaned data.
    from exploration import run_analysis

    run_analysis(clean_path=output_path, year=2025)

    print("\nCleaning + analysis complete. Clean CSV:", output_path)


def clean_summarized_activities(
    source: Path | str,
    output: Path | str | None = None,
) -> pd.DataFrame:
    """
    End-to-end cleaning utility: load raw Garmin export JSON, normalize fields,
    prune sparse/constant columns, and optionally persist to CSV.
    """
    source_path = Path(source)
    records = read_activity_records(source_path)

    clean_df = build_clean_dataframe(records)
    clean_df = tidy_dataframe(clean_df)

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        clean_df.to_csv(output_path, index=False)

    return clean_df


def resolve_source_path() -> Path:
    """
    Resolve the input JSON path from environment or .env.
    Priority:
    1) GARMIN_SOURCE_PATH env var
    2) GARMIN_SOURCE_PATH entry in .env
    3) default data/summarized_activities.json
    """
    # 1) environment variable
    env_path = os.getenv(ENV_SOURCE_KEY)

    # 2) .env file fallback
    if not env_path:
        env_file = Path(".env")
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    if key.strip() == ENV_SOURCE_KEY:
                        env_path = value.strip().strip('"').strip("'")
                        break

    # 3) default path
    if not env_path:
        env_path = "data/summarized_activities.json"

    source_path = Path(env_path).expanduser()
    if not source_path.exists():
        raise FileNotFoundError(
            f"Source JSON not found at {source_path}. Set {ENV_SOURCE_KEY} in .env or env."
        )
    return source_path


if __name__ == "__main__":
    main()
