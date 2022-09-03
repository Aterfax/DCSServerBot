CREATE TABLE IF NOT EXISTS credits (campaign_id INTEGER NOT NULL, player_ucid TEXT NOT NULL, points INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(campaign_id, player_ucid));
CREATE TABLE IF NOT EXISTS credits_log (id SERIAL PRIMARY KEY, campaign_id INTEGER NOT NULL, event TEXT NOT NULL, player_ucid TEXT NOT NULL, old_points INTEGER NOT NULL, new_points INTEGER NOT NULL, remark TEXT, time TIMESTAMP DEFAULT NOW());
