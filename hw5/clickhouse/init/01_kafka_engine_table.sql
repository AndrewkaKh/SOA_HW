CREATE TABLE IF NOT EXISTS events_kafka
(
    event_id String,
    user_id String,
    movie_id String,
    event_type String,
    timestamp DateTime64(6),
    device_type String,
    session_id String,
    progress_seconds Int32
)
ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'kafka-1:9092,kafka-2:9093',
    kafka_topic_list = 'movie-events',
    kafka_group_name = 'clickhouse-consumer',
    kafka_format = 'AvroConfluent',
    kafka_schema_registry_url = 'http://schema-registry:8081',
    kafka_num_consumers = 1,
    kafka_handle_error_mode = 'stream';
