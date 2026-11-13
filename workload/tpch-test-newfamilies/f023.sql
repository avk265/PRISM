-- generated TPC-H-schema test-only query (seed 23, #23, family string); not an official TPC-H query
SELECT o_orderpriority AS op, COUNT(*) AS m0, SUM(o_totalprice) AS m1
FROM orders
WHERE o_comment NOT LIKE '%express%requests%'
  AND o_orderstatus = 'O'
GROUP BY o_orderpriority
ORDER BY op
