-- generated TPC-H-schema test-only query (seed 23, #19, family setop); not an official TPC-H query
WITH s AS (SELECT l_partkey AS k FROM lineitem WHERE l_receiptdate > l_commitdate
  EXCEPT
  SELECT p_partkey AS k FROM part WHERE p_type LIKE '%BRASS')
SELECT COUNT(*) AS m0, MIN(k) AS m1, MAX(k) AS m2, SUM(k % 1000) AS m3 FROM s
