-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT l_returnflag AS returnflag,
       COUNT(*) AS m0,
       MAX(l_extendedprice) AS m1,
       SUM(l_quantity) AS m2
FROM lineitem
WHERE l_returnflag = 'R'
GROUP BY l_returnflag
HAVING COUNT(*) > 1
ORDER BY m0 DESC, returnflag
LIMIT 100
