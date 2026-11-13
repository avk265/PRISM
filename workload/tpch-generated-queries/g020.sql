-- generated TPC-H-schema training query (seed 7, #20, family spj_agg); not an official TPC-H query
SELECT l_suppkey AS suppkey,
       l_returnflag AS returnflag,
       COUNT(DISTINCT l_orderkey) AS m0,
       SUM(l_extendedprice * (1 - l_discount)) AS m1,
       COUNT(*) AS m2
FROM lineitem
WHERE l_receiptdate > l_commitdate
  AND l_partkey IN (SELECT p_partkey FROM part WHERE p_size < 15)
GROUP BY l_suppkey, l_returnflag
ORDER BY m0 DESC, suppkey, returnflag
LIMIT 100
