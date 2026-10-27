CREATE TABLE IF NOT EXISTS entries (
    id         bigserial PRIMARY KEY,
    author     text        NOT NULL,
    message    text        NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
