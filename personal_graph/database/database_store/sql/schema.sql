CREATE TABLE IF NOT EXISTS nodes (
    embed_id INT NOT NULL UNIQUE,
    label TEXT,
    attributes JSON,
    id   TEXT GENERATED ALWAYS AS (json_extract(attributes, '$.id')) VIRTUAL NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS id_idx ON nodes(id);

CREATE TABLE IF NOT EXISTS edges (
    embed_id INTEGER NOT NULL UNIQUE,
    source     TEXT,
    target     TEXT,
    label TEXT,
    attributes JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source, target, attributes) ON CONFLICT REPLACE,
    FOREIGN KEY(source) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY(target) REFERENCES nodes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS source_idx ON edges(source);
CREATE INDEX IF NOT EXISTS target_idx ON edges(target);
