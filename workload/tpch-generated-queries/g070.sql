-- generated TPC-H-schema training query (seed 7, #70, family subquery); not an official TPC-H query
SELECT o_orderpriority AS orderpriority, COUNT(*) AS m0
FROM orders
WHERE o_orderpriority IN ('4-NOT SPECIFIED')
  AND o_totalprice > (SELECT 1.5 * AVG(o_totalprice) FROM orders)
GROUP BY o_orderpriority
ORDER BY m0 DESC, orderpriority
