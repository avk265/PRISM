-- generated TPC-H-schema training query (seed 7, #309, family subquery); not an official TPC-H query
SELECT o_orderpriority AS orderpriority, COUNT(*) AS m0
FROM orders
WHERE o_orderdate >= DATE '1992-03-01' AND o_orderdate < DATE '1995-01-01'
  AND o_totalprice > (SELECT 2.0 * AVG(o_totalprice) FROM orders)
GROUP BY o_orderpriority
ORDER BY m0 DESC, orderpriority
