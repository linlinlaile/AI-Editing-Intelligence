import sqlite3

SCHEMA_VERSION=1
MIGRATION_SQL='''
CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS media_assets(id TEXT PRIMARY KEY, uri TEXT NOT NULL, byte_size INTEGER, fingerprint TEXT NOT NULL UNIQUE, format_name TEXT);
CREATE TABLE IF NOT EXISTS media_streams(id TEXT PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES media_assets(id), stream_index INTEGER NOT NULL, kind TEXT NOT NULL, codec TEXT, tb_num INTEGER NOT NULL, tb_den INTEGER NOT NULL, start_pts INTEGER, duration_pts INTEGER, width INTEGER, height INTEGER, pixel_format TEXT, avg_fps_num INTEGER, avg_fps_den INTEGER, nominal_fps_num INTEGER, nominal_fps_den INTEGER, rotation INTEGER, sar_num INTEGER, sar_den INTEGER, dar_num INTEGER, dar_den INTEGER, color_metadata_json TEXT NOT NULL DEFAULT '{}', UNIQUE(asset_id,stream_index));
CREATE TABLE IF NOT EXISTS timeline_layers(id TEXT PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES media_assets(id), kind TEXT NOT NULL, detector_revision TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS temporal_segments(id TEXT PRIMARY KEY, layer_id TEXT NOT NULL REFERENCES timeline_layers(id), kind TEXT NOT NULL, stream_id TEXT NOT NULL REFERENCES media_streams(id), start_pts INTEGER NOT NULL, end_pts INTEGER NOT NULL, start_frame_index INTEGER, end_frame_index INTEGER);
'''
def migrate(conn: sqlite3.Connection):
    conn.executescript(MIGRATION_SQL)
    conn.execute('INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)',(SCHEMA_VERSION,)); conn.commit()
