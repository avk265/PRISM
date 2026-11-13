-- generated TPC-H-schema training query (seed 7, #188, family semi_anti); not an official TPC-H query
SELECT o_orderpriority AS orderpriority, COUNT(*) AS m0, SUM(o_totalprice) AS m1
FROM orders
WHERE o_orderpriority IN ('3-MEDIUM')
  AND EXISTS (SELECT 1 FROM lineitem WHERE l_orderkey = o_orderkey AND l_discount BETWEEN 0.0 AND 0.1)
GROUP BY o_orderpriority
ORDER BY m0 DESC, orderpriority
