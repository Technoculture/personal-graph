SELECT
  n.embed_id,
  n.id,
  n.label,
  n.attributes
FROM nodes n
JOIN (SELECT value AS embed_id FROM json_each(?)) AS ids ON n.embed_id = ids.embed_id
ORDER BY
  CASE
    WHEN ? != "" AND ? IS TRUE THEN json_extract(n.attributes, '$.' || ?) ELSE NULL
  END DESC,
  CASE
    WHEN ? != "" AND ? IS FALSE THEN json_extract(n.attributes, '$.' || ?) ELSE NULL
  END ASC;