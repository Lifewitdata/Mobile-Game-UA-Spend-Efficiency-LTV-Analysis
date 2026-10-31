-- Extended synthetic monetisation, retention and experiment examples.
-- Run sql/schema.sql and sql/extended_demo_schema.sql first.

-- 1. Ad request fill rate, CTR and eCPM by app and demand partner.
SELECT app_id, demand_partner_id, ad_format,
       COUNT(*) AS ad_requests,
       SUM(request_status = 'filled') AS impressions,
       SUM(click_id IS NOT NULL AND click_id <> '') AS clicks,
       ROUND(SUM(request_status = 'filled') / NULLIF(COUNT(*), 0), 4) AS fill_rate,
       ROUND(SUM(click_id IS NOT NULL AND click_id <> '') /
             NULLIF(SUM(request_status = 'filled'), 0), 4) AS ctr,
       ROUND(SUM(revenue_usd) / NULLIF(SUM(request_status = 'filled'), 0) * 1000, 2) AS ecpm_usd
FROM ad_delivery_events
GROUP BY app_id, demand_partner_id, ad_format
ORDER BY app_id, demand_partner_id, ad_format;

-- 2. Revenue and delivery by partner.
SELECT d.demand_partner_id, d.partner_name,
       COUNT(a.request_id) AS requests,
       SUM(a.request_status = 'filled') AS impressions,
       ROUND(SUM(a.revenue_usd), 2) AS ad_revenue_usd,
       ROUND(SUM(a.revenue_usd) / NULLIF(SUM(a.request_status = 'filled'), 0) * 1000, 2) AS ecpm_usd
FROM demand_partners d
LEFT JOIN ad_delivery_events a ON a.demand_partner_id = d.demand_partner_id
GROUP BY d.demand_partner_id, d.partner_name
ORDER BY ad_revenue_usd DESC;

-- 3. D1, D7 and D30 retention by install cohort week. Complete day-30 cohorts only.
WITH observation AS (
    SELECT MAX(DATE(session_start)) AS last_observed_date FROM player_sessions
),
cohort_players AS (
    SELECT p.player_id, p.install_date,
           DATE_SUB(p.install_date, INTERVAL WEEKDAY(p.install_date) DAY) AS install_week
    FROM players p CROSS JOIN observation o
    WHERE DATE_ADD(p.install_date, INTERVAL 30 DAY) <= o.last_observed_date
),
cohort_activity AS (
    SELECT cp.install_week,
           COUNT(DISTINCT cp.player_id) AS eligible_installs,
           COUNT(DISTINCT CASE WHEN s.session_day = 1 THEN cp.player_id END) AS active_d1,
           COUNT(DISTINCT CASE WHEN s.session_day = 7 THEN cp.player_id END) AS active_d7,
           COUNT(DISTINCT CASE WHEN s.session_day = 30 THEN cp.player_id END) AS active_d30
    FROM cohort_players cp
    LEFT JOIN player_sessions s ON s.player_id = cp.player_id
    GROUP BY cp.install_week
)
SELECT install_week, eligible_installs,
       ROUND(active_d1 / NULLIF(eligible_installs, 0) * 100, 2) AS retention_d1_pct,
       ROUND(active_d7 / NULLIF(eligible_installs, 0) * 100, 2) AS retention_d7_pct,
       ROUND(active_d30 / NULLIF(eligible_installs, 0) * 100, 2) AS retention_d30_pct
FROM cohort_activity
ORDER BY install_week;

-- 4. Primary experiment view: intention-to-treat by random assignment.
SELECT assigned_variant, COUNT(*) AS assigned_players,
       ROUND(AVG(retained_d7) * 100, 2) AS retention_d7_pct,
       ROUND(AVG(sessions_first_7d), 3) AS avg_sessions_first_7d,
       ROUND(AVG(total_revenue_first_7d_usd), 5) AS avg_revenue_first_7d_per_player_usd,
       ROUND(AVG(was_exposed) * 100, 2) AS exposure_rate_pct
FROM experiment_player_outcomes
WHERE experiment_id = 'interstitial_frequency_cap_v1'
  AND d7_observation_complete = 1
GROUP BY assigned_variant
ORDER BY assigned_variant;

-- 5. Randomisation balance by app, acquisition channel and platform.
SELECT m.app_id, p.channel, p.platform,
       SUM(a.variant = 'control') AS control_players,
       SUM(a.variant = 'treatment') AS treatment_players
FROM experiment_assignments a
JOIN players p ON p.player_id = a.player_id
JOIN player_app_mapping m ON m.player_id = p.player_id
WHERE a.experiment_id = 'interstitial_frequency_cap_v1'
GROUP BY m.app_id, p.channel, p.platform
ORDER BY m.app_id, p.channel, p.platform;

-- 6. Exposure rate is a delivery diagnostic, not the primary ITT denominator.
SELECT a.variant, COUNT(DISTINCT a.player_id) AS assigned_players,
       COUNT(DISTINCT e.player_id) AS exposed_players,
       ROUND(COUNT(DISTINCT e.player_id) / NULLIF(COUNT(DISTINCT a.player_id), 0) * 100, 2) AS exposure_rate_pct
FROM experiment_assignments a
LEFT JOIN experiment_exposures e
  ON e.experiment_id = a.experiment_id AND e.player_id = a.player_id
WHERE a.experiment_id = 'interstitial_frequency_cap_v1'
GROUP BY a.variant;
