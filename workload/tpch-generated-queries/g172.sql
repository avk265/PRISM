-- generated TPC-H-schema training query (seed 7, #172, family spj_agg); not an official TPC-H query
SELECT l_returnflag AS returnflag,
       s_name AS sname,
       COUNT(*) AS m0,
       COUNT(DISTINCT l_orderkey) AS m1,
       SUM(s_acctbal) AS m2
FROM lineitem, supplier
WHERE l_suppkey = s_suppkey
  AND l_returnflag = 'A'
  AND s_acctbal > -500
GROUP BY l_returnflag, s_name
ORDER BY m0 DESC, returnflag, sname
LIMIT 100
