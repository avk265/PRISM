-- generated TPC-H-schema training query (seed 7, #204, family spj_agg); not an official TPC-H query
SELECT l_linestatus AS linestatus,
       l_returnflag AS returnflag,
       SUM(l_quantity) AS m0,
       AVG(l_discount) AS m1,
       COUNT(DISTINCT l_orderkey) AS m2
FROM lineitem, supplier
WHERE l_suppkey = s_suppkey
  AND s_acctbal > 5000
  AND l_quantity < 15
GROUP BY l_linestatus, l_returnflag
HAVING COUNT(*) > 5
ORDER BY m0 DESC, linestatus, returnflag
LIMIT 100
