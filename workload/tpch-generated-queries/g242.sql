-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT l_returnflag AS returnflag,
       SUM(s_acctbal) AS m0,
       COUNT(*) AS m1,
       SUM(l_quantity) AS m2
FROM lineitem, supplier
WHERE l_suppkey = s_suppkey
  AND l_partkey IN (SELECT p_partkey FROM part WHERE p_size < 5)
GROUP BY l_returnflag
HAVING COUNT(*) > 20
ORDER BY m0 DESC, returnflag
LIMIT 100
