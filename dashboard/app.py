import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("UA_DATA_DIR", ROOT / "data")).resolve()

st.set_page_config(page_title="Mobile Game UA Efficiency", layout="wide")
st.title("Mobile Game UA Spend Efficiency")
st.caption("Portfolio analytics built from clearly labelled synthetic data; not live media reporting.")


@st.cache_data
def load_base_data(data_dir: str):
    source = Path(data_dir)
    spend_df = pd.read_csv(source / "ua_spend.csv", parse_dates=["spend_date"])
    players_df = pd.read_csv(source / "players.csv", parse_dates=["install_date"])
    return spend_df, players_df


spend, players = load_base_data(str(DATA))
channel = spend.groupby("channel", as_index=False).agg(
    spend_usd=("daily_spend_usd", "sum"),
    installs=("installs", "sum"),
)
channel["blended_cac"] = channel["spend_usd"] / channel["installs"].replace(0, pd.NA)
paid = channel[channel.channel != "organic"].sort_values("blended_cac")

a, b, c = st.columns(3)
a.metric("Lowest paid-channel CAC", f"\${paid.iloc[0].blended_cac:.2f}", paid.iloc[0].channel)
b.metric("Total UA spend", f"\${channel.spend_usd.sum():,.0f}")
c.metric("Attributed installs", f"{channel.installs.sum():,}")

st.subheader("Blended CAC by channel")
st.altair_chart(
    alt.Chart(channel).mark_bar().encode(
        x=alt.X("channel:N", sort="-y", title="Channel"),
        y=alt.Y("blended_cac:Q", title="Blended CAC (USD)"),
        tooltip=["channel", "spend_usd", "installs", alt.Tooltip("blended_cac:Q", format=".2f")],
    ),
    use_container_width=True,
)

st.subheader("Daily spend and installs")
daily = spend.groupby(["spend_date", "channel"], as_index=False).agg(
    spend_usd=("daily_spend_usd", "sum"),
    installs=("installs", "sum"),
)
metric = st.selectbox("Trend metric", ["spend_usd", "installs"])
st.altair_chart(
    alt.Chart(daily).mark_line().encode(
        x="spend_date:T",
        y=alt.Y(f"{metric}:Q"),
        color="channel:N",
        tooltip=["spend_date:T", "channel:N", f"{metric}:Q"],
    ),
    use_container_width=True,
)

st.subheader("Country and platform mix")
mix = players.groupby(["country", "platform", "channel"], as_index=False).agg(
    players=("player_id", "nunique")
)
st.dataframe(mix.sort_values("players", ascending=False), use_container_width=True)
st.dataframe(channel.sort_values("blended_cac"), use_container_width=True)

EXTENDED_FILES = {
    "apps.csv", "demand_partners.csv", "player_app_mapping.csv", "player_sessions.csv",
    "ad_delivery_events.csv", "experiment_assignments.csv", "experiment_exposures.csv",
    "experiment_player_outcomes.csv",
}
if EXTENDED_FILES.issubset({path.name for path in DATA.glob("*.csv")}):
    st.divider()
    st.header("Synthetic Monetisation, Retention & Experiment Lab")
    st.caption("Everything in this additional section is generated demonstration data.")

    apps = pd.read_csv(DATA / "apps.csv")
    partners = pd.read_csv(DATA / "demand_partners.csv")
    sessions = pd.read_csv(DATA / "player_sessions.csv", parse_dates=["session_start", "session_end"])
    ads = pd.read_csv(DATA / "ad_delivery_events.csv", parse_dates=["request_timestamp"])
    outcomes = pd.read_csv(DATA / "experiment_player_outcomes.csv")

    ads["is_impression"] = ads["impression_id"].fillna("").astype(str).ne("")
    ads["is_click"] = ads["click_id"].fillna("").astype(str).ne("")
    request_count = len(ads)
    impression_count = int(ads["is_impression"].sum())
    click_count = int(ads["is_click"].sum())
    ad_revenue = ads["revenue_usd"].sum()
    fill_rate = impression_count / request_count if request_count else 0
    ctr = click_count / impression_count if impression_count else 0
    ecpm = ad_revenue / impression_count * 1000 if impression_count else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ad requests", f"{request_count:,}")
    k2.metric("Fill rate", f"{fill_rate:.1%}")
    k3.metric("CTR", f"{ctr:.2%}")
    k4.metric("eCPM", f"\${ecpm:.2f}")

    st.subheader("Ad delivery by app and demand partner")
    summary = ads.groupby(["app_id", "demand_partner_id"], as_index=False).agg(
        requests=("request_id", "count"),
        impressions=("is_impression", "sum"),
        clicks=("is_click", "sum"),
        revenue_usd=("revenue_usd", "sum"),
    )
    summary["fill_rate"] = summary["impressions"] / summary["requests"].replace(0, pd.NA)
    summary["ctr"] = summary["clicks"] / summary["impressions"].replace(0, pd.NA)
    summary["ecpm_usd"] = summary["revenue_usd"] / summary["impressions"].replace(0, pd.NA) * 1000
    summary = summary.merge(apps[["app_id", "app_name"]], on="app_id", how="left").merge(
        partners[["demand_partner_id", "partner_name"]], on="demand_partner_id", how="left"
    )
    st.dataframe(
        summary[["app_name", "partner_name", "requests", "impressions", "clicks", "fill_rate", "ctr", "ecpm_usd", "revenue_usd"]].sort_values("revenue_usd", ascending=False),
        use_container_width=True,
    )

    st.subheader("Player retention by install cohort")
    retention_day = st.selectbox("Retention day", [1, 7, 30], index=1)
    max_observed_date = sessions["session_start"].dt.normalize().max()
    cohort_players = players.copy()
    cohort_players["install_week"] = cohort_players["install_date"].dt.to_period("W").dt.start_time
    cohort_players = cohort_players[
        cohort_players["install_date"] + pd.to_timedelta(retention_day, unit="D") <= max_observed_date
    ]
    eligible_player_ids = set(cohort_players["player_id"])
    active = sessions.loc[
        (sessions["session_day"] == retention_day) & sessions["player_id"].isin(eligible_player_ids),
        ["player_id"],
    ].drop_duplicates().merge(
        players[["player_id", "install_date"]], on="player_id", how="inner"
    )
    active["install_week"] = active["install_date"].dt.to_period("W").dt.start_time
    retention = cohort_players.groupby("install_week", as_index=False).agg(installs=("player_id", "nunique"))
    active_counts = active.groupby("install_week", as_index=False).agg(active_players=("player_id", "nunique"))
    retention = retention.merge(active_counts, on="install_week", how="left").fillna({"active_players": 0})
    retention["retention_pct"] = retention["active_players"] / retention["installs"].replace(0, pd.NA) * 100
    st.altair_chart(
        alt.Chart(retention).mark_line(point=True).encode(
            x=alt.X("install_week:T", title="Install cohort week"),
            y=alt.Y("retention_pct:Q", title=f"D{retention_day} retention (%)"),
            tooltip=["install_week:T", "installs:Q", "active_players:Q", alt.Tooltip("retention_pct:Q", format=".2f")],
        ),
        use_container_width=True,
    )

    st.subheader("Experiment: interstitial frequency cap")
    experiment = outcomes.groupby("assigned_variant", as_index=False).agg(
        assigned_players=("player_id", "nunique"),
        d7_retention=("retained_d7", "mean"),
        avg_sessions_first_7d=("sessions_first_7d", "mean"),
        avg_revenue_first_7d=("total_revenue_first_7d_usd", "mean"),
        exposure_rate=("was_exposed", "mean"),
    )
    experiment["d7_retention_pct"] = experiment["d7_retention"] * 100
    experiment["exposure_rate_pct"] = experiment["exposure_rate"] * 100
    st.dataframe(
        experiment[["assigned_variant", "assigned_players", "d7_retention_pct", "avg_sessions_first_7d", "avg_revenue_first_7d", "exposure_rate_pct"]],
        use_container_width=True,
    )
    if {"control", "treatment"}.issubset(set(experiment["assigned_variant"])):
        arms = experiment.set_index("assigned_variant")
        d7_delta = (arms.loc["treatment", "d7_retention"] - arms.loc["control", "d7_retention"]) * 100
        revenue_delta = arms.loc["treatment", "avg_revenue_first_7d"] - arms.loc["control", "avg_revenue_first_7d"]
        m1, m2 = st.columns(2)
        m1.metric("D7 retention difference (treatment − control)", f"{d7_delta:+.2f} pp")
        m2.metric("7-day revenue / assigned player difference", f"\${revenue_delta:+.4f}")
    st.info(
        "Use assigned variant for the primary intention-to-treat comparison; exposure rate is a delivery diagnostic. "
        "Assignments and treatment response are simulated. Differences shown here are not evidence of a live-game causal effect."
    )
else:
    st.info(
        "The committed baseline does not include ad request/impression logs, app IDs, partners, sessions or experiment assignment. "
        "To enable the extended synthetic lab, run scripts/generate_extended_demo_data.py and launch with UA_DATA_DIR=data/generated_extended."
    )
