-- generated TPC-H-schema training query (seed 7, #72, family subquery); not an official TPC-H query
SELECT o_orderpriority AS orderpriority, COUNT(*) AS m0
FROM orders
WHERE o_orderpriority IN ('2-HIGH', '1-URGENT', '5-LOW')
  AND o_totalprice > (SELECT 2.0 * AVG(o_totalprice) FROM orders)
GROUP BY o_orderpriority
ORDER BY m0 DESC, orderpriority
