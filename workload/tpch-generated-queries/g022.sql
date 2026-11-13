-- generated TPC-H-schema training query (seed 7, #22, family union); not an official TPC-H query
WITH u AS (
  SELECT l_returnflag AS f, l_extendedprice AS v FROM lineitem WHERE l_returnflag = 'R'
  UNION ALL
  SELECT l_returnflag AS f, l_extendedprice AS v FROM lineitem WHERE l_receiptdate > l_commitdate)
SELECT f AS returnflag, COUNT(*) AS m0, SUM(v) AS m1
FROM u
GROUP BY f
ORDER BY m0 DESC, returnflag
