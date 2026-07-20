<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=2,8,14&height=200&section=header&text=UA%20Spend%20%26%20LTV%20Analytics&fontSize=38&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=CAC%20%7C%20LTV%20%7C%20ROAS%20%7C%20Payback%20Period%20by%20Channel&descAlignY=55&descSize=17" width="100%"/>

<img src="https://readme-typing-svg.demolab.com/svg?font=Fira+Code&weight=500&size=20&duration=3000&pause=800&color=00B4A6&center=true&vCenter=true&width=650&lines=The+cheapest+channel+isn't+the+best+one.;CPI+ranked+these+channels+backwards.;SQL+%2B+Python+%2B+Financial+Analysis" alt="Typing SVG" />

<br/>

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/pandas-2.x-150458?style=for-the-badge&logo=pandas&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-notebooks-F37626?style=for-the-badge&logo=jupyter&logoColor=white)
![Status](https://img.shields.io/badge/status-complete-success?style=for-the-badge)

</div>

A portfolio project simulating a UA (user acquisition) budget review for a
mobile game: 90 days of spend across four channels, cohort-based LTV
tracking, and a quantified budget reallocation recommendation — the kind
of financial/growth analysis a live-ops or marketing analytics team runs
every month.

**Built to demonstrate the financial half of mobile game analytics** —
CAC, LTV, ROAS, and payback period — that pairs with product-side work
like A/B testing and retention analysis (see the companion
[Bingo F2P Analytics](../bingo_analytics) project).

---

## 🔑 Headline finding

`paid_social` has the **lowest** cost-per-install of the three paid
channels — but the **worst** return. `cross_promo`, the smallest spend
line in the portfolio, is the only paid channel that actually pays back
within 90 days, at 130% ROAS.

<div align="center">

| Channel | Blended CAC | D90 LTV | D90 ROAS | Payback |
|:---:|:---:|:---:|:---:|:---:|
| 🟢 **cross_promo** | $0.45 | $0.59 | **130.3%** | Day 28 |
| ⚪ organic | $0.00 | $0.92 | — | Immediate |
| 🟡 paid_search | $3.16 | $0.97 | 30.8% | Not in 90d |
| 🔴 **paid_social** | $1.54 | $0.33 | 21.5% | Not in 90d |

</div>

> 💡 **CPI alone ranks these channels almost exactly backwards from what
> the LTV data supports.** paid_social absorbs the largest budget share
> while returning the least.

📄 Full stakeholder readout: [`docs/stakeholder_writeup.md`](docs/stakeholder_writeup.md)

<div align="center">
<img src="docs/ltv_vs_cac.png" width="80%" alt="Cumulative LTV vs CAC by channel"/>
</div>

---

## 📑 Table of contents

- [Project structure](#-project-structure)
- [Data model](#️-data-model)
- [What each notebook covers](#-what-each-notebook-covers)
- [Analysis workflow](#-analysis-workflow)
- [Running it locally](#-running-it-locally)
- [Stack](#️-stack)

---

## 📊 Project structure

```
ua_ltv_analytics/
├── generate_data.py              # synthetic UA spend + player + revenue generator
├── sql/
│   ├── schema.sql                # table definitions
│   └── analysis_queries.sql      # 20 business-focused MySQL queries
├── data/                         # generated CSVs (gitignored — run generator locally)
├── notebooks/
│   ├── 01_ua_spend_exploration.ipynb    # spend, blended vs. marginal CPI trend
│   └── 02_ltv_roas_payback.ipynb        # LTV curves, ROAS, payback, reallocation model
├── docs/
│   └── stakeholder_writeup.md    # one-page finance-facing readout
└── requirements.txt
```

## 🗂️ Data model

```mermaid
erDiagram
    ua_campaigns ||--o{ ua_spend : has
    ua_campaigns ||--o{ players : acquires
    players ||--o{ iap_transactions : makes
    players ||--o{ ad_revenue_events : generates

    ua_campaigns {
        int campaign_id PK
        string channel
        string campaign_name
        date start_date
        date end_date
    }
    ua_spend {
        bigint spend_id PK
        int campaign_id FK
        string channel
        date spend_date
        decimal daily_spend_usd
        int installs
    }
    players {
        int player_id PK
        date install_date
        string channel
        int campaign_id FK
        string country
        string platform
    }
    iap_transactions {
        bigint transaction_id PK
        int player_id FK
        datetime transaction_timestamp
        string product_type
        decimal usd_amount
    }
    ad_revenue_events {
        bigint event_id PK
        int player_id FK
        datetime event_timestamp
        string ad_type
        decimal revenue_usd
    }
```

---

## 🔄 Analysis workflow

```mermaid
flowchart LR
    A[generate_data.py] --> B[01 Spend Exploration]
    B -->|CAC by channel| C[02 LTV / ROAS / Payback]
    C --> D[Reallocation Model]
    D --> E[Stakeholder Writeup]

    style A fill:#00B4A6,color:#fff
    style B fill:#FF6B6B,color:#fff
    style C fill:#4ECDC4,color:#fff
    style D fill:#FFD93D,color:#000
    style E fill:#6C63FF,color:#fff
```

---

## 🔍 What each notebook covers

<details open>
<summary><b>📓 01 — UA Spend Exploration & CAC</b></summary>
<br/>

- Total spend, installs, and blended CAC by channel
- Daily CPI trend, 7-day rolling average
- **First-30-days vs. last-30-days CAC comparison** — catches `paid_social`'s
  marginal cost nearly doubling over the window, a fact the blended average
  hides completely.

</details>

<details>
<summary><b>📓 02 — LTV, ROAS & Payback Period</b> (the core deliverable)</summary>
<br/>

- Combines IAP + ad revenue into a single per-player LTV timeline
- Cumulative LTV curves vs. CAC, by channel, over a 90-day window
- Payback day calculation (first day cumulative LTV crosses CAC)
- D90 ROAS by channel
- A quantified budget reallocation model — dollars and installs, not just
  a verbal recommendation

</details>

---

## 🚀 Running it locally

```bash
pip install -r requirements.txt
python generate_data.py          # generates data/*.csv (~30 sec)
jupyter notebook notebooks/       # run 01 → 02, in order
```

---

## 🛠️ Stack

<div align="center">

![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/-pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/-NumPy-013243?style=flat-square&logo=numpy&logoColor=white)
![Matplotlib](https://img.shields.io/badge/-Matplotlib-11557C?style=flat-square)
![SQL](https://img.shields.io/badge/-SQL-4479A1?style=flat-square&logo=mysql&logoColor=white)
![Jupyter](https://img.shields.io/badge/-Jupyter-F37626?style=flat-square&logo=jupyter&logoColor=white)

</div>

Financial/growth methods: blended vs. marginal CAC, cohort-based LTV,
payback period, ROAS, quantified budget reallocation modeling.

<div align="center">
<br/>
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=2,8,14&height=100&section=footer" width="100%"/>
</div>
