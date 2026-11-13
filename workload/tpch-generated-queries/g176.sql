-- generated TPC-H-schema training query (seed 7, #176, family spj_agg); not an official TPC-H query
SELECT p_size AS psize,
       l_shipmode AS shipmode,
       COUNT(DISTINCT l_orderkey) AS m0,
       SUM(l_quantity) AS m1,
       COUNT(*) AS m2
FROM lineitem, part
WHERE l_partkey = p_partkey
  AND l_shipdate >= DATE '1997-01-01' AND l_shipdate < DATE '1999-01-01'
  AND p_size IN (22, 19, 41, 32, 6, 1)
GROUP BY p_size, l_shipmode
HAVING COUNT(*) > 20
ORDER BY m0 DESC, psize, shipmode
LIMIT 100
