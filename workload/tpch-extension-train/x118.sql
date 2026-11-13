-- generated TPC-H-schema training query (seed 11, #118, family scan_agg); not an official TPC-H query
SELECT l_linestatus AS ls, year(l_shipdate) AS yr, AVG(l_extendedprice) AS m0, SUM(l_quantity) AS m1
FROM lineitem
WHERE l_shipdate >= DATE '1996-01-01' AND l_shipdate < DATE '1999-01-01'
  AND l_quantity < 5
GROUP BY l_linestatus, year(l_shipdate)
ORDER BY ls, yr
