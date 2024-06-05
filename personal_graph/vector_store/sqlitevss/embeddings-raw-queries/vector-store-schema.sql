begin;

CREATE VIRTUAL TABLE IF NOT EXISTS nodes_embedding USING vss0(
  vector_nodes({{size}})
);

CREATE VIRTUAL TABLE IF NOT EXISTS relationship_embedding USING vss0(
  vector_relations({{size}})
);

commit;