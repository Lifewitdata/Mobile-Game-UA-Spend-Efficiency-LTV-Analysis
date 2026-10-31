# SQL run guide (MySQL 8.0+)

The query library uses CTEs and window functions and targets MySQL 8.0+.

## 1. Create database and tables

```sql
CREATE DATABASE mobile_game_ua;
USE mobile_game_ua;
```

Run [../sql/schema.sql](../sql/schema.sql).

## 2. Import CSV files

Use MySQL Workbench Table Data Import Wizard and map columns to the schema. Import in this order to satisfy foreign keys:

1. `ua_campaigns.csv` → `ua_campaigns`
2. `players.csv` → `players`
3. `ua_spend.csv` → `ua_spend`
4. `iap_transactions.csv` → `iap_transactions`
5. `ad_revenue_events.csv` → `ad_revenue_events`

Alternatively, use `LOAD DATA LOCAL INFILE` with local-infile enabled on both client and server, providing an absolute CSV path. Never commit database credentials.

## 3. Verify imported row counts

```sql
SELECT 'ua_campaigns' AS table_name, COUNT(*) AS row_count FROM ua_campaigns
UNION ALL SELECT 'ua_spend', COUNT(*) FROM ua_spend
UNION ALL SELECT 'players', COUNT(*) FROM players
UNION ALL SELECT 'iap_transactions', COUNT(*) FROM iap_transactions
UNION ALL SELECT 'ad_revenue_events', COUNT(*) FROM ad_revenue_events;
```

Check the blended CAC result:

```sql
SELECT channel, ROUND(SUM(daily_spend_usd)/NULLIF(SUM(installs),0),2) AS blended_cac
FROM ua_spend GROUP BY channel ORDER BY blended_cac;
```

Expected paid-channel ordering for the committed snapshot: cross_promo ($0.45), paid_social ($1.54), paid_search ($3.16). Organic has no paid spend.

## 4. Execute query library

Run [../sql/analysis_queries.sql](../sql/analysis_queries.sql). Queries 21–24 demonstrate CTEs, `RANK`, `LAG` and running totals. No execution output is committed; the verification queries above are the expected sanity checks.


## Automated SQL execution

The GitHub Actions workflow starts MySQL 8.0, creates tables from the schema, loads all committed CSVs, executes every statement in the SQL library, and checks the known paid-channel CAC ordering. To run this locally, install the pinned requirements, start a MySQL 8.0 server, set `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD` and `MYSQL_DATABASE`, then run:

```bash
python scripts/validate_sql.py
```

The script prints the number of query statements successfully executed and validates the expected CAC outputs. It does not publish database credentials.
