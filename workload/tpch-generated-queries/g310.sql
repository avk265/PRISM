-- generated TPC-H-schema training query (seed 7, #310, family spj_agg); not an official TPC-H query
SELECT l_suppkey AS suppkey,
       SUM(l_quantity) AS m0
FROM lineitem
WHERE l_quantity < 25
GROUP BY l_suppkey
ORDER BY m0 DESC, suppkey
LIMIT 100
