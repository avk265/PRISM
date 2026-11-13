-- generated TPC-H-schema test-only query (seed 23, #20, family setop); not an official TPC-H query
WITH s AS (SELECT l_partkey AS k FROM lineitem WHERE l_shipdate >= DATE '1993-01-01' AND l_shipdate < DATE '1999-01-01'
  EXCEPT
  SELECT p_partkey AS k FROM part WHERE p_brand = 'Brand#12')
SELECT COUNT(*) AS m0, MIN(k) AS m1, MAX(k) AS m2, SUM(k % 1000) AS m3 FROM s
