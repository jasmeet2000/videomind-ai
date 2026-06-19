-- SQLite migration: create core tables

CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    source_uri TEXT NOT NULL,
    duration_seconds REAL,
    status TEXT DEFAULT 'uploaded',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transcript_chunks (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    content TEXT NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    embedding TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_transcript_video_id ON transcript_chunks(video_id);
CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at);
