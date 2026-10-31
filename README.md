# Mobile Game UA Spend Efficiency & LTV Analysis

A reproducible portfolio analysis of synthetic mobile-game user-acquisition spend, player cohorts and monetisation, using the committed CSV snapshot.

## Headline findings

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
├── data/                         # committed source CSVs
├── dashboard/app.py              # Streamlit dashboard
├── docs/
│   ├── data_dictionary.md
│   ├── sql_run_guide.md
│   ├── stakeholder_writeup.md
│   └── *.png                     # analysis outputs
├── sql/
│   ├── schema.sql
│   └── analysis_queries.sql
├── scripts/generate_demo_data.py # deterministic QA fixtures; not a baseline overwrite
├── tests/test_metrics.py
├── requirements.txt
├── LICENSE
└── .github/workflows/validate.yml
```

`data/sample_players.csv` is a 20-row sample fixture for inspection and lightweight examples. The full notebook reads only `data/players.csv`.

## Run the notebook

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

Open `Mobile Game Efficiency & LTV Analysis.ipynb` at the repository root and run all cells top to bottom. Inputs default to `data/`; figures are saved under `docs/`.

To generate a separate deterministic synthetic dataset without overwriting the committed snapshot:

```bash
python scripts/generate_demo_data.py
```

The script writes all five analysis CSVs plus a 20-row sample to `data/generated_demo/`. Use that alternative dataset by setting `UA_DATA_DIR=data/generated_demo` before starting Jupyter or Streamlit. The generated sample is a new synthetic scenario, not an exact recreation of the committed snapshot or its headline LTV/revenue results.

## Dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard shows channel CAC, spend/install trends and country/platform mix. It reads the existing committed dataset; a hosted deployment is not configured.

## SQL

The query library targets **MySQL 8.0+**. Follow [docs/sql_run_guide.md](docs/sql_run_guide.md) to create the database, run the schema, import CSV files and verify counts and headline CAC outputs. Queries include CTEs, `RANK`, `LAG`, running totals and rolling averages.

## Metric and source limitations

See [docs/data_dictionary.md](docs/data_dictionary.md) for table grain, metric definitions and quality rules. The data provides spend, installs, country, platform, purchase transactions and ad-revenue events by ad type. It has no ad impressions/requests, app IDs, demand-partner IDs, sessions/activity, experiment assignment or exposure. Thus CTR, CVR, CPC, fill rate, eCPM, retention, app/partner splits and causal A/B statistics cannot be calculated; they are not fabricated.

D120/D180 LTV is calculated only for cohorts with complete observation windows. The notebook will report when no cohort is eligible.

## Validate

```bash
pytest -q
```

GitHub Actions runs the tests and validates notebook JSON on pushes and pull requests.

## License

MIT. See [LICENSE](LICENSE).
