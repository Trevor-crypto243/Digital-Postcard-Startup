-- Initialize application schema
CREATE TABLE IF NOT EXISTS human_reviews (
    submission_id TEXT PRIMARY KEY,
    decision TEXT NOT NULL,
    reasoning TEXT,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
