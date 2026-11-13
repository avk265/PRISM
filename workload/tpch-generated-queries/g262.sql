-- generated TPC-H-schema training query (seed 7, #262, family semi_anti); not an official TPC-H query
SELECT o_orderpriority AS orderpriority, COUNT(*) AS m0, SUM(o_totalprice) AS m1
FROM orders
WHERE o_orderpriority IN ('2-HIGH')
  AND NOT EXISTS (SELECT 1 FROM lineitem WHERE l_orderkey = o_orderkey AND l_shipmode IN ('MAIL'))
GROUP BY o_orderpriority
ORDER BY m0 DESC, orderpriority
