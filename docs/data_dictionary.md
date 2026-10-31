# Data dictionary and metric definitions

All monetary values are USD. Both the baseline source snapshot and optional extended lab are synthetic portfolio data, not production telemetry.

## Baseline tables

| File | Grain / primary key | Main fields | Notes |
|---|---|---|---|
| ua_campaigns.csv | campaign / campaign_id | channel, name, start_date, end_date | Acquisition campaign metadata. |
| ua_spend.csv | campaign-day / spend_id | campaign_id, channel, date, spend, installs | Daily paid spend and attributed installs. |
| players.csv | player / player_id | install_date, channel, campaign_id, country, platform | One acquired player per row. |
| iap_transactions.csv | purchase / transaction_id | player_id, timestamp, product_type, usd_amount | In-app purchase revenue. |
| ad_revenue_events.csv | monetisation event / event_id | player_id, timestamp, ad_type, revenue_usd | Revenue event; not an impression log. |

## Baseline metric definitions

| Metric | Formula / definition | Availability |
|---|---|---|
| Blended CAC | Channel spend / channel installs | Available |
| Marginal CAC | Spend in selected window / installs in the same window | Available as a descriptive proxy, not a causal cost curve |
| LTV D90 | IAP + ad revenue from player age day 0–90 / eligible installs | Available for fully observed cohorts |
| ROAS D90 | D90 LTV / blended CAC × 100% | Available; excludes operating costs |
| Payback day | First age day cumulative LTV >= CAC | Available within observed horizon |
| CTR | Clicks / impressions | Not available in baseline |
| CPC | Spend / clicks | Not available in baseline |
| eCPM | Ad revenue / served impressions × 1,000 | Not available in baseline |
| Fill rate | Served impressions / ad requests | Not available in baseline |
| Retention | Active users on day N / cohort installs | Not available in baseline |

## Extended synthetic tables

Generated only by `scripts/generate_extended_demo_data.py` under `data/generated_extended/`. `demo_metadata.json` records the seed, observation end date, row counts and `synthetic_generated` origin.

| File | Grain / primary key | Purpose |
|---|---|---|
| apps.csv | App / app_id | Generated app catalogue. |
| demand_partners.csv | Partner / demand_partner_id | Generated demand-partner catalogue. |
| player_app_mapping.csv | Player / player_id | Separate one-to-one app mapping; baseline players.csv is unchanged. |
| player_sessions.csv | Session / session_id | Synthetic activity events with player-age day. |
| ad_delivery_events.csv | Ad request / request_id | One row per request; status, nullable impression/click IDs, app, partner, format and revenue. |
| experiment_assignments.csv | Player-experiment / assignment_id | Stratified random 1:1 assignment. |
| experiment_exposures.csv | Exposure / exposure_id | Logged exposure; simulated non-compliance is present. |
| experiment_player_outcomes.csv | Player-experiment / experiment_id + player_id | First-seven-day sessions, D7, ad/IAP/total revenue and exposure flag. |

## Extended metric definitions

- **Fill rate** = requests with an impression ID / all requests.
- **CTR** = requests with a click ID / requests with an impression ID.
- **eCPM** = sum of ad request-row revenue / impressions × 1,000.
- **D1/D7/D30 retention** = distinct players active on exactly age day 1/7/30 / eligible cohort installs with a complete observation window.
- **Experiment ITT** = compare outcomes by randomised assigned variant across every assigned player, including players with no exposure log. Exposure rate is a separate delivery diagnostic.

The `interstitial_frequency_cap_v1` simulation assigns players 1:1 within app/channel/platform strata. Treatment models at most one interstitial request per session; control can receive a second request opportunity. The generator adds a small predefined uplift to selected activity probabilities among exposed treatment players. Arm differences are a property of the simulation, not a real product effect or causal evidence.

## Quality and scope safeguards

Extension tests check unique IDs, assignment balance, player references, request-to-impression-to-click hierarchy and zero revenue for no-fill requests. Do not combine `ad_revenue_events.csv` and `ad_delivery_events.csv` into one ad ledger; they are separate generated event models. App mapping remains separate; do not overwrite baseline `players.csv`. Baseline CTR, eCPM, fill rate, retention and actual A/B results remain unavailable because the original source lacks the required data.
