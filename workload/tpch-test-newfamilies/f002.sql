-- generated TPC-H-schema test-only query (seed 23, #2, family string); not an official TPC-H query
SELECT year(l_shipdate) AS yr, SUM(l_extendedprice * (1 - l_discount)) AS m0, COUNT(*) AS m1
FROM lineitem, part
WHERE l_partkey = p_partkey
  AND p_name LIKE '%lace%'
GROUP BY year(l_shipdate)
ORDER BY yr
