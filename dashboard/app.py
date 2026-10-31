import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("UA_DATA_DIR", ROOT / "data")).resolve()

st.set_page_config(page_title="Mobile Game UA Efficiency", layout="wide")
st.title("Mobile Game UA Spend Efficiency")
st.caption("Synthetic portfolio dataset — descriptive metrics, not live media reporting.")


@st.cache_data
def load_data():
    spend_df = pd.read_csv(DATA / "ua_spend.csv", parse_dates=["spend_date"])
    players_df = pd.read_csv(DATA / "players.csv", parse_dates=["install_date"])
    return spend_df, players_df


spend, players = load_data()
channel = spend.groupby("channel", as_index=False).agg(
    spend_usd=("daily_spend_usd", "sum"),
    installs=("installs", "sum"),
)
channel["blended_cac"] = channel["spend_usd"] / channel["installs"].replace(0, pd.NA)
paid = channel[channel.channel != "organic"].sort_values("blended_cac")
a, b, c = st.columns(3)
a.metric("Lowest paid-channel CAC", f"${paid.iloc[0].blended_cac:.2f}", paid.iloc[0].channel)
b.metric("Total UA spend", f"${channel.spend_usd.sum():,.0f}")
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

st.info(
    "No ad request/impression logs, app IDs, demand partners, sessions or experiment "
    "assignment are supplied. CTR, fill rate, eCPM, retention, app/partner splits "
    "and A/B results are not estimable."
)
