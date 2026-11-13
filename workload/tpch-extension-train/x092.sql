-- generated TPC-H-schema training query (seed 11, #92, family scan_agg); not an official TPC-H query
SELECT l_shipmode AS sm, SUM(l_quantity) AS m0, AVG(l_extendedprice) AS m1, SUM(l_extendedprice * (1 - l_discount) * (1 + l_tax)) AS m2, COUNT(*) AS m3
FROM lineitem
WHERE l_shipmode IN ('TRUCK', 'REG AIR', 'SHIP', 'RAIL')
GROUP BY l_shipmode
ORDER BY sm
