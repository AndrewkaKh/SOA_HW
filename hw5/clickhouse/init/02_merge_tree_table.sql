CREATE TABLE IF NOT EXISTS events
(
    event_id String,
    user_id String,
    movie_id String,
    event_type LowCardinality(String),
    timestamp DateTime64(6),
    device_type LowCardinality(String),
    session_id String,
    progress_seconds Int32,
    event_date Date MATERIALIZED toDate(timestamp)
)
ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (event_date, user_id, session_id, event_id);
