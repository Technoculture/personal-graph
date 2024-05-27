begin;

CREATE VIRTUAL TABLE IF NOT EXISTS nodes_embedding USING vss0(
  vector_nodes(384)
);

CREATE VIRTUAL TABLE IF NOT EXISTS relationship_embedding USING vss0(
  vector_relations(384)
);

commit;