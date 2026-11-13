-- generated TPC-H-schema training query (seed 7, #123, family subquery); not an official TPC-H query
SELECT o_orderpriority AS orderpriority, COUNT(*) AS m0
FROM orders
WHERE o_orderdate >= DATE '1994-09-01' AND o_orderdate < DATE '1997-01-01'
  AND o_totalprice > (SELECT 1.5 * AVG(o_totalprice) FROM orders)
GROUP BY o_orderpriority
ORDER BY m0 DESC, orderpriority
