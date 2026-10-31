# Data dictionary and metric definitions

All monetary values are USD. Source data is synthetic.

## File dictionary

| File | Grain / primary key | Main fields | Notes |
|---|---|---|---|
| ua_campaigns.csv | campaign / campaign_id | channel, name, start_date, end_date | Acquisition campaign metadata. |
| ua_spend.csv | campaign-day / spend_id | campaign_id, channel, date, spend, installs | Daily paid spend and attributed installs. |
| players.csv | player / player_id | install_date, channel, campaign_id, country, platform | One acquired player per row. |
| iap_transactions.csv | purchase / transaction_id | player_id, timestamp, product_type, usd_amount | In-app purchase revenue. |
| ad_revenue_events.csv | monetisation event / event_id | player_id, timestamp, ad_type, revenue_usd | Revenue event; not an impression log. |

## Metric definitions

| Metric | Formula / definition | Notes |
|---|---|---|
| Blended CAC | Channel spend / channel installs | Weighted historical average over the selected period. |
| Marginal CAC | Spend in a selected recent window / installs in that same window | Window-specific proxy, not a causal marginal cost curve. |
| LTV D90 | IAP + ad revenue from player age day 0–90 / eligible installs | Requires a fully observed cohort horizon. |
| ROAS D90 | D90 LTV / blended CAC × 100% | Revenue return as a percentage of acquisition cost; excludes operating costs. |
| Payback day | First player-age day cumulative LTV >= CAC | Not reached in the measured window does not mean never. |
| CPI | Acquisition spend / attributed installs | Equivalent to CAC in this install-based source. |
| CTR | Clicks / impressions | Not available: no click/impression source. |
| CVR | Conversions / clicks | Not available: no click/conversion funnel. |
| CPC | Spend / clicks | Not available: no click count. |
| eCPM | Ad revenue / served impressions × 1,000 | Not available: no impression count. |
| Fill rate | Served impressions / ad requests | Not available: no request/impression counts. |
| Retention | Active users on day N / cohort installs | Not available: no session/activity events. |

## Quality controls

Notebook checks cover missing cells, duplicate player/spend IDs, negative spend/revenue, zero or negative install rows, and orphan revenue-event player IDs. IQR screening flags unusually high/low channel-day CAC for review; flagged rows are not automatically deleted.

## Source limitations

Available user dimensions are country and platform. The source lacks app IDs, demand-partner IDs, sessions/activity, impression/request events, experiment variants, assignment and exposure. Consequently app/partner splits, CTR/fill/eCPM, retention and A/B treatment statistics are intentionally not reported.
