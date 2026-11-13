-- generated TPC-H-schema training query (seed 11, #68, family scan_agg); not an official TPC-H query
SELECT l_linestatus AS ls, SUM(l_extendedprice * l_discount) AS m0
FROM lineitem
WHERE l_quantity < 5
  AND l_shipdate >= DATE '1997-01-01' AND l_shipdate < DATE '1999-01-01'
GROUP BY l_linestatus
ORDER BY ls
