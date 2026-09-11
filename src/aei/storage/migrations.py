import sqlite3

SCHEMA_VERSION = 2
MIGRATION_SQL = '''
CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS media_assets(id TEXT PRIMARY KEY, uri TEXT NOT NULL, byte_size INTEGER, fingerprint TEXT NOT NULL UNIQUE, format_name TEXT);
CREATE TABLE IF NOT EXISTS media_streams(id TEXT PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES media_assets(id), stream_index INTEGER NOT NULL, kind TEXT NOT NULL, codec TEXT, tb_num INTEGER NOT NULL, tb_den INTEGER NOT NULL, start_pts INTEGER, duration_pts INTEGER, width INTEGER, height INTEGER, pixel_format TEXT, avg_fps_num INTEGER, avg_fps_den INTEGER, nominal_fps_num INTEGER, nominal_fps_den INTEGER, rotation INTEGER, sar_num INTEGER, sar_den INTEGER, dar_num INTEGER, dar_den INTEGER, color_metadata_json TEXT NOT NULL DEFAULT '{}', UNIQUE(asset_id,stream_index));
CREATE TABLE IF NOT EXISTS timeline_layers(id TEXT PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES media_assets(id), kind TEXT NOT NULL, detector_revision TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS temporal_segments(id TEXT PRIMARY KEY, layer_id TEXT NOT NULL REFERENCES timeline_layers(id), kind TEXT NOT NULL, stream_id TEXT NOT NULL REFERENCES media_streams(id), start_pts INTEGER NOT NULL, end_pts INTEGER NOT NULL, start_frame_index INTEGER, end_frame_index INTEGER);
CREATE TABLE IF NOT EXISTS analysis_runs(id TEXT PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES media_assets(id), producer_name TEXT NOT NULL, status TEXT NOT NULL, model_name TEXT, model_revision TEXT, code_revision TEXT, config_hash TEXT, input_artifact_ids_json TEXT NOT NULL DEFAULT '[]', parent_run_ids_json TEXT NOT NULL DEFAULT '[]', started_at TEXT, completed_at TEXT);
CREATE TABLE IF NOT EXISTS samples(id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES analysis_runs(id), asset_id TEXT NOT NULL REFERENCES media_assets(id), purpose TEXT NOT NULL, kind TEXT NOT NULL, stream_id TEXT, start_pts INTEGER, start_tb_num INTEGER, start_tb_den INTEGER, end_pts INTEGER, end_tb_num INTEGER, end_tb_den INTEGER, start_frame_index INTEGER, end_frame_index INTEGER, source_frame_index INTEGER, selection_reason TEXT, artifact_ids_json TEXT NOT NULL DEFAULT '[]');
CREATE TABLE IF NOT EXISTS evidences(id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES analysis_runs(id), kind TEXT NOT NULL, description TEXT, stream_id TEXT, start_pts INTEGER, start_tb_num INTEGER, start_tb_den INTEGER, end_pts INTEGER, end_tb_num INTEGER, end_tb_den INTEGER, frame_start INTEGER, frame_end INTEGER, numeric_measurement_json TEXT, external_artifact_ref TEXT, artifact_hash TEXT, metadata_json TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS observations(id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES analysis_runs(id), target_type TEXT NOT NULL, target_id TEXT NOT NULL, feature TEXT NOT NULL, value_json TEXT NOT NULL, value_status TEXT NOT NULL, confidence REAL, confidence_kind TEXT, coverage REAL, producer_ref TEXT);
CREATE TABLE IF NOT EXISTS observation_evidence(observation_id TEXT NOT NULL REFERENCES observations(id) ON DELETE CASCADE, evidence_id TEXT NOT NULL REFERENCES evidences(id), PRIMARY KEY(observation_id,evidence_id));
CREATE INDEX IF NOT EXISTS idx_samples_run ON samples(run_id);
CREATE INDEX IF NOT EXISTS idx_evidence_run ON evidences(run_id);
CREATE INDEX IF NOT EXISTS idx_observations_run_target ON observations(run_id,target_type,target_id);
'''

def migrate(conn: sqlite3.Connection):
    conn.executescript(MIGRATION_SQL)
    conn.execute('INSERT OR IGNORE INTO schema_migrations(version) VALUES (1)')
    conn.execute('INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)', (SCHEMA_VERSION,))
    conn.commit()

