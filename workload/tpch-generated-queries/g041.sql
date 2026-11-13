-- generated TPC-H-schema training query (seed 7, #41, family subquery); not an official TPC-H query
SELECT l_returnflag AS returnflag, COUNT(*) AS m0, SUM(l_extendedprice) AS m1
FROM lineitem
WHERE l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1995-01-01'
  AND l_extendedprice > (SELECT 2.0 * AVG(l_extendedprice) FROM lineitem)
GROUP BY l_returnflag
ORDER BY m0 DESC, returnflag
