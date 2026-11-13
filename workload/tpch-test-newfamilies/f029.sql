-- generated TPC-H-schema test-only query (seed 23, #29, family string); not an official TPC-H query
SELECT o_orderpriority AS op, COUNT(*) AS m0, SUM(o_totalprice) AS m1
FROM orders
WHERE o_comment NOT LIKE '%special%deposits%'
  AND o_orderdate >= DATE '1995-02-01' AND o_orderdate < DATE '1997-01-01'
GROUP BY o_orderpriority
ORDER BY op
