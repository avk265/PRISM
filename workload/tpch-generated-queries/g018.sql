-- generated TPC-H-schema training query (seed 7, #18, family spj_agg); not an official TPC-H query
SELECT l_shipmode AS shipmode,
       o_orderstatus AS orderstatus,
       l_returnflag AS returnflag,
       MAX(l_extendedprice) AS m0,
       SUM(o_totalprice) AS m1,
       COUNT(DISTINCT o_custkey) AS m2
FROM orders, lineitem
WHERE l_orderkey = o_orderkey
  AND l_quantity < 25
  AND o_orderpriority IN ('5-LOW')
  AND l_partkey IN (SELECT p_partkey FROM part WHERE p_size < 30)
GROUP BY l_shipmode, o_orderstatus, l_returnflag
ORDER BY m0 DESC, shipmode, orderstatus, returnflag
LIMIT 100
