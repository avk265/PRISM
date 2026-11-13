-- generated TPC-H-schema training query (seed 7, #360, family semi_anti); not an official TPC-H query
SELECT c_mktsegment AS mktsegment, COUNT(*) AS m0, SUM(c_acctbal) AS m1
FROM customer
WHERE c_mktsegment = 'BUILDING'
  AND NOT EXISTS (SELECT 1 FROM orders WHERE o_custkey = c_custkey AND o_totalprice > 150000)
GROUP BY c_mktsegment
ORDER BY m0 DESC, mktsegment
