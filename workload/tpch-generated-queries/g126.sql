-- generated TPC-H-schema training query (seed 7, #126, family small_tables); not an official TPC-H query
SELECT p_brand AS brand, p_size AS psize, COUNT(*) AS m0
FROM part
WHERE p_type LIKE '%STEEL'
  AND p_size IN (48, 26, 34, 15, 30)
GROUP BY p_brand, p_size
ORDER BY m0 DESC, brand, psize
LIMIT 100
