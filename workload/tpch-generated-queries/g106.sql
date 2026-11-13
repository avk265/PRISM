-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT o_custkey AS custkey,
       o_orderpriority AS orderpriority,
       COUNT(*) AS m0,
       COUNT(DISTINCT o_custkey) AS m1
FROM orders
WHERE o_orderstatus = 'O'
  AND o_orderkey IN (SELECT l_orderkey FROM lineitem GROUP BY l_orderkey HAVING SUM(l_quantity) > 150)
GROUP BY o_custkey, o_orderpriority
ORDER BY m0 DESC, custkey, orderpriority
LIMIT 100
