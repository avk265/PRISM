-- generated TPC-H-schema training query (seed 11, #6, family scan_agg); not an official TPC-H query
SELECT l_linestatus AS ls, COUNT(*) AS m0, SUM(l_quantity) AS m1
FROM lineitem
WHERE l_discount BETWEEN 0.0 AND 0.1
GROUP BY l_linestatus
ORDER BY ls
