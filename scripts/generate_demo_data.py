"""Generate a deterministic synthetic mobile-game UA dataset in a separate output folder.

By default this writes data/generated_demo/ and never overwrites the committed
source snapshot in data/. The generated dataset is a new synthetic scenario; it
does not reproduce the committed snapshot's headline LTV/revenue values.
"""
from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

START = date(2026, 1, 1)
DAYS = 90
EVENT_END = date(2026, 6, 28)
CHANNELS = {
    "paid_social": {"install_total": 12742, "blended_cac": 1.54, "campaign_ids": [1, 2, 3]},
    "paid_search": {"install_total": 4932, "blended_cac": 3.16, "campaign_ids": [4, 5, 6]},
    "cross_promo": {"install_total": 2171, "blended_cac": 0.45, "campaign_ids": [7, 8, 9]},
    "organic": {"install_total": 6400, "blended_cac": 0.0, "campaign_ids": [10]},
}
COUNTRIES = ["US", "GB", "IN", "DE", "CA", "AU", "BR", "MX"]
PLATFORMS = ["Android", "iOS"]
PRODUCTS = [("starter_bundle", 0.99), ("remove_ads", 3.99), ("coin_pack", 9.99), ("vip_pass", 14.99)]


def distribute(total: int, parts: int) -> list[int]:
    base, remainder = divmod(total, parts)
    return [base + (index < remainder) for index in range(parts)]


def write_csv(path: Path, header: list[str], rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)


def generate(output: Path, seed: int = 42) -> None:
    rng = random.Random(seed)
    output.mkdir(parents=True, exist_ok=True)

    campaign_rows = []
    campaign_map = {}
    for channel, spec in CHANNELS.items():
        for idx, campaign_id in enumerate(spec["campaign_ids"], start=1):
            campaign_name = f"{channel}_campaign_{idx}"
            campaign_map[campaign_id] = (channel, campaign_name)
            campaign_rows.append([campaign_id, channel, campaign_name, START, START + timedelta(days=DAYS)])
    write_csv(output / "ua_campaigns.csv",
              ["campaign_id", "channel", "campaign_name", "start_date", "end_date"],
              campaign_rows)

    spend_rows = []
    player_rows = []
    players_by_id = {}
    player_id = 1
    spend_id = 1
    for channel, spec in CHANNELS.items():
        daily_totals = distribute(spec["install_total"], DAYS)
        for day_index, day_installs in enumerate(daily_totals):
            spend_date = START + timedelta(days=day_index)
            campaign_allocations = distribute(day_installs, len(spec["campaign_ids"]))
            for campaign_id, installs in zip(spec["campaign_ids"], campaign_allocations):
                # The committed snapshot uses the same blended paid CAC references for this demonstration.
                daily_spend = round(installs * spec["blended_cac"], 2)
                spend_rows.append([spend_id, campaign_id, channel, spend_date, daily_spend, installs])
                spend_id += 1
                for _ in range(installs):
                    country = rng.choice(COUNTRIES)
                    platform = rng.choice(PLATFORMS)
                    player_rows.append([player_id, spend_date, channel, campaign_id, country, platform])
                    players_by_id[player_id] = spend_date
                    player_id += 1
    write_csv(output / "ua_spend.csv",
              ["spend_id", "campaign_id", "channel", "spend_date", "daily_spend_usd", "installs"],
              spend_rows)
    write_csv(output / "players.csv",
              ["player_id", "install_date", "channel", "campaign_id", "country", "platform"],
              player_rows)
    write_csv(output / "sample_players.csv",
              ["player_id", "install_date", "channel", "campaign_id", "country", "platform"],
              player_rows[:20])

    iap_rows = []
    for transaction_id in range(1, 1652):
        pid = rng.choice(list(players_by_id))
        install_date = players_by_id[pid]
        event_date = install_date + timedelta(days=rng.randint(0, min(89, (EVENT_END - install_date).days)))
        product_type, amount = rng.choice(PRODUCTS)
        iap_rows.append([transaction_id, pid, datetime.combine(event_date, datetime.min.time()) + timedelta(hours=rng.randrange(24)), product_type, amount])
    write_csv(output / "iap_transactions.csv",
              ["transaction_id", "player_id", "transaction_timestamp", "product_type", "usd_amount"],
              iap_rows)

    ad_rows = []
    for event_id in range(1, 107945):
        pid = rng.choice(list(players_by_id))
        install_date = players_by_id[pid]
        max_age = max(0, (EVENT_END - install_date).days)
        event_date = install_date + timedelta(days=rng.randint(0, max_age))
        event_ts = datetime.combine(event_date, datetime.min.time()) + timedelta(hours=rng.randrange(24))
        ad_type = rng.choices(["rewarded_video", "interstitial"], weights=[0.6, 0.4], k=1)[0]
        revenue_usd = round(rng.choices([0.006, 0.01, 0.014, 0.02, 0.028], weights=[1, 3, 3, 2, 1], k=1)[0], 4)
        ad_rows.append([event_id, pid, event_ts, ad_type, revenue_usd])
    write_csv(output / "ad_revenue_events.csv",
              ["event_id", "player_id", "event_timestamp", "ad_type", "revenue_usd"],
              ad_rows)

    print(f"Generated files in {output.resolve()}")
    print(f"Players: {len(player_rows):,}; spend rows: {len(spend_rows):,}; IAP transactions: {len(iap_rows):,}; ad events: {len(ad_rows):,}")
    print("This is an alternative deterministic synthetic sample, not a byte-for-byte recreation of the committed analysis snapshot.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "generated_demo")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate(args.output_dir, seed=args.seed)
