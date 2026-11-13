-- generated TPC-H-schema test-only query (seed 23, #32, family setop); not an official TPC-H query
WITH s AS (SELECT o_custkey AS k FROM orders WHERE o_orderdate >= DATE '1993-01-01' AND o_orderdate < DATE '1996-01-01'
  INTERSECT
  SELECT c_custkey AS k FROM customer WHERE c_mktsegment = 'MACHINERY')
SELECT COUNT(*) AS m0, MIN(k) AS m1, MAX(k) AS m2, SUM(k % 1000) AS m3 FROM s
