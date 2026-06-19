-- Migration: 0002_add_video_status.sql
-- Adds a status column to videos for processing lifecycle state

ALTER TABLE videos ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'uploaded';
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
