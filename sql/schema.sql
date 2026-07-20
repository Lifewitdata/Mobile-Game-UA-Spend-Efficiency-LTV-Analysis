-- ============================================================
-- Mobile Game UA Spend Efficiency & LTV Analysis — Schema
-- Portfolio project: CAC, LTV, ROAS, Payback Period by Channel
-- ============================================================

CREATE TABLE ua_campaigns (
    campaign_id       INT PRIMARY KEY,
    channel           VARCHAR(20) NOT NULL,     -- paid_social / paid_search / cross_promo / organic
    campaign_name     VARCHAR(50) NOT NULL,
    start_date        DATE NOT NULL,
    end_date          DATE NOT NULL
);

CREATE TABLE ua_spend (
    spend_id          BIGINT PRIMARY KEY,
    campaign_id       INT NOT NULL REFERENCES ua_campaigns(campaign_id),
    channel           VARCHAR(20) NOT NULL,
    spend_date        DATE NOT NULL,
    daily_spend_usd   DECIMAL(10,2) NOT NULL,
    installs          INT NOT NULL              -- installs attributed to this campaign that day
);

CREATE TABLE players (
    player_id         INT PRIMARY KEY,
    install_date      DATE NOT NULL,
    channel           VARCHAR(20) NOT NULL,
    campaign_id       INT REFERENCES ua_campaigns(campaign_id),  -- NULL for organic
    country           VARCHAR(2) NOT NULL,
    platform          VARCHAR(10) NOT NULL
);

CREATE TABLE iap_transactions (
    transaction_id           BIGINT PRIMARY KEY,
    player_id                 INT NOT NULL REFERENCES players(player_id),
    transaction_timestamp     DATETIME NOT NULL,
    product_type               VARCHAR(20) NOT NULL,
    usd_amount                 DECIMAL(6,2) NOT NULL
);

CREATE TABLE ad_revenue_events (
    event_id           BIGINT PRIMARY KEY,
    player_id            INT NOT NULL REFERENCES players(player_id),
    event_timestamp       DATETIME NOT NULL,
    ad_type                VARCHAR(20) NOT NULL,   -- rewarded_video / interstitial
    revenue_usd            DECIMAL(6,4) NOT NULL
);

CREATE INDEX idx_players_channel ON players(channel);
CREATE INDEX idx_players_campaign ON players(campaign_id);
CREATE INDEX idx_spend_campaign ON ua_spend(campaign_id);
CREATE INDEX idx_spend_date ON ua_spend(spend_date);
CREATE INDEX idx_iap_player ON iap_transactions(player_id);
CREATE INDEX idx_ad_player ON ad_revenue_events(player_id);
