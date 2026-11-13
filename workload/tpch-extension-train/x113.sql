-- generated TPC-H-schema training query (seed 11, #113, family scan_agg); not an official TPC-H query
SELECT l_shipmode AS sm, l_linestatus AS ls, AVG(l_extendedprice) AS m0
FROM lineitem
WHERE l_receiptdate > l_commitdate
  AND l_quantity < 15
  AND l_shipdate >= DATE '1993-01-01' AND l_shipdate < DATE '1999-01-01'
GROUP BY l_shipmode, l_linestatus
ORDER BY sm, ls
