-- generated TPC-H-schema training query (seed 11, #115, family scan_agg); not an official TPC-H query
SELECT l_shipmode AS sm, SUM(l_quantity) AS m0, SUM(l_extendedprice * l_discount) AS m1
FROM lineitem
WHERE l_discount BETWEEN 0.05 AND 0.08
GROUP BY l_shipmode
ORDER BY sm
