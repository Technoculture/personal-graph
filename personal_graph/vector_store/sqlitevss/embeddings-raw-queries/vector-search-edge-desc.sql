WITH matches AS (
  SELECT rowid, distance
  FROM relationship_embedding
  WHERE vss_search(vector_relations, vss_search_params(json(?), ?))
)
SELECT
  rowid,
  edges.source,
  edges.target,
  edges.label,
  edges.attributes,
  matches.distance
FROM matches
JOIN edges ON edges.embed_id = matches.rowid
ORDER BY distance DESC
LIMIT ?;
