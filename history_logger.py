import csv
from pathlib import Path
from datetime import datetime

HISTORY_FILE = Path(__file__).with_name("analysis_history.csv")

FIELDNAMES = [
    "timestamp",
    "home_team",
    "away_team",
    "minute",
    "home_goals",
    "away_goals",
    "stoppage",
    "home_reds",
    "away_reds",
    "pressure",
    "draw_price",
    "under_price",
    "over_price",
    "recommended",
    "confidence",
    "best_edge",
    "final_home_goals",
    "final_away_goals",
    "actual_draw",
    "actual_under_2_5",
    "actual_over_2_5",
    "recommended_hit",
    "settled",
]


def ensure_history_file():
    if not HISTORY_FILE.exists():
        with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
        return

    with open(HISTORY_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        existing_rows = list(reader)
        existing_fields = reader.fieldnames or []

    if existing_fields == FIELDNAMES:
        return

    normalized_rows = []
    for row in existing_rows:
        new_row = {field: row.get(field, "") for field in FIELDNAMES}
        normalized_rows.append(new_row)

    with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(normalized_rows)


def read_history():
    ensure_history_file()
    with open(HISTORY_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_history(rows):
    with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def log_analysis(row: dict) -> None:
    ensure_history_file()

    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)

        writer.writerow({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "home_team": row.get("home_team", ""),
            "away_team": row.get("away_team", ""),
            "minute": row.get("minute", ""),
            "home_goals": row.get("home_goals", ""),
            "away_goals": row.get("away_goals", ""),
            "stoppage": row.get("stoppage", ""),
            "home_reds": row.get("home_reds", ""),
            "away_reds": row.get("away_reds", ""),
            "pressure": row.get("pressure", ""),
            "draw_price": row.get("draw_price", ""),
            "under_price": row.get("under_price", ""),
            "over_price": row.get("over_price", ""),
            "recommended": row.get("recommended", ""),
            "confidence": row.get("confidence", ""),
            "best_edge": row.get("best_edge", ""),
            "final_home_goals": "",
            "final_away_goals": "",
            "actual_draw": "",
            "actual_under_2_5": "",
            "actual_over_2_5": "",
            "recommended_hit": "",
            "settled": "0",
        })


def settle_match_by_index(index: int, final_home_goals: int, final_away_goals: int) -> bool:
    rows = read_history()
    if not rows:
        return False

    if index < 0 or index >= len(rows):
        return False

    row = rows[index]

    total_goals = final_home_goals + final_away_goals
    actual_draw = "1" if final_home_goals == final_away_goals else "0"
    actual_under_2_5 = "1" if total_goals <= 2 else "0"
    actual_over_2_5 = "1" if total_goals >= 3 else "0"

    recommended = row.get("recommended", "").strip().upper()

    recommended_hit = "0"
    if recommended == "DRAW" and actual_draw == "1":
        recommended_hit = "1"
    elif recommended == "UNDER 2.5" and actual_under_2_5 == "1":
        recommended_hit = "1"
    elif recommended == "OVER 2.5" and actual_over_2_5 == "1":
        recommended_hit = "1"

    row["final_home_goals"] = str(final_home_goals)
    row["final_away_goals"] = str(final_away_goals)
    row["actual_draw"] = actual_draw
    row["actual_under_2_5"] = actual_under_2_5
    row["actual_over_2_5"] = actual_over_2_5
    row["recommended_hit"] = recommended_hit
    row["settled"] = "1"

    rows[index] = row
    write_history(rows)
    return True


def summarize_accuracy():
    rows = read_history()
    settled_rows = [r for r in rows if r.get("settled", "0") == "1"]

    total = len(settled_rows)
    if total == 0:
        return {
            "total_settled": 0,
            "recommended_hit_rate": 0.0,
            "draw_hit_rate": 0.0,
            "under_hit_rate": 0.0,
            "over_hit_rate": 0.0,
        }

    recommended_hits = sum(1 for r in settled_rows if r.get("recommended_hit") == "1")
    draw_hits = sum(1 for r in settled_rows if r.get("actual_draw") == "1")
    under_hits = sum(1 for r in settled_rows if r.get("actual_under_2_5") == "1")
    over_hits = sum(1 for r in settled_rows if r.get("actual_over_2_5") == "1")

    return {
        "total_settled": total,
        "recommended_hit_rate": round(100 * recommended_hits / total, 1),
        "draw_hit_rate": round(100 * draw_hits / total, 1),
        "under_hit_rate": round(100 * under_hits / total, 1),
        "over_hit_rate": round(100 * over_hits / total, 1),
    }