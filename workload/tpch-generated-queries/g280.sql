-- generated TPC-H-schema training query (seed 7, #280, family spj_agg); not an official TPC-H query
SELECT l_linestatus AS linestatus,
       l_returnflag AS returnflag,
       AVG(l_discount) AS m0,
       COUNT(*) AS m1,
       SUM(l_extendedprice * (1 - l_discount)) AS m2
FROM lineitem
WHERE l_receiptdate > l_commitdate
GROUP BY l_linestatus, l_returnflag
ORDER BY m0 DESC, linestatus, returnflag
LIMIT 100
