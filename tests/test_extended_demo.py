import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_extended_demo_data import generate_extensions


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_extended_events_and_experiment_tables_are_consistent(tmp_path):
    players = [
        [i, "2026-01-01", "paid_social" if i % 2 else "paid_search", i % 3 + 1, "US", "Android" if i % 2 else "iOS"]
        for i in range(1, 25)
    ]
    write_csv(tmp_path / "players.csv", ["player_id", "install_date", "channel", "campaign_id", "country", "platform"], players)
    write_csv(
        tmp_path / "iap_transactions.csv",
        ["transaction_id", "player_id", "transaction_timestamp", "product_type", "usd_amount"],
        [[1, 1, "2026-01-03 12:00:00", "starter_bundle", "0.99"], [2, 8, "2026-01-05 10:00:00", "coin_pack", "9.99"]],
    )

    counts = generate_extensions(tmp_path, seed=11)
    ad_events = read_csv(tmp_path / "ad_delivery_events.csv")
    assignments = read_csv(tmp_path / "experiment_assignments.csv")
    exposures = read_csv(tmp_path / "experiment_exposures.csv")
    sessions = read_csv(tmp_path / "player_sessions.csv")
    outcomes = read_csv(tmp_path / "experiment_player_outcomes.csv")

    player_ids = {str(row[0]) for row in players}
    assert counts["players"] == 24
    assert len(assignments) == 24 and len(outcomes) == 24
    assert len({row["assignment_id"] for row in assignments}) == 24
    assert len({row["request_id"] for row in ad_events}) == len(ad_events)
    assert all(row["player_id"] in player_ids for row in ad_events + sessions + exposures)
    assert all(row["d7_observation_complete"] == "1" for row in outcomes)
    assert json.loads((tmp_path / "demo_metadata.json").read_text())["data_origin"] == "synthetic_generated"

    impressions = [row for row in ad_events if row["impression_id"]]
    clicks = [row for row in ad_events if row["click_id"]]
    assert impressions and len(clicks) <= len(impressions)
    assert all(row["impression_id"] for row in clicks)
    assert all(float(row["revenue_usd"]) == 0 for row in ad_events if row["request_status"] == "no_fill")

    mapping = {row["player_id"]: row for row in read_csv(tmp_path / "player_app_mapping.csv")}
    strata = {}
    for assignment in assignments:
        player = next(row for row in players if str(row[0]) == assignment["player_id"])
        key = (mapping[assignment["player_id"]]["app_id"], player[2], player[5])
        strata.setdefault(key, []).append(assignment["variant"])
    assert all(abs(group.count("control") - group.count("treatment")) <= 1 for group in strata.values())
