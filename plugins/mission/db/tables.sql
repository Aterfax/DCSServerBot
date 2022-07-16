CREATE TABLE IF NOT EXISTS players (ucid TEXT PRIMARY KEY, discord_id BIGINT, name TEXT, ipaddr TEXT, coalition TEXT, coalition_leave TIMESTAMP, manual BOOLEAN DEFAULT FALSE, last_seen TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_players_discord_id ON players(discord_id);
CREATE TABLE IF NOT EXISTS missions (id SERIAL PRIMARY KEY, server_name TEXT NOT NULL, mission_name TEXT NOT NULL, mission_theatre TEXT NOT NULL, mission_start TIMESTAMP NOT NULL DEFAULT NOW(), mission_end TIMESTAMP);
CREATE TABLE IF NOT EXISTS players_hist (id SERIAL PRIMARY KEY, ucid TEXT NOT NULL, discord_id BIGINT NOT NULL, name TEXT NOT NULL, ipaddr TEXT NOT NULL, coalition TEXT, manual BOOLEAN NOT NULL, time TIMESTAMP NOT NULL DEFAULT NOW());
CREATE INDEX IF NOT EXISTS idx_players_hist_discord_id ON players_hist(discord_id);
CREATE INDEX IF NOT EXISTS idx_players_hist_ucid ON players_hist(ucid);
CREATE OR REPLACE FUNCTION player_hist_change() RETURNS trigger AS $$ BEGIN INSERT INTO players_hist(ucid, discord_id, name, ipaddr, coalition, manual) SELECT OLD.ucid, OLD.discord_id, OLD.name, OLD.ipaddr, OLD.coalition, OLD.manual; RETURN NEW; END; $$ LANGUAGE 'plpgsql';
CREATE TRIGGER IF NOT EXISTS tgr_player_update AFTER UPDATE OF discord_id, name, ipaddr, coalition, manual ON players FOR EACH ROW EXECUTE PROCEDURE player_hist_change();
