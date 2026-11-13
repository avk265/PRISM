-- generated TPC-H-schema training query (seed 7, #125, family cte); not an official TPC-H query
WITH big AS (SELECT l_orderkey AS ok FROM lineitem GROUP BY l_orderkey HAVING SUM(l_quantity) > 300)
SELECT o_orderpriority AS orderpriority, COUNT(*) AS m0, SUM(o_totalprice) AS m1
FROM orders, big
WHERE o_orderkey = big.ok
GROUP BY o_orderpriority
ORDER BY m0 DESC, orderpriority
