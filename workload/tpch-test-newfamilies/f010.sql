-- generated TPC-H-schema test-only query (seed 23, #10, family setop); not an official TPC-H query
WITH s AS (SELECT l_partkey AS k FROM lineitem WHERE l_quantity < 5
  EXCEPT
  SELECT p_partkey AS k FROM part WHERE p_size IN (30, 36, 13, 49, 19))
SELECT COUNT(*) AS m0, MIN(k) AS m1, MAX(k) AS m2, SUM(k % 1000) AS m3 FROM s
