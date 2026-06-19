-- Migration: 0001_create_tables.sql
-- Creates core metadata tables for VideoMind AI

-- Ensure pgcrypto extension for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_uri TEXT NOT NULL,
    duration_seconds DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transcript_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    start_time DOUBLE PRECISION NOT NULL,
    end_time DOUBLE PRECISION NOT NULL,
    embedding JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_transcript_video_id ON transcript_chunks(video_id);
CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at);
