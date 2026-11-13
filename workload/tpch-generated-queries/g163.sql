-- generated TPC-H-schema training query (seed 7, #163, family spj_agg); not an official TPC-H query
SELECT c_custkey AS c_custkey,
       COUNT(*) AS m0
FROM orders, customer
WHERE o_custkey = c_custkey
  AND c_mktsegment = 'MACHINERY'
  AND o_orderkey IN (SELECT l_orderkey FROM lineitem GROUP BY l_orderkey HAVING SUM(l_quantity) > 250)
GROUP BY c_custkey
ORDER BY m0 DESC, c_custkey
LIMIT 100
