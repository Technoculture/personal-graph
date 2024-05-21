WITH matches AS (
  SELECT rowid, distance
  FROM nodes_embedding
  WHERE vss_search(vector_nodes, vss_search_params(json(?), ?))
)
SELECT
  rowid,
  nodes.id,
  nodes.label,
  nodes.attributes,
  matches.distance
FROM matches
JOIN nodes ON nodes.embed_id = matches.rowid
ORDER BY
  CASE
    WHEN ? != "" AND ? IS TRUE THEN json_extract(nodes.attributes, '$.' || ?) ELSE NULL
  END DESC,
  CASE
    WHEN ? != "" AND ? IS FALSE THEN json_extract(nodes.attributes, '$.' || ?) ELSE NULL
  END ASC;