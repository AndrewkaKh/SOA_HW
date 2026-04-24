CREATE TABLE IF NOT EXISTS metrics
(
    id BIGSERIAL PRIMARY KEY,
    metric_date DATE NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value JSONB NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (metric_date, metric_name)
);

CREATE TABLE IF NOT EXISTS retention_cohorts
(
    cohort_date DATE NOT NULL,
    day_of_life SMALLINT NOT NULL,
    cohort_size BIGINT NOT NULL,
    returning_users BIGINT NOT NULL,
    retention_pct FLOAT NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (cohort_date, day_of_life)
);
