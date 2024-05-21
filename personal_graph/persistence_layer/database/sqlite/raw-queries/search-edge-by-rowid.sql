SELECT
  e.embed_id,
  e.source,
  e.target,
  e.label,
  e.attributes
FROM edges e
JOIN (SELECT value AS embed_id FROM json_each(?)) AS ids ON e.embed_id = ids.embed_id
ORDER BY
  CASE
    WHEN ? != "" AND ? IS TRUE THEN json_extract(e.attributes, '$.' || ?) ELSE NULL
  END DESC,
  CASE
    WHEN ? != "" AND ? IS FALSE THEN json_extract(e.attributes, '$.' || ?) ELSE NULL
  END ASC;