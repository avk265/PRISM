-- generated TPC-H-schema training query (seed 7, #23, family spj_agg); not an official TPC-H query
SELECT l_shipmode AS shipmode,
       o_orderpriority AS orderpriority,
       COUNT(*) AS m0,
       COUNT(DISTINCT l_orderkey) AS m1
FROM lineitem, orders, supplier
WHERE l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
GROUP BY l_shipmode, o_orderpriority
ORDER BY m0 DESC, shipmode, orderpriority
LIMIT 100
