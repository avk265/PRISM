-- generated TPC-H-schema training query (seed 7, #207, family spj_agg); not an official TPC-H query
SELECT l_shipmode AS shipmode,
       MIN(ps_supplycost) AS m0,
       SUM(l_quantity) AS m1,
       SUM(l_extendedprice * (1 - l_discount)) AS m2
FROM lineitem, partsupp, supplier
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_suppkey = s_suppkey
GROUP BY l_shipmode
ORDER BY m0 DESC, shipmode
LIMIT 100
