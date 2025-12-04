from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # use non-interactive backend for headless environments
import matplotlib.pyplot as plt
import pandas as pd

CLEAN_PATH = Path("data/summarized_activities_clean.csv")
FIG_DIR = Path("data/figures")


def load_cleaned_data(path: Path = CLEAN_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    for col in ["start_time_local", "start_time_gmt", "begin_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def apply_sport_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Combine similar sport labels for clearer charts."""
    df = df.copy()
    if "sportType" in df:
        df["sport_group"] = df["sportType"].replace({"TRAINING": "FITNESS_EQUIPMENT"})
    return df


def drop_container_activities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove multisport container rows from totals/plots.
    Containers are usually sportType MULTISPORT or flagged as parent=True.
    """
    mask_container = False
    if "sportType" in df:
        mask_container |= df["sportType"].eq("MULTISPORT")
    if "parent" in df:
        mask_container |= df["parent"].fillna(False)
    return df.loc[~mask_container].copy()


def filter_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Keep only activities whose local start time is in the given year."""
    if "start_time_local" not in df:
        return df
    return df[df["start_time_local"].dt.year == year].copy()

def compute_stats(df: pd.DataFrame) -> dict[str, Any]:
    stats: dict[str, Any] = {}

    stats["activity_count"] = len(df)

    if "start_time_local" in df:
        start_dates = df["start_time_local"].dropna()
        if not start_dates.empty:
            stats["date_range"] = (
                start_dates.min().date().isoformat(),
                start_dates.max().date().isoformat(),
            )

    if "distance_mi" in df:
        stats["total_miles"] = round(df["distance_mi"].fillna(0).sum(), 2)
        stats["median_miles"] = round(df["distance_mi"].median(), 2)

    if "duration_minutes" in df:
        total_hours = df["duration_minutes"].fillna(0).sum() / 60
        stats["total_hours"] = round(total_hours, 2)
        stats["median_duration_min"] = round(df["duration_minutes"].median(), 2)

    if "calories" in df:
        stats["total_calories"] = int(df["calories"].fillna(0).sum())

    if "avgHr" in df:
        stats["avg_heart_rate"] = round(df["avgHr"].mean(), 1)
        stats["max_heart_rate"] = int(df["maxHr"].max()) if "maxHr" in df else None

    if "sport_group" in df:
        stats["top_sports"] = df["sport_group"].value_counts().head(5).to_dict()

    return stats


def plot_activity_counts(df: pd.DataFrame) -> None:
    if "sport_group" not in df:
        return
    top = df["sport_group"].value_counts().head(10)
    plt.figure(figsize=(8, 5))
    top.plot(kind="bar", color="#4C6FFF")
    plt.title("Activity Count by Sport")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "activity_counts.png", dpi=150)
    plt.close()


def plot_distance_over_time(df: pd.DataFrame) -> None:
    if "start_time_local" not in df or "distance_mi" not in df:
        return
    daily = (
        df.dropna(subset=["start_time_local"])
        .assign(date=lambda d: d["start_time_local"].dt.date)
        .groupby("date")["distance_mi"]
        .sum()
        .sort_index()
    )
    if daily.empty:
        return
    plt.figure(figsize=(10, 4))
    plt.plot(daily.index, daily.values, color="#FF7A59")
    plt.title("Distance per Day (miles)")
    plt.xlabel("Date")
    plt.ylabel("Miles")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "distance_over_time.png", dpi=150)
    plt.close()


def plot_heart_rate_hist(df: pd.DataFrame) -> None:
    if "avgHr" not in df:
        return
    plt.figure(figsize=(8, 4))
    df["avgHr"].dropna().plot(kind="hist", bins=20, color="#00A676", edgecolor="black")
    plt.title("Average Heart Rate Distribution")
    plt.xlabel("BPM")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "heart_rate_hist.png", dpi=150)
    plt.close()


def plot_duration_by_sport(df: pd.DataFrame) -> None:
    if "duration_minutes" not in df or "sport_group" not in df:
        return
    agg = (
        df[["sport_group", "duration_minutes"]]
        .dropna()
        .groupby("sport_group")["duration_minutes"]
        .median()
        .sort_values(ascending=False)
        .head(10)
    )
    if agg.empty:
        return
    plt.figure(figsize=(8, 5))
    agg.plot(kind="bar", color="#F2C94C")
    plt.title("Median Duration by Sport (minutes)")
    plt.ylabel("Minutes")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "median_duration_by_sport.png", dpi=150)
    plt.close()


def plot_hr_zone_distribution(df: pd.DataFrame) -> None:
    zone_cols = sorted(
        [c for c in df.columns if c.startswith("hrTimeInZone_")],
        key=lambda c: int(c.split("_")[-1]),
    )
    if not zone_cols:
        return

    totals_min = df[zone_cols].fillna(0).sum() / 60000  # ms -> minutes
    labels = [f"Zone {c.split('_')[-1]}" for c in totals_min.index]

    plt.figure(figsize=(8, 4))
    plt.bar(labels, totals_min.values, color="#7B61FF")
    plt.title("Total Time in Heart Rate Zones")
    plt.ylabel("Minutes")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "hr_zone_distribution.png", dpi=150)
    plt.close()


def plot_weekly_totals(df: pd.DataFrame) -> None:
    if "start_time_local" not in df:
        return

    temp = df.dropna(subset=["start_time_local"]).copy()
    temp["week_start"] = temp["start_time_local"].dt.to_period("W").dt.start_time

    if "distance_mi" in temp:
        weekly_dist = (
            temp.groupby("week_start")["distance_mi"]
            .sum()
            .sort_index()
        )
        if not weekly_dist.empty:
            plt.figure(figsize=(10, 4))
            plt.plot(weekly_dist.index, weekly_dist.values, color="#4C6FFF")
            plt.title("Weekly Distance (miles)")
            plt.xlabel("Week starting")
            plt.ylabel("Miles")
            plt.tight_layout()
            plt.savefig(FIG_DIR / "weekly_distance.png", dpi=150)
            plt.close()

    if "duration_minutes" in temp:
        weekly_dur = (
            temp.groupby("week_start")["duration_minutes"]
            .sum()
            .sort_index()
        )
        if not weekly_dur.empty:
            plt.figure(figsize=(10, 4))
            plt.plot(weekly_dur.index, weekly_dur.values, color="#FF7A59")
            plt.title("Weekly Time (minutes)")
            plt.xlabel("Week starting")
            plt.ylabel("Minutes")
            plt.tight_layout()
            plt.savefig(FIG_DIR / "weekly_time.png", dpi=150)
            plt.close()


def main() -> None:
    df = load_cleaned_data()
    df = filter_year(df, 2025)
    df = drop_container_activities(df)
    df = apply_sport_groups(df)
    stats = compute_stats(df)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    plot_activity_counts(df)
    plot_distance_over_time(df)
    plot_heart_rate_hist(df)
    plot_duration_by_sport(df)
    plot_hr_zone_distribution(df)
    plot_weekly_totals(df)

    print("Key stats:")
    for key, value in stats.items():
        print(f"- {key}: {value}")

    print(f"\nCharts saved to {FIG_DIR}")


if __name__ == "__main__":
    main()
