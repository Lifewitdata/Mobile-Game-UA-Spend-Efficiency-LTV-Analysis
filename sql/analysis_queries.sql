-- ============================================================
-- UA Spend Efficiency & LTV Analysis — Query Library (MySQL)
-- 20 queries covering spend, CAC, LTV, ROAS, and payback.
-- ============================================================


-- ------------------------------------------------------------
-- SECTION 1: SPEND & CAC
-- ------------------------------------------------------------

-- 1. Total spend and blended CAC by channel
SELECT
    channel,
    SUM(daily_spend_usd) AS total_spend,
    SUM(installs) AS total_installs,
    ROUND(SUM(daily_spend_usd) / NULLIF(SUM(installs), 0), 3) AS blended_cac
FROM ua_spend
GROUP BY channel
ORDER BY total_spend DESC;


-- 2. Daily CPI trend by channel (7-day rolling average not natively
--    supported pre-8.0 window functions; MySQL 8+ syntax shown)
SELECT
    channel,
    spend_date,
    ROUND(daily_spend_usd / NULLIF(installs, 0), 3) AS daily_cpi,
    ROUND(AVG(daily_spend_usd / NULLIF(installs, 0))
          OVER (PARTITION BY channel ORDER BY spend_date
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 3) AS cpi_7day_avg
FROM ua_spend
ORDER BY channel, spend_date;


-- 3. First-30-days vs last-30-days CAC by channel (marginal cost creep check)
SELECT
    channel,
    ROUND(SUM(CASE WHEN spend_date < (SELECT MIN(spend_date) FROM ua_spend) + INTERVAL 30 DAY
              THEN daily_spend_usd ELSE 0 END) /
          NULLIF(SUM(CASE WHEN spend_date < (SELECT MIN(spend_date) FROM ua_spend) + INTERVAL 30 DAY
              THEN installs ELSE 0 END), 0), 3) AS cac_first_30d,
    ROUND(SUM(CASE WHEN spend_date >= (SELECT MAX(spend_date) FROM ua_spend) - INTERVAL 30 DAY
              THEN daily_spend_usd ELSE 0 END) /
          NULLIF(SUM(CASE WHEN spend_date >= (SELECT MAX(spend_date) FROM ua_spend) - INTERVAL 30 DAY
              THEN installs ELSE 0 END), 0), 3) AS cac_last_30d
FROM ua_spend
GROUP BY channel;


-- 4. Spend and installs by campaign (drill into channel-level campaigns)
SELECT
    c.campaign_name,
    c.channel,
    SUM(s.daily_spend_usd) AS total_spend,
    SUM(s.installs) AS total_installs,
    ROUND(SUM(s.daily_spend_usd) / NULLIF(SUM(s.installs), 0), 3) AS cac
FROM ua_campaigns c
JOIN ua_spend s ON s.campaign_id = c.campaign_id
GROUP BY c.campaign_name, c.channel
ORDER BY total_spend DESC;


-- 5. Install volume by country and channel (where is spend concentrated?)
SELECT
    p.country,
    p.channel,
    COUNT(*) AS installs
FROM players p
GROUP BY p.country, p.channel
ORDER BY p.country, installs DESC;


-- ------------------------------------------------------------
-- SECTION 2: LTV
-- ------------------------------------------------------------

-- 6. Total revenue (IAP + ads) per player
SELECT
    player_id,
    SUM(revenue) AS total_revenue
FROM (
    SELECT player_id, usd_amount AS revenue FROM iap_transactions
    UNION ALL
    SELECT player_id, revenue_usd AS revenue FROM ad_revenue_events
) rev
GROUP BY player_id;


-- 7. LTV at Day 30 per player, by channel
SELECT
    p.channel,
    COUNT(DISTINCT p.player_id) AS installs,
    ROUND(SUM(rev.revenue) / COUNT(DISTINCT p.player_id), 4) AS ltv_d30
FROM players p
LEFT JOIN (
    SELECT player_id, transaction_timestamp AS event_ts, usd_amount AS revenue FROM iap_transactions
    UNION ALL
    SELECT player_id, event_timestamp AS event_ts, revenue_usd AS revenue FROM ad_revenue_events
) rev ON rev.player_id = p.player_id
     AND DATEDIFF(rev.event_ts, p.install_date) BETWEEN 0 AND 30
GROUP BY p.channel;


-- 8. LTV at Day 90 per player, by channel
SELECT
    p.channel,
    COUNT(DISTINCT p.player_id) AS installs,
    ROUND(SUM(rev.revenue) / COUNT(DISTINCT p.player_id), 4) AS ltv_d90
FROM players p
LEFT JOIN (
    SELECT player_id, transaction_timestamp AS event_ts, usd_amount AS revenue FROM iap_transactions
    UNION ALL
    SELECT player_id, event_timestamp AS event_ts, revenue_usd AS revenue FROM ad_revenue_events
) rev ON rev.player_id = p.player_id
     AND DATEDIFF(rev.event_ts, p.install_date) BETWEEN 0 AND 90
GROUP BY p.channel;


-- 9. IAP-only vs ad-only revenue split, by channel
SELECT
    p.channel,
    ROUND(COALESCE(SUM(i.usd_amount), 0), 2) AS iap_revenue,
    ROUND(COALESCE(SUM(a.revenue_usd), 0), 2) AS ad_revenue
FROM players p
LEFT JOIN iap_transactions i ON i.player_id = p.player_id
LEFT JOIN ad_revenue_events a ON a.player_id = p.player_id
GROUP BY p.channel;


-- 10. Payer conversion rate by channel
SELECT
    p.channel,
    COUNT(DISTINCT p.player_id) AS installs,
    COUNT(DISTINCT i.player_id) AS payers,
    ROUND(COUNT(DISTINCT i.player_id) / COUNT(DISTINCT p.player_id) * 100, 3) AS payer_conversion_pct
FROM players p
LEFT JOIN iap_transactions i ON i.player_id = p.player_id
GROUP BY p.channel;


-- 11. Top 10 highest-LTV players and their acquisition channel
SELECT
    p.player_id,
    p.channel,
    p.country,
    ROUND(SUM(rev.revenue), 2) AS total_ltv
FROM players p
JOIN (
    SELECT player_id, usd_amount AS revenue FROM iap_transactions
    UNION ALL
    SELECT player_id, revenue_usd AS revenue FROM ad_revenue_events
) rev ON rev.player_id = p.player_id
GROUP BY p.player_id, p.channel, p.country
ORDER BY total_ltv DESC
LIMIT 10;


-- ------------------------------------------------------------
-- SECTION 3: ROAS & PAYBACK
-- ------------------------------------------------------------

-- 12. D90 ROAS by channel (LTV / CAC as a percentage)
SELECT
    ltv.channel,
    ltv.ltv_d90,
    cac.blended_cac,
    ROUND(ltv.ltv_d90 / NULLIF(cac.blended_cac, 0) * 100, 1) AS roas_d90_pct
FROM (
    SELECT p.channel, SUM(rev.revenue) / COUNT(DISTINCT p.player_id) AS ltv_d90
    FROM players p
    LEFT JOIN (
        SELECT player_id, transaction_timestamp AS event_ts, usd_amount AS revenue FROM iap_transactions
        UNION ALL
        SELECT player_id, event_timestamp AS event_ts, revenue_usd AS revenue FROM ad_revenue_events
    ) rev ON rev.player_id = p.player_id AND DATEDIFF(rev.event_ts, p.install_date) BETWEEN 0 AND 90
    GROUP BY p.channel
) ltv
JOIN (
    SELECT channel, SUM(daily_spend_usd) / NULLIF(SUM(installs), 0) AS blended_cac
    FROM ua_spend
    GROUP BY channel
) cac ON cac.channel = ltv.channel;


-- 13. Cumulative LTV by day-since-install, by channel (for a payback curve chart)
SELECT
    p.channel,
    DATEDIFF(rev.event_ts, p.install_date) AS day_since_install,
    SUM(rev.revenue) / COUNT(DISTINCT p.player_id) OVER (
        PARTITION BY p.channel ORDER BY DATEDIFF(rev.event_ts, p.install_date)
    ) AS running_ltv_approx
FROM players p
JOIN (
    SELECT player_id, transaction_timestamp AS event_ts, usd_amount AS revenue FROM iap_transactions
    UNION ALL
    SELECT player_id, event_timestamp AS event_ts, revenue_usd AS revenue FROM ad_revenue_events
) rev ON rev.player_id = p.player_id
WHERE DATEDIFF(rev.event_ts, p.install_date) BETWEEN 0 AND 90
GROUP BY p.channel, DATEDIFF(rev.event_ts, p.install_date)
ORDER BY p.channel, day_since_install;


-- 14. Channels that have NOT paid back within 90 days (LTV < CAC at D90)
SELECT
    ltv.channel,
    ROUND(ltv.ltv_d90, 4) AS ltv_d90,
    ROUND(cac.blended_cac, 4) AS cac,
    ROUND(ltv.ltv_d90 - cac.blended_cac, 4) AS gap
FROM (
    SELECT p.channel, SUM(rev.revenue) / COUNT(DISTINCT p.player_id) AS ltv_d90
    FROM players p
    LEFT JOIN (
        SELECT player_id, transaction_timestamp AS event_ts, usd_amount AS revenue FROM iap_transactions
        UNION ALL
        SELECT player_id, event_timestamp AS event_ts, revenue_usd AS revenue FROM ad_revenue_events
    ) rev ON rev.player_id = p.player_id AND DATEDIFF(rev.event_ts, p.install_date) BETWEEN 0 AND 90
    GROUP BY p.channel
) ltv
JOIN (
    SELECT channel, SUM(daily_spend_usd) / NULLIF(SUM(installs), 0) AS blended_cac
    FROM ua_spend GROUP BY channel
) cac ON cac.channel = ltv.channel
WHERE ltv.ltv_d90 < cac.blended_cac;


-- 15. Blended portfolio ROAS (all paid channels combined, excluding organic)
SELECT
    ROUND(SUM(rev.revenue) / NULLIF((SELECT SUM(daily_spend_usd) FROM ua_spend WHERE channel != 'organic'), 0) * 100, 2)
        AS blended_portfolio_roas_pct
FROM players p
JOIN (
    SELECT player_id, usd_amount AS revenue FROM iap_transactions
    UNION ALL
    SELECT player_id, revenue_usd AS revenue FROM ad_revenue_events
) rev ON rev.player_id = p.player_id
WHERE p.channel != 'organic';


-- ------------------------------------------------------------
-- SECTION 4: PLATFORM / GEO CUTS
-- ------------------------------------------------------------

-- 16. LTV by platform (iOS vs Android)
SELECT
    p.platform,
    COUNT(DISTINCT p.player_id) AS installs,
    ROUND(SUM(rev.revenue) / COUNT(DISTINCT p.player_id), 4) AS ltv
FROM players p
LEFT JOIN (
    SELECT player_id, usd_amount AS revenue FROM iap_transactions
    UNION ALL
    SELECT player_id, revenue_usd AS revenue FROM ad_revenue_events
) rev ON rev.player_id = p.player_id
GROUP BY p.platform;


-- 17. LTV by country, top 5 by revenue per install
SELECT
    p.country,
    COUNT(DISTINCT p.player_id) AS installs,
    ROUND(SUM(rev.revenue) / COUNT(DISTINCT p.player_id), 4) AS ltv
FROM players p
LEFT JOIN (
    SELECT player_id, usd_amount AS revenue FROM iap_transactions
    UNION ALL
    SELECT player_id, revenue_usd AS revenue FROM ad_revenue_events
) rev ON rev.player_id = p.player_id
GROUP BY p.country
ORDER BY ltv DESC
LIMIT 5;


-- 18. Channel x platform CAC-efficiency matrix
SELECT
    p.channel,
    p.platform,
    COUNT(DISTINCT p.player_id) AS installs,
    ROUND(SUM(rev.revenue) / COUNT(DISTINCT p.player_id), 4) AS ltv
FROM players p
LEFT JOIN (
    SELECT player_id, usd_amount AS revenue FROM iap_transactions
    UNION ALL
    SELECT player_id, revenue_usd AS revenue FROM ad_revenue_events
) rev ON rev.player_id = p.player_id
GROUP BY p.channel, p.platform
ORDER BY p.channel, ltv DESC;


-- ------------------------------------------------------------
-- SECTION 5: PRODUCT & AD REVENUE MIX
-- ------------------------------------------------------------

-- 19. Revenue by IAP product type
SELECT
    product_type,
    COUNT(*) AS transactions,
    ROUND(SUM(usd_amount), 2) AS total_revenue,
    ROUND(AVG(usd_amount), 2) AS avg_transaction_value
FROM iap_transactions
GROUP BY product_type
ORDER BY total_revenue DESC;


-- 20. Ad revenue by ad type and channel
SELECT
    p.channel,
    a.ad_type,
    COUNT(*) AS ad_events,
    ROUND(SUM(a.revenue_usd), 2) AS total_ad_revenue
FROM ad_revenue_events a
JOIN players p ON p.player_id = a.player_id
GROUP BY p.channel, a.ad_type
ORDER BY p.channel, total_ad_revenue DESC;
