# UA Budget Readout: Channel Efficiency Review

**Audience:** UA / Growth and Finance stakeholders  
**Window:** 90-day spend period and available monetisation observations  
**Channels:** paid_social, paid_search, cross_promo and organic  
**Data:** synthetic portfolio demonstration

## Executive summary

The lowest paid-channel blended CAC is **cross_promo at $0.45**, not paid_social. Paid_social blended CAC is **$1.54** and paid_search is **$3.16**. Cross_promo also has the strongest observed 90-day return, but its relatively small historical spend base makes aggressive scaling unproven.

| Channel | Blended CAC | D90 LTV | D90 ROAS | Payback |
|---|---:|---:|---:|---|
| cross_promo | **$0.45** | $0.59 | **130.3%** | Day 28 |
| organic | $0.00* | $0.92 | — | No paid spend |
| paid_search | $3.16 | $0.97 | 30.8% | Not within observed 90d |
| paid_social | $1.54 | $0.33 | 21.5% | Not within observed 90d |

*Organic CAC is zero because paid spend is not attributed to the channel, not because organic acquisition is cost-free.

## Marginal cost trend

Paid_social marginal CAC increased from **$1.174 in the first 30 days** to **$1.888 in the last 30 days**, a **60.8% increase**. The earlier statement that it nearly doubled was inaccurate. Each window uses total spend divided by total installs.

## Interpretation and budget risk

The ROAS-weighted scenario allocates approximately **$4,762** of incremental spend to cross_promo, although its entire historic spend was only **$976.95**. The proposed increment is about **4.9 times its total prior spend**.

Do not assume the historical $0.45 CAC or 130.3% D90 ROAS will persist at nearly five times the scale. Inventory supply, audience overlap, partner capacity and marginal pricing can cause saturation. The arithmetic is a sensitivity scenario, not a forecast. Any budget test should be staged and capped, with incremental CAC and D90 ROAS monitored at each step.

Paid_search has the highest D90 LTV among paid channels ($0.97), but D90 ROAS is only 30.8%. D120/D180 should be assessed only for install cohorts with a complete observation horizon; immature cohorts must not be treated as zero revenue or complete observations.

## What this source can and cannot answer

The player file supports country and platform cuts. Purchase and ad-revenue files support revenue by channel and ad type. The data has no session/activity records for retention, no experiment assignment/exposure for treatment effects or SRM, and no impression/request counters for CTR, fill rate or eCPM. App IDs and demand-partner fields are absent too. These metrics are therefore not estimable.

## Recommended action

1. Treat cross_promo as the most efficient observed paid channel, not an unlimited source of cheap installs.
2. Run a small, capped increment before considering larger budget changes.
3. Track marginal CAC, cohort maturity, player-level value and country/platform mix.
4. Extend paid_search observation only where full D120/D180 horizons are available.
5. Collect sessions, experiment assignment/exposure, ad requests/impressions, app IDs and demand-partner IDs before expanding the metric set.

---
Full methodology and analysis: [Mobile Game Efficiency & LTV Analysis.ipynb](../Mobile%20Game%20Efficiency%20%26%20LTV%20Analysis.ipynb).
