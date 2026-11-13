-- generated TPC-H-schema training query (seed 11, #34, family scan_agg); not an official TPC-H query
SELECT year(l_shipdate) AS yr, COUNT(*) AS m0, SUM(l_extendedprice * (1 - l_discount) * (1 + l_tax)) AS m1
FROM lineitem
WHERE l_quantity < 25
GROUP BY year(l_shipdate)
ORDER BY yr
