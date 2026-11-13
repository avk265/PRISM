-- generated TPC-H-schema training query (seed 11, #71, family scan_agg); not an official TPC-H query
SELECT year(l_shipdate) AS yr, COUNT(*) AS m0
FROM lineitem
WHERE l_receiptdate > l_commitdate
  AND l_quantity < 5
  AND l_shipdate >= DATE '1992-01-01' AND l_shipdate < DATE '1997-01-01'
GROUP BY year(l_shipdate)
ORDER BY yr
