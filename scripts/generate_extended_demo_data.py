"""Generate a separate, clearly synthetic mobile-game ad, retention and experiment dataset.

The script reuses the project's deterministic base demo generator, then adds
app mapping, ad request/impression/click, session and experiment tables. It never
writes into the committed source snapshot in data/.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_demo_data import EVENT_END, generate as generate_base

EXPERIMENT_ID = "interstitial_frequency_cap_v1"
APPS = [
    ["app_001", "Puzzle Harbor", "Puzzle", "com.demo.puzzleharbor"],
    ["app_002", "Word Trails", "Word", "com.demo.wordtrails"],
    ["app_003", "Merge Meadow", "Casual", "com.demo.mergemeadow"],
]
PARTNERS = [
    ["dsp_001", "Northstar Ads", "Mediation A"],
    ["dsp_002", "Orbit Exchange", "Mediation A"],
    ["dsp_003", "Pinecone Media", "Mediation B"],
    ["dsp_004", "Riverbid Network", "Mediation B"],
]
PARTNER_WEIGHTS = [0.34, 0.29, 0.22, 0.15]
PARTNER_YIELD = {"dsp_001": 1.12, "dsp_002": 1.00, "dsp_003": 0.91, "dsp_004": 0.84}
PARTNER_FILL = {"dsp_001": 0.86, "dsp_002": 0.82, "dsp_003": 0.78, "dsp_004": 0.74}
ACTIVE_DAY_PROB = {0: 1.00, 1: 0.27, 3: 0.18, 7: 0.13, 14: 0.09, 30: 0.06, 60: 0.035, 89: 0.02}


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def read_players(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["player_id"] = int(row["player_id"])
        row["install_date"] = date.fromisoformat(row["install_date"])
        row["campaign_id"] = int(row["campaign_id"]) if row["campaign_id"] else None
    return rows


def assign_experiment(players: list[dict], app_by_player: dict[int, str], rng: random.Random):
    """Randomise 1:1 within app/channel/platform strata for a balanced demo."""
    strata: dict[tuple, list[int]] = defaultdict(list)
    for player in players:
        key = (app_by_player[player["player_id"]], player["channel"], player["platform"])
        strata[key].append(player["player_id"])

    variants: dict[int, str] = {}
    for ids in strata.values():
        rng.shuffle(ids)
        for index, player_id in enumerate(ids):
            variants[player_id] = "control" if index % 2 == 0 else "treatment"
    return variants


def generate_extensions(output: Path, seed: int = 42) -> dict[str, int]:
    rng = random.Random(seed + 10_000)
    players = read_players(output / "players.csv")

    app_rows = APPS
    partner_rows = PARTNERS
    app_by_player: dict[int, str] = {}
    player_app_rows = []
    for player in players:
        app = rng.choices(APPS, weights=[0.40, 0.32, 0.28], k=1)[0]
        app_by_player[player["player_id"]] = app[0]
        player_app_rows.append([player["player_id"], app[0], "synthetic_assignment"])

    write_csv(output / "apps.csv", ["app_id", "app_name", "genre", "package_name"], app_rows)
    write_csv(output / "demand_partners.csv", ["demand_partner_id", "partner_name", "mediation_group"], partner_rows)
    write_csv(output / "player_app_mapping.csv", ["player_id", "app_id", "mapping_source"], player_app_rows)

    variants = assign_experiment(players, app_by_player, rng)
    assignment_rows = []
    exposure_rows = []
    exposed_players: set[int] = set()
    assignment_id_by_player = {}
    for assignment_id, player in enumerate(players, start=1):
        pid = player["player_id"]
        assigned_at = datetime.combine(player["install_date"], time(0, 5))
        variant = variants[pid]
        assignment_id_by_player[pid] = assignment_id
        assignment_rows.append([
            assignment_id, EXPERIMENT_ID, pid, variant, assigned_at,
            "player_id", "1:1_stratified", "synthetic_random_assignment",
        ])
        # Exposure logging is deliberately near-complete, not assumed to be universal.
        if rng.random() < 0.985:
            exposed_players.add(pid)
            exposure_rows.append([
                len(exposure_rows) + 1, EXPERIMENT_ID, pid, variant,
                datetime.combine(player["install_date"], time(0, 20)) + timedelta(minutes=rng.randrange(20)),
                app_by_player[pid],
            ])

    write_csv(
        output / "experiment_assignments.csv",
        ["assignment_id", "experiment_id", "player_id", "variant", "assigned_at", "randomization_unit", "allocation_design", "data_origin"],
        assignment_rows,
    )
    write_csv(
        output / "experiment_exposures.csv",
        ["exposure_id", "experiment_id", "player_id", "variant", "exposure_timestamp", "app_id"],
        exposure_rows,
    )

    # Generate active days and session events. Day 0 is guaranteed; later activity
    # follows a decaying synthetic curve, with a small treatment uplift only for
    # exposed treatment players. This is a demonstration mechanism, not evidence.
    sessions_by_player: dict[int, list[dict]] = defaultdict(list)
    session_rows = []
    session_id = 1
    for player in players:
        pid = player["player_id"]
        install_date = player["install_date"]
        max_age = max(0, (EVENT_END - install_date).days)
        app_id = app_by_player[pid]
        variant = variants[pid]
        for age_day, base_probability in ACTIVE_DAY_PROB.items():
            if age_day > max_age:
                continue
            probability = base_probability
            if age_day > 0 and variant == "treatment" and pid in exposed_players and age_day in (1, 3, 7, 14, 30):
                probability = min(0.95, probability + 0.018)
            active = age_day == 0 or rng.random() < probability
            if not active:
                continue
            number_of_sessions = 1 + int(rng.random() < (0.22 if age_day == 0 else 0.12))
            for _ in range(number_of_sessions):
                hour_low = 1 if age_day == 0 else 6
                hour = rng.randrange(hour_low, 23)
                minute = rng.randrange(60)
                start = datetime.combine(install_date + timedelta(days=age_day), time(hour, minute))
                duration = rng.randint(75, 1_200)
                end = start + timedelta(seconds=duration)
                session = {
                    "session_id": session_id,
                    "player_id": pid,
                    "app_id": app_id,
                    "session_start": start,
                    "session_end": end,
                    "session_duration_seconds": duration,
                    "session_day": age_day,
                }
                sessions_by_player[pid].append(session)
                session_rows.append([
                    session_id, pid, app_id, start, end, duration, age_day,
                ])
                session_id += 1

    write_csv(
        output / "player_sessions.csv",
        ["session_id", "player_id", "app_id", "session_start", "session_end", "session_duration_seconds", "session_day"],
        session_rows,
    )

    # One row per ad request. A filled request has an impression ID; a click ID
    # can only exist for a served impression. This supports clean funnel metrics.
    ad_rows = []
    request_id = 1
    impression_id = 1
    click_id = 1
    for player in players:
        pid = player["player_id"]
        variant = variants[pid]
        app_id = app_by_player[pid]
        for session in sessions_by_player[pid]:
            requests = []
            if rng.random() < 0.64:
                requests.append("rewarded_video")
            if rng.random() < 0.82:
                requests.append("interstitial")
                # Control has an uncapped second interstitial opportunity; the
                # treatment arm models a one-interstitial-per-session cap.
                if variant == "control" and rng.random() < 0.24:
                    requests.append("interstitial")
            for ad_format in requests:
                partner_id = rng.choices([p[0] for p in PARTNERS], weights=PARTNER_WEIGHTS, k=1)[0]
                fill_probability = PARTNER_FILL[partner_id] - (0.025 if ad_format == "interstitial" else 0.0)
                filled = rng.random() < fill_probability
                request_timestamp = session["session_start"] + timedelta(seconds=rng.randrange(15, max(30, session["session_duration_seconds"] - 10)))
                this_impression_id = f"imp_{impression_id}" if filled else ""
                this_click_id = ""
                revenue = 0.0
                if filled:
                    impression_id += 1
                    click_probability = 0.013 if ad_format == "rewarded_video" else 0.019
                    if rng.random() < click_probability:
                        this_click_id = f"clk_{click_id}"
                        click_id += 1
                    base_revenue = 0.018 if ad_format == "rewarded_video" else 0.007
                    revenue = round(base_revenue * PARTNER_YIELD[partner_id] * rng.uniform(0.72, 1.28), 5)
                ad_rows.append([
                    f"req_{request_id}", pid, app_id, partner_id, session["session_id"],
                    request_timestamp, ad_format, "filled" if filled else "no_fill",
                    this_impression_id, this_click_id, revenue, EXPERIMENT_ID, variant,
                ])
                request_id += 1

    write_csv(
        output / "ad_delivery_events.csv",
        ["request_id", "player_id", "app_id", "demand_partner_id", "session_id", "request_timestamp", "ad_format", "request_status", "impression_id", "click_id", "revenue_usd", "experiment_id", "experiment_variant"],
        ad_rows,
    )

    # Player-level intention-to-treat outcome table. Outcomes are derived from
    # generated sessions, ad delivery and IAP records over [assignment, +7 days).
    install_by_player = {player["player_id"]: player["install_date"] for player in players}
    # Use raw event timestamps to retain the exact 7-day observation window.
    iap_7d = defaultdict(float)
    with (output / "iap_transactions.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            pid = int(row["player_id"])
            event_ts = datetime.fromisoformat(row["transaction_timestamp"])
            installed = install_by_player[pid]
            if datetime.combine(installed, time.min) <= event_ts < datetime.combine(installed + timedelta(days=7), time.min):
                iap_7d[pid] += float(row["usd_amount"])

    ad_7d = defaultdict(float)
    with (output / "ad_delivery_events.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            pid = int(row["player_id"])
            event_ts = datetime.fromisoformat(row["request_timestamp"])
            installed = install_by_player[pid]
            if datetime.combine(installed, time.min) <= event_ts < datetime.combine(installed + timedelta(days=7), time.min):
                ad_7d[pid] += float(row["revenue_usd"])

    outcomes = []
    for player in players:
        pid = player["player_id"]
        player_sessions = sessions_by_player[pid]
        sessions_7d = sum(1 for row in player_sessions if 0 <= row["session_day"] < 7)
        retained_d7 = int(any(row["session_day"] == 7 for row in player_sessions))
        ad_revenue = round(ad_7d[pid], 5)
        iap_revenue = round(iap_7d[pid], 2)
        outcomes.append([
            EXPERIMENT_ID, pid, variants[pid], assignment_id_by_player[pid],
            int(pid in exposed_players), sessions_7d, retained_d7, ad_revenue,
            iap_revenue, round(ad_revenue + iap_revenue, 5), 1,
        ])
    write_csv(
        output / "experiment_player_outcomes.csv",
        ["experiment_id", "player_id", "assigned_variant", "assignment_id", "was_exposed", "sessions_first_7d", "retained_d7", "ad_revenue_first_7d_usd", "iap_revenue_first_7d_usd", "total_revenue_first_7d_usd", "d7_observation_complete"],
        outcomes,
    )

    counts = {
        "players": len(players),
        "player_app_mapping": len(player_app_rows),
        "experiment_assignments": len(assignment_rows),
        "experiment_exposures": len(exposure_rows),
        "player_sessions": len(session_rows),
        "ad_delivery_events": len(ad_rows),
        "experiment_player_outcomes": len(outcomes),
        "impressions": sum(1 for row in ad_rows if row[8]),
        "clicks": sum(1 for row in ad_rows if row[9]),
    }
    manifest = {
        "dataset_name": "mobile_game_extended_synthetic_demo",
        "data_origin": "synthetic_generated",
        "seed": seed,
        "observation_end_date": EVENT_END.isoformat(),
        "experiment_id": EXPERIMENT_ID,
        "experiment_design": "1:1 stratified synthetic control/treatment assignment",
        "treatment_definition": "at most one interstitial ad request per session",
        "interpretation_warning": "All added telemetry and experiment outcomes are simulated, not observed production data or real causal evidence.",
        "row_counts": counts,
    }
    (output / "demo_metadata.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "generated_extended",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    generate_base(args.output_dir, seed=args.seed)
    counts = generate_extensions(args.output_dir, seed=args.seed)
    print("Extended synthetic dataset generated:", args.output_dir.resolve())
    for name, count in counts.items():
        print(f"  {name}: {count:,}")
    print("All added tables are generated demonstration data, not observed production telemetry.")


if __name__ == "__main__":
    main()
