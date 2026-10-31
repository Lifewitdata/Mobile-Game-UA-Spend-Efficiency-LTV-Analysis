-- Extended synthetic demo schema. Run sql/schema.sql first.
-- These tables are generated demonstration data, not production telemetry.

CREATE TABLE IF NOT EXISTS apps (
    app_id VARCHAR(20) PRIMARY KEY,
    app_name VARCHAR(80) NOT NULL,
    genre VARCHAR(30) NOT NULL,
    package_name VARCHAR(100) NOT NULL
);
CREATE TABLE IF NOT EXISTS demand_partners (
    demand_partner_id VARCHAR(20) PRIMARY KEY,
    partner_name VARCHAR(80) NOT NULL,
    mediation_group VARCHAR(40) NOT NULL
);
CREATE TABLE IF NOT EXISTS player_app_mapping (
    player_id INT PRIMARY KEY,
    app_id VARCHAR(20) NOT NULL,
    mapping_source VARCHAR(40) NOT NULL,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (app_id) REFERENCES apps(app_id)
);
CREATE TABLE IF NOT EXISTS player_sessions (
    session_id BIGINT PRIMARY KEY,
    player_id INT NOT NULL,
    app_id VARCHAR(20) NOT NULL,
    session_start DATETIME NOT NULL,
    session_end DATETIME NOT NULL,
    session_duration_seconds INT NOT NULL,
    session_day SMALLINT NOT NULL,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (app_id) REFERENCES apps(app_id),
    INDEX idx_session_player_day (player_id, session_day),
    INDEX idx_session_start (session_start)
);
CREATE TABLE IF NOT EXISTS experiment_assignments (
    assignment_id BIGINT PRIMARY KEY,
    experiment_id VARCHAR(64) NOT NULL,
    player_id INT NOT NULL,
    variant VARCHAR(20) NOT NULL,
    assigned_at DATETIME NOT NULL,
    randomization_unit VARCHAR(30) NOT NULL,
    allocation_design VARCHAR(40) NOT NULL,
    data_origin VARCHAR(60) NOT NULL,
    UNIQUE KEY uq_experiment_player (experiment_id, player_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    INDEX idx_assignment_variant (experiment_id, variant)
);
CREATE TABLE IF NOT EXISTS experiment_exposures (
    exposure_id BIGINT PRIMARY KEY,
    experiment_id VARCHAR(64) NOT NULL,
    player_id INT NOT NULL,
    variant VARCHAR(20) NOT NULL,
    exposure_timestamp DATETIME NOT NULL,
    app_id VARCHAR(20) NOT NULL,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (app_id) REFERENCES apps(app_id),
    INDEX idx_exposure_player (experiment_id, player_id)
);
CREATE TABLE IF NOT EXISTS ad_delivery_events (
    request_id VARCHAR(32) PRIMARY KEY,
    player_id INT NOT NULL,
    app_id VARCHAR(20) NOT NULL,
    demand_partner_id VARCHAR(20) NOT NULL,
    session_id BIGINT NOT NULL,
    request_timestamp DATETIME NOT NULL,
    ad_format VARCHAR(30) NOT NULL,
    request_status VARCHAR(20) NOT NULL,
    impression_id VARCHAR(32) NULL,
    click_id VARCHAR(32) NULL,
    revenue_usd DECIMAL(10,5) NOT NULL,
    experiment_id VARCHAR(64) NOT NULL,
    experiment_variant VARCHAR(20) NOT NULL,
    UNIQUE KEY uq_ad_impression (impression_id),
    UNIQUE KEY uq_ad_click (click_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (app_id) REFERENCES apps(app_id),
    FOREIGN KEY (demand_partner_id) REFERENCES demand_partners(demand_partner_id),
    FOREIGN KEY (session_id) REFERENCES player_sessions(session_id),
    INDEX idx_ad_app_partner (app_id, demand_partner_id),
    INDEX idx_ad_timestamp (request_timestamp),
    INDEX idx_ad_variant (experiment_id, experiment_variant)
);
CREATE TABLE IF NOT EXISTS experiment_player_outcomes (
    experiment_id VARCHAR(64) NOT NULL,
    player_id INT NOT NULL,
    assigned_variant VARCHAR(20) NOT NULL,
    assignment_id BIGINT NOT NULL,
    was_exposed TINYINT NOT NULL,
    sessions_first_7d INT NOT NULL,
    retained_d7 TINYINT NOT NULL,
    ad_revenue_first_7d_usd DECIMAL(10,5) NOT NULL,
    iap_revenue_first_7d_usd DECIMAL(10,2) NOT NULL,
    total_revenue_first_7d_usd DECIMAL(10,5) NOT NULL,
    d7_observation_complete TINYINT NOT NULL,
    PRIMARY KEY (experiment_id, player_id),
    FOREIGN KEY (assignment_id) REFERENCES experiment_assignments(assignment_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);
