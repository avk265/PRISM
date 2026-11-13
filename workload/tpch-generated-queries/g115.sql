-- generated TPC-H-schema training query (seed 7, #115, family spj_agg); not an official TPC-H query
SELECT l_shipmode AS shipmode,
       SUM(l_extendedprice * (1 - l_discount)) AS m0
FROM part, lineitem
WHERE l_partkey = p_partkey
GROUP BY l_shipmode
ORDER BY m0 DESC, shipmode
LIMIT 100
