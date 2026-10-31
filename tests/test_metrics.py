from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def test_required_inputs_exist():
    for name in [
        "ua_campaigns.csv",
        "ua_spend.csv",
        "players.csv",
        "iap_transactions.csv",
        "ad_revenue_events.csv",
    ]:
        assert (DATA / name).is_file()


def test_acquisition_ids_and_nonnegative_measures():
    players = pd.read_csv(DATA / "players.csv")
    spend = pd.read_csv(DATA / "ua_spend.csv")
    assert players.player_id.is_unique
    assert spend.spend_id.is_unique
    assert (spend.daily_spend_usd >= 0).all()
    assert (spend.installs > 0).all()
    assert players[["country", "platform", "channel"]].notna().all().all()


def test_blended_cac_reproduces_headline():
    spend = pd.read_csv(DATA / "ua_spend.csv")
    summary = spend.groupby("channel").agg(
        spend=("daily_spend_usd", "sum"),
        installs=("installs", "sum"),
    )
    summary["cac"] = summary.spend / summary.installs
    assert np.isclose(summary.loc["cross_promo", "cac"], 0.45, atol=0.01)
    assert np.isclose(summary.loc["paid_social", "cac"], 1.54, atol=0.01)
    assert np.isclose(summary.loc["paid_search", "cac"], 3.16, atol=0.01)


def test_iap_references_valid_players():
    players = pd.read_csv(DATA / "players.csv")
    iap = pd.read_csv(DATA / "iap_transactions.csv")
    assert iap.transaction_id.is_unique
    assert iap.player_id.isin(players.player_id).all()
    assert (iap.usd_amount >= 0).all()
