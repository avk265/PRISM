-- generated TPC-H-schema test-only query (seed 23, #36, family string); not an official TPC-H query
SELECT o_orderpriority AS op, COUNT(*) AS m0, SUM(o_totalprice) AS m1
FROM orders
WHERE o_comment NOT LIKE '%pending%accounts%'
  AND o_orderpriority IN ('5-LOW', '3-MEDIUM', '2-HIGH')
GROUP BY o_orderpriority
ORDER BY op
