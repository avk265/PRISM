-- generated TPC-H-schema training query (seed 7, #350, family spj_agg); not an official TPC-H query
SELECT o_custkey AS custkey,
       o_orderpriority AS orderpriority,
       COUNT(*) AS m0,
       COUNT(DISTINCT o_custkey) AS m1,
       AVG(o_totalprice) AS m2
FROM customer, orders
WHERE o_custkey = c_custkey
  AND o_orderstatus = 'F'
GROUP BY o_custkey, o_orderpriority
ORDER BY m0 DESC, custkey, orderpriority
LIMIT 100
