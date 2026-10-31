# Mobile Game UA Spend Efficiency & LTV Analysis

A reproducible portfolio analysis of synthetic mobile-game user-acquisition spend, player cohorts and monetisation. The repository contains the original baseline source snapshot and an optional extended event-level lab for ad delivery, retention and experiment measurement.

## Baseline findings

| Channel | Blended CAC | D90 LTV | D90 ROAS | Payback |
|---|---:|---:|---:|---|
| cross_promo | **$0.45** | $0.59 | **130.3%** | Day 28 |
| organic | $0.00* | $0.92 | — | No paid spend |
| paid_search | $3.16 | $0.97 | 30.8% | Not within observed 90d |
| paid_social | $1.54 | $0.33 | 21.5% | Not within observed 90d |

**cross_promo has the lowest paid-channel blended CAC at $0.45; paid_social is $1.54.** Paid_social marginal CAC increased **60.8%**, from **$1.174** in the first 30 days to **$1.888** in the last 30 days.

*Organic CAC is zero only because paid acquisition spend is not assigned to organic; this does not mean organic acquisition has no operational cost.*

## Saturation warning

The weighted reallocation scenario proposes an additional ~$4,762 into cross_promo, whose full historical spend was $976.95. The increase is about **4.9× its total historical spend**. Do not assume the same $0.45 CAC or 130.3% ROAS at that scale. Treat the allocation as a sensitivity scenario only; any live shift should be staged, capped and evaluated using incremental CAC and ROAS.

## Repository structure

```
.
├── Mobile Game Efficiency & LTV Analysis.ipynb
├── data/                         # committed baseline source CSVs
├── dashboard/app.py              # baseline + optional extended Streamlit lab
├── docs/
│   ├── data_dictionary.md
│   ├── extended_demo_guide.md
│   ├── sql_run_guide.md
│   └── stakeholder_writeup.md
├── sql/
│   ├── schema.sql
│   ├── analysis_queries.sql
│   ├── extended_demo_schema.sql
│   └── extended_demo_queries.sql
├── scripts/
│   ├── generate_demo_data.py
│   └── generate_extended_demo_data.py
├── tests/
├── requirements.txt
├── LICENSE
└── .github/workflows/validate.yml
```

## Run the baseline notebook

Python 3.11 recommended.

```bash
git clone https://github.com/Lifewitdata/Mobile-Game-UA-Spend-Efficiency-LTV-Analysis.git
cd Mobile-Game-UA-Spend-Efficiency-LTV-Analysis
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter lab
```

Open `Mobile Game Efficiency & LTV Analysis.ipynb` at the repository root and run all cells. The committed inputs default to `data/`; figures are saved under `docs/`.

## Extended synthetic monetisation, retention and experiment lab

The original source does not contain ad requests/impressions/clicks, app IDs, demand partners, sessions, or experiment assignment/exposure. These are not inferred from revenue events. Instead, the repository includes a separate synthetic generator:

```bash
python scripts/generate_extended_demo_data.py
```

It writes baseline-format CSVs plus `apps.csv`, `demand_partners.csv`, `player_app_mapping.csv`, `player_sessions.csv`, `ad_delivery_events.csv`, `experiment_assignments.csv`, `experiment_exposures.csv`, `experiment_player_outcomes.csv` and `demo_metadata.json` to `data/generated_extended/`. It never overwrites committed data. The manifest records the deterministic seed, row counts and synthetic origin.

Launch the dashboard with the extended data:

**Windows PowerShell**
```powershell
$env:UA_DATA_DIR = "data/generated_extended"
streamlit run dashboard/app.py
```

**macOS / Linux**
```bash
UA_DATA_DIR=data/generated_extended streamlit run dashboard/app.py
```

The dashboard then adds ad requests, fill rate, CTR, eCPM, app/partner cuts, cohort D1/D7/D30 retention and experiment assignment summaries. The full definitions and safeguards are in [docs/extended_demo_guide.md](docs/extended_demo_guide.md).

**Important:** every additional app ID, partner ID, ad-delivery event, session, assignment, exposure and experiment outcome is generated demonstration data. The frequency-cap scenario intentionally simulates a treatment mechanism. Its outputs are not production evidence and must not be represented as real causal findings. Do not combine `ad_revenue_events.csv` and `ad_delivery_events.csv` into one ad ledger.

## SQL

Baseline SQL targets **MySQL 8.0+**. Follow [docs/sql_run_guide.md](docs/sql_run_guide.md) for the original schema and queries. To analyse extended tables, run `sql/extended_demo_schema.sql` after `sql/schema.sql`, then use `sql/extended_demo_queries.sql`.

## Validate

```bash
pytest -q
```

GitHub Actions runs tests, smoke-tests the synthetic generator, validates notebook JSON, and runs the baseline SQL and notebook checks.

## License

MIT. See [LICENSE](LICENSE).
