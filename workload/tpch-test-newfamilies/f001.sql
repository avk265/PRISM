-- generated TPC-H-schema test-only query (seed 23, #1, family setop); not an official TPC-H query
WITH s AS (SELECT l_orderkey AS k FROM lineitem WHERE l_receiptdate > l_commitdate
  EXCEPT
  SELECT o_orderkey AS k FROM orders WHERE o_orderpriority IN ('2-HIGH'))
SELECT COUNT(*) AS m0, MIN(k) AS m1, MAX(k) AS m2, SUM(k % 1000) AS m3 FROM s
