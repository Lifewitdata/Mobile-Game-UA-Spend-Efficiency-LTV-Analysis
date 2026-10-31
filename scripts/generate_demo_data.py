"""Write deterministic QA-only fixture CSVs without replacing the project baseline."""
from pathlib import Path
import csv
import random
from datetime import date, timedelta

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "generated_demo"
OUTPUT.mkdir(parents=True, exist_ok=True)
rng = random.Random(42)
start = date(2026, 1, 1)
channels = [("paid_social", 1.54), ("paid_search", 3.16), ("cross_promo", 0.45)]
countries = ["US", "GB", "IN", "DE", "CA", "AU", "BR", "MX"]
platforms = ["Android", "iOS"]

with (OUTPUT / "players_demo.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["player_id", "install_date", "channel", "country", "platform"])
    player_id = 1
    for day in range(30):
        for channel, _ in channels:
            for _ in range(25):
                writer.writerow([
                    player_id, start + timedelta(days=day), channel,
                    rng.choice(countries), rng.choice(platforms)
                ])
                player_id += 1

with (OUTPUT / "spend_demo.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["date", "channel", "spend_usd", "installs"])
    for day in range(30):
        for channel, cac in channels:
            installs = 25
            writer.writerow([start + timedelta(days=day), channel, round(installs * cac, 2), installs])

print(f"Wrote deterministic QA fixtures to {OUTPUT}")
print("These fixtures are not replacements for the committed full source datasets.")
