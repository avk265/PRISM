-- generated TPC-H-schema training query (seed 11, #4, family scan_agg); not an official TPC-H query
SELECT l_shipmode AS sm, SUM(l_quantity) AS m0, SUM(l_extendedprice * (1 - l_discount) * (1 + l_tax)) AS m1, AVG(l_extendedprice) AS m2, SUM(l_extendedprice * l_discount) AS m3
FROM lineitem
WHERE l_shipmode IN ('MAIL', 'TRUCK')
GROUP BY l_shipmode
ORDER BY sm
