-- generated TPC-H-schema training query (seed 7, #250, family spj_agg); not an official TPC-H query
SELECT p_partkey AS partkey,
       COUNT(*) AS m0,
       SUM(o_totalprice) AS m1,
       COUNT(DISTINCT o_custkey) AS m2
FROM orders, lineitem, part
WHERE l_orderkey = o_orderkey
  AND l_partkey = p_partkey
  AND p_container LIKE 'SM%'
  AND l_shipmode IN ('MAIL', 'AIR', 'TRUCK')
GROUP BY p_partkey
ORDER BY m0 DESC, partkey
LIMIT 100
