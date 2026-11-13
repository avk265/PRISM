-- generated TPC-H-schema training query (seed 11, #18, family wide_agg); not an official TPC-H query
WITH g AS (SELECT l_partkey, l_suppkey, SUM(l_quantity) AS q, COUNT(*) AS c FROM lineitem
WHERE l_receiptdate > l_commitdate
  AND l_returnflag = 'A' GROUP BY l_partkey, l_suppkey HAVING SUM(l_quantity) > 50)
SELECT COUNT(*) AS m0, SUM(q) AS m1, MAX(c) AS m2 FROM g
