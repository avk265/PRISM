-- generated TPC-H-schema training query (seed 11, #12, family scan_agg); not an official TPC-H query
SELECT l_linestatus AS ls, SUM(l_extendedprice * l_discount) AS m0
FROM lineitem
WHERE l_discount BETWEEN 0.0 AND 0.08
GROUP BY l_linestatus
ORDER BY ls
