-- generated TPC-H-schema training query (seed 11, #61, family scan_agg); not an official TPC-H query
SELECT l_shipmode AS sm, COUNT(*) AS m0, SUM(l_extendedprice * l_discount) AS m1, AVG(l_extendedprice) AS m2, SUM(l_quantity) AS m3
FROM lineitem
WHERE l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1997-01-01'
GROUP BY l_shipmode
ORDER BY sm
