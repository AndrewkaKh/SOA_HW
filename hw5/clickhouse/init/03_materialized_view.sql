CREATE MATERIALIZED VIEW IF NOT EXISTS events_mv
TO events
AS
SELECT
    event_id,
    user_id,
    movie_id,
    CAST(event_type, 'String') AS event_type,
    timestamp,
    CAST(device_type, 'String') AS device_type,
    session_id,
    progress_seconds
FROM events_kafka;
