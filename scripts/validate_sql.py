"""Load the committed CSV snapshot into MySQL 8.0, execute the SQL library and verify key outputs."""
from __future__ import annotations

import csv
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import mysql.connector

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

TABLES = {
    "ua_campaigns": {
        "file": "ua_campaigns.csv",
        "columns": ["campaign_id", "channel", "campaign_name", "start_date", "end_date"],
        "integers": {"campaign_id"},
        "dates": {"start_date", "end_date"},
    },
    "ua_spend": {
        "file": "ua_spend.csv",
        "columns": ["spend_id", "campaign_id", "channel", "spend_date", "daily_spend_usd", "installs"],
        "integers": {"spend_id", "campaign_id", "installs"},
        "dates": {"spend_date"},
        "decimals": {"daily_spend_usd"},
    },
    "players": {
        "file": "players.csv",
        "columns": ["player_id", "install_date", "channel", "campaign_id", "country", "platform"],
        "integers": {"player_id", "campaign_id"},
        "dates": {"install_date"},
    },
    "iap_transactions": {
        "file": "iap_transactions.csv",
        "columns": ["transaction_id", "player_id", "transaction_timestamp", "product_type", "usd_amount"],
        "integers": {"transaction_id", "player_id"},
        "datetimes": {"transaction_timestamp"},
        "decimals": {"usd_amount"},
    },
    "ad_revenue_events": {
        "file": "ad_revenue_events.csv",
        "columns": ["event_id", "player_id", "event_timestamp", "ad_type", "revenue_usd"],
        "integers": {"event_id", "player_id"},
        "datetimes": {"event_timestamp"},
        "decimals": {"revenue_usd"},
    },
}


def convert(value: str, column: str, spec: dict):
    if value == "":
        return None
    if column in spec.get("integers", set()):
        return int(float(value))
    if column in spec.get("dates", set()):
        return date.fromisoformat(value)
    if column in spec.get("datetimes", set()):
        return datetime.fromisoformat(value)
    if column in spec.get("decimals", set()):
        return Decimal(value)
    return value


def load_table(cursor, table: str, spec: dict, batch_size: int = 2000) -> int:
    path = DATA / spec["file"]
    columns = spec["columns"]
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    total = 0
    batch = []
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        for row in reader:
            batch.append(tuple(convert(row[col], col, spec) for col in columns))
            if len(batch) >= batch_size:
                cursor.executemany(sql, batch)
                total += len(batch)
                batch.clear()
        if batch:
            cursor.executemany(sql, batch)
            total += len(batch)
    return total


def strip_comment_lines(sql_text: str) -> str:
    return "\n".join(
        line for line in sql_text.splitlines()
        if not line.lstrip().startswith("--")
    )


def main() -> None:
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
        schema_text = strip_comment_lines((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))
        for statement in schema_text.split(";"):
            if statement.strip():
                cursor.execute(statement)

        row_counts = {}
        for table, spec in TABLES.items():
            row_counts[table] = load_table(cursor, table, spec)
        connection.commit()
        print("Loaded rows:", row_counts)

        cursor.execute("""
            SELECT channel, ROUND(SUM(daily_spend_usd) / NULLIF(SUM(installs), 0), 2) AS blended_cac
            FROM ua_spend
            GROUP BY channel
        """)
        cac = {channel: float(value) for channel, value in cursor.fetchall()}
        assert abs(cac["cross_promo"] - 0.45) < 0.01, cac
        assert abs(cac["paid_social"] - 1.54) < 0.01, cac
        assert abs(cac["paid_search"] - 3.16) < 0.01, cac
        print("Verified paid-channel blended CAC:", cac)

        queries_text = strip_comment_lines((ROOT / "sql" / "analysis_queries.sql").read_text(encoding="utf-8"))
        executed = 0
        for statement in queries_text.split(";"):
            statement = statement.strip()
            if not statement:
                continue
            cursor.execute(statement)
            if cursor.with_rows:
                cursor.fetchall()
            executed += 1
        print(f"Successfully executed {executed} SQL statements against MySQL 8.0.")
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
