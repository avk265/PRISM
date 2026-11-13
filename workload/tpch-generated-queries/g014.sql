-- generated TPC-H-schema training query (seed 7, #14, family union); not an official TPC-H query
WITH u AS (
  SELECT l_returnflag AS f, l_extendedprice AS v FROM lineitem WHERE l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1997-01-01'
  UNION ALL
  SELECT l_returnflag AS f, l_extendedprice AS v FROM lineitem WHERE l_discount BETWEEN 0.05 AND 0.08)
SELECT f AS returnflag, COUNT(*) AS m0, SUM(v) AS m1
FROM u
GROUP BY f
ORDER BY m0 DESC, returnflag
