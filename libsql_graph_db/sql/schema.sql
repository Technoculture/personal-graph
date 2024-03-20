CREATE TABLE IF NOT EXISTS nodes (
    embed_id TEXT NOT NULL UNIQUE,
    body TEXT,
    id   TEXT GENERATED ALWAYS AS (json_extract(body, '$.id')) VIRTUAL NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS id_idx ON nodes(id);

CREATE TABLE IF NOT EXISTS edges (
    embed_id TEXT NOT NULL UNIQUE,
    source     TEXT,
    target     TEXT,
    properties TEXT,
    UNIQUE(source, target, properties) ON CONFLICT REPLACE,
    FOREIGN KEY(source) REFERENCES nodes(id),
    FOREIGN KEY(target) REFERENCES nodes(id)
);

CREATE INDEX IF NOT EXISTS source_idx ON edges(source);
CREATE INDEX IF NOT EXISTS target_idx ON edges(target);

begin;

CREATE VIRTUAL TABLE IF NOT EXISTS nodes_embedding USING vss0(
  vector_nodes(384)
);

CREATE VIRTUAL TABLE IF NOT EXISTS relationship_embedding USING vss0(
  vector_relations(384)
);

commit;