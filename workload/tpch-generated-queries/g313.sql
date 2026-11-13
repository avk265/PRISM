-- generated TPC-H-schema training query (seed 7, #313, family spj_agg); not an official TPC-H query
SELECT l_linestatus AS linestatus,
       AVG(l_discount) AS m0,
       COUNT(DISTINCT l_orderkey) AS m1,
       SUM(l_quantity) AS m2
FROM lineitem
WHERE l_quantity < 40
GROUP BY l_linestatus
ORDER BY m0 DESC, linestatus
LIMIT 100
