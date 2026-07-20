# UA Budget Readout: Channel Efficiency Review

**Prepared for:** UA / Growth & Finance stakeholders
**Window:** 90-day spend period, 90-day LTV observation per cohort
**Channels reviewed:** paid_social, paid_search, cross_promo, organic

---

## The question

Which acquisition channels are actually worth their spend once we look
past cost-per-install and into what those installs are worth?

## What we found

| Channel | Blended CAC | D90 LTV | D90 ROAS | Payback |
|---|---|---|---|---|
| **cross_promo** | $0.45 | $0.59 | **130.3%** | Day 28 |
| organic | $0.00 | $0.92 | — | Immediate |
| **paid_search** | $3.16 | $0.97 | 30.8% | Not within 90d |
| **paid_social** | $1.54 | $0.33 | 21.5% | Not within 90d |

**paid_social has the lowest cost per install of the three paid channels,
but the worst return.** It's currently the largest spend line in the
portfolio. Its marginal cost (most recent 30 days vs. first 30 days of the
window) is also rising — so the channel is getting more expensive and less
efficient at the same time.

**cross_promo is the standout performer** — best ROAS by a wide margin,
only paid channel that's crossed breakeven within the window — and it's
also the smallest spend line. It's currently under-invested relative to
its return.

## Why this matters

A CPI-only view of these channels would rank them: cross_promo (cheapest)
→ paid_social → paid_search (most expensive), and a growth team optimizing
purely for install volume per dollar would keep pushing paid_social. The
LTV view flips that ranking almost entirely.

## Recommendation

**Shift ~30% of paid_social's budget into cross_promo and paid_search**,
weighted toward cross_promo given its confirmed payback and higher ROAS.
Modeled impact of a $5,900 shift:

- cross_promo: +$4,760 → ~10,600 additional installs at 130% ROAS
- paid_search: +$1,130 → ~360 additional installs at 31% ROAS
- paid_social: −$5,900 → ~3,800 fewer installs at 22% ROAS

This trades total install volume for install *value* — fewer installs
overall, but a portfolio that returns more per dollar spent.

## Process recommendation

Track **marginal CAC** (recent-window cost, not all-time blended average)
alongside every CPI report, and pair CAC reviews with an LTV/ROAS check
before scaling any channel further. In this review, the CPI metric alone
would have pointed budget at the worst-performing channel.

---
*Full analysis, methodology, and code: see `notebooks/01_ua_spend_exploration.ipynb`
and `notebooks/02_ltv_roas_payback.ipynb`*
