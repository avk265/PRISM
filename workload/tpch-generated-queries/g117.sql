-- generated TPC-H-schema training query (seed 7, #117, family subquery); not an official TPC-H query
SELECT l_returnflag AS returnflag, COUNT(*) AS m0, SUM(l_extendedprice) AS m1
FROM lineitem
WHERE l_returnflag = 'R'
  AND l_extendedprice > (SELECT 1.0 * AVG(l_extendedprice) FROM lineitem)
GROUP BY l_returnflag
ORDER BY m0 DESC, returnflag
