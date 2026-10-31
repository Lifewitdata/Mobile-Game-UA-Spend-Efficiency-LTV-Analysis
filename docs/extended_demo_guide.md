# Extended synthetic monetisation, retention and experiment lab

This is a second, explicitly synthetic scenario generated alongside (not merged into) the committed source snapshot. It demonstrates event modelling, ad-funnel metrics, retention analysis and experiment measurement where the original source tables do not contain those fields.

## Generate the dataset

```bash
python scripts/generate_extended_demo_data.py
```

The command writes the original five baseline CSVs plus the extension tables into `data/generated_extended/`. It does not overwrite committed files in `data/`. The generator is deterministic for a given seed:

```bash
python scripts/generate_extended_demo_data.py --output-dir data/generated_extended --seed 42
```

The output includes `demo_metadata.json` with the seed, simulation scope, row counts and explicit synthetic origin.

## Run the extended dashboard

Windows PowerShell:
```powershell
$env:UA_DATA_DIR = "data/generated_extended"
streamlit run dashboard/app.py
```

macOS / Linux:
```bash
UA_DATA_DIR=data/generated_extended streamlit run dashboard/app.py
```

## Added tables

| File | Grain / key | Purpose |
|---|---|---|
| `apps.csv` | App / `app_id` | Synthetic app catalogue and genre. |
| `demand_partners.csv` | Partner / `demand_partner_id` | Synthetic demand-partner catalogue. |
| `player_app_mapping.csv` | Player / `player_id` | Separate one-to-one synthetic app mapping; baseline players remain unchanged. |
| `player_sessions.csv` | Session / `session_id` | Session start/end, duration and player-age day. |
| `ad_delivery_events.csv` | Ad request / `request_id` | One row per request, with fill status and nullable impression/click IDs. |
| `experiment_assignments.csv` | Player-experiment / `assignment_id` | 1:1 stratified control/treatment allocation. |
| `experiment_exposures.csv` | Exposure / `exposure_id` | Logged exposure; a small non-exposed share illustrates delivery non-compliance. |
| `experiment_player_outcomes.csv` | Player-experiment / `experiment_id + player_id` | First-seven-day player-level outcomes. |

## Metric definitions

- **Fill rate** = filled ad requests / all ad requests. A filled request has a non-empty `impression_id`.
- **CTR** = clicks / impressions. A click is represented by a non-empty `click_id` and can only exist on a served impression.
- **eCPM** = ad revenue / impressions × 1,000. Revenue is stored once on the ad-request row and is zero for no-fill requests.
- **D1 / D7 / D30 retention** = distinct installed players with at least one session on exactly player-age day 1 / 7 / 30, divided by eligible installs with a complete observation window.
- **Experiment ITT** = compare outcomes by the randomly assigned `variant`, regardless of whether an exposure row exists. The exposure log is a delivery diagnostic; do not use exposed-only players as the primary experiment denominator.

The synthetic `interstitial_frequency_cap_v1` experiment assigns players 1:1 within app/channel/platform strata. Treatment models at most one interstitial request per session; control may receive a second request opportunity. The generator also adds a small predefined treatment uplift to selected synthetic active-day probabilities among exposed treatment players. This is a known simulation mechanism, not evidence about a live game.

## Safeguards

1. Do not combine `ad_revenue_events.csv` with `ad_delivery_events.csv` as though they are the same event source. They are separate generated event models; unioning them into one ad ledger would double-count or misrepresent revenue.
2. Do not merge the app assignment into baseline `players.csv` in place. Join through `player_app_mapping.csv`.
3. Treat all app IDs, partner IDs, requests, impressions, clicks, sessions, assignments, exposures and experiment outcomes as generated demonstration data.
4. The generated treatment/control difference is a property of the simulator. Do not report it as a real-world causal finding.

## SQL

Run `sql/schema.sql` first, then `sql/extended_demo_schema.sql`. The additional MySQL 8.0+ analysis examples are in `sql/extended_demo_queries.sql`.
