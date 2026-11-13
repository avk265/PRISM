-- generated TPC-H-schema training query (seed 7, #155, family spj_agg); not an official TPC-H query
SELECT l_suppkey AS suppkey,
       SUM(l_extendedprice * (1 - l_discount)) AS m0,
       COUNT(*) AS m1,
       COUNT(*) AS m2
FROM lineitem, part
WHERE l_partkey = p_partkey
  AND p_size IN (25, 13, 47, 15, 20, 39, 4, 26)
  AND l_returnflag = 'N'
GROUP BY l_suppkey
ORDER BY m0 DESC, suppkey
LIMIT 100
