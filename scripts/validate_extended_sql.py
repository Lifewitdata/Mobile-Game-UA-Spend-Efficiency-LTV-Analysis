"""Load and validate the optional generated extension tables in MySQL 8.0+."""
from __future__ import annotations

import csv
import os
from pathlib import Path

import mysql.connector

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("UA_DATA_DIR", ROOT / "data" / "generated_extended")).resolve()
TABLE_FILES = {
    "apps": ("apps.csv", ["app_id", "app_name", "genre", "package_name"]),
    "demand_partners": ("demand_partners.csv", ["demand_partner_id", "partner_name", "mediation_group"]),
    "player_app_mapping": ("player_app_mapping.csv", ["player_id", "app_id", "mapping_source"]),
    "player_sessions": ("player_sessions.csv", ["session_id", "player_id", "app_id", "session_start", "session_end", "session_duration_seconds", "session_day"]),
    "experiment_assignments": ("experiment_assignments.csv", ["assignment_id", "experiment_id", "player_id", "variant", "assigned_at", "randomization_unit", "allocation_design", "data_origin"]),
    "experiment_exposures": ("experiment_exposures.csv", ["exposure_id", "experiment_id", "player_id", "variant", "exposure_timestamp", "app_id"]),
    "ad_delivery_events": ("ad_delivery_events.csv", ["request_id", "player_id", "app_id", "demand_partner_id", "session_id", "request_timestamp", "ad_format", "request_status", "impression_id", "click_id", "revenue_usd", "experiment_id", "experiment_variant"]),
    "experiment_player_outcomes": ("experiment_player_outcomes.csv", ["experiment_id", "player_id", "assigned_variant", "assignment_id", "was_exposed", "sessions_first_7d", "retained_d7", "ad_revenue_first_7d_usd", "iap_revenue_first_7d_usd", "total_revenue_first_7d_usd", "d7_observation_complete"]),
}


def load_csv(cursor, table: str, filename: str, columns: list[str], batch_size: int = 2000) -> int:
    placeholders = ", ".join(["%s"] * len(columns))
    statement = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    total = 0
    batch = []
    with (DATA / filename).open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            batch.append(tuple(row[column] for column in columns))
            if len(batch) >= batch_size:
                cursor.executemany(statement, batch)
                total += len(batch)
                batch.clear()
        if batch:
            cursor.executemany(statement, batch)
            total += len(batch)
    return total


def strip_comment_lines(sql_text: str) -> str:
    return "\n".join(line for line in sql_text.splitlines() if not line.lstrip().startswith("--"))


def main() -> None:
    if not (DATA / "demo_metadata.json").is_file():
        raise FileNotFoundError(f"Missing synthetic dataset manifest in {DATA}. Run generate_extended_demo_data.py first.")

    connection = mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DATABASE", "mobile_game_ua"),
        autocommit=False,
    )
    cursor = connection.cursor()
    try:
        # Clean extension child tables in FK-safe order so the validator is repeatable.
        for table in [
            "experiment_player_outcomes", "ad_delivery_events", "experiment_exposures",
            "experiment_assignments", "player_sessions", "player_app_mapping",
            "demand_partners", "apps",
        ]:
            cursor.execute(f"DELETE FROM {table}")

        schema = strip_comment_lines((ROOT / "sql" / "extended_demo_schema.sql").read_text(encoding="utf-8"))
        for statement in schema.split(";"):
            if statement.strip():
                cursor.execute(statement)

        counts = {}
        for table, (filename, columns) in TABLE_FILES.items():
            counts[table] = load_csv(cursor, table, filename, columns)
        connection.commit()
        print("Loaded extended synthetic tables:", counts)

        cursor.execute("SELECT COUNT(*) FROM ad_delivery_events")
        request_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ad_delivery_events WHERE impression_id <> ''")
        impression_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ad_delivery_events WHERE click_id <> ''")
        click_count = cursor.fetchone()[0]
        assert request_count == counts["ad_delivery_events"]
        assert 0 < click_count <= impression_count <= request_count

        sql_text = strip_comment_lines((ROOT / "sql" / "extended_demo_queries.sql").read_text(encoding="utf-8"))
        executed = 0
        for statement in sql_text.split(";"):
            statement = statement.strip()
            if not statement:
                continue
            cursor.execute(statement)
            if cursor.with_rows:
                cursor.fetchall()
            executed += 1
        connection.commit()
        print(f"Successfully executed {executed} extended MySQL analysis statements.")
        print(f"Validated ad funnel: requests={request_count:,}, impressions={impression_count:,}, clicks={click_count:,}.")
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
