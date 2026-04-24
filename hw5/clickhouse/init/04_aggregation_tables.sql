CREATE TABLE IF NOT EXISTS agg_dau
(
    event_date Date,
    unique_users UInt64
)
ENGINE = ReplacingMergeTree()
ORDER BY event_date;

CREATE TABLE IF NOT EXISTS agg_avg_watch_time
(
    event_date Date,
    avg_progress_seconds Float64
)
ENGINE = ReplacingMergeTree()
ORDER BY event_date;

CREATE TABLE IF NOT EXISTS agg_top_movies
(
    event_date Date,
    movie_id String,
    view_count UInt64,
    rank UInt32
)
ENGINE = ReplacingMergeTree()
ORDER BY (event_date, movie_id);

CREATE TABLE IF NOT EXISTS agg_conversion
(
    event_date Date,
    view_started_count UInt64,
    view_finished_count UInt64,
    conversion_ratio Float64
)
ENGINE = ReplacingMergeTree()
ORDER BY event_date;

CREATE TABLE IF NOT EXISTS agg_retention
(
    cohort_date Date,
    day_of_life UInt8,
    cohort_size UInt64,
    returning_users UInt64,
    retention_pct Float64
)
ENGINE = ReplacingMergeTree()
ORDER BY (cohort_date, day_of_life);
