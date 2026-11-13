-- generated TPC-H-schema training query (seed 11, #19, family scan_agg); not an official TPC-H query
SELECT l_shipmode AS sm, SUM(l_extendedprice * (1 - l_discount) * (1 + l_tax)) AS m0, SUM(l_quantity) AS m1, COUNT(*) AS m2, AVG(l_extendedprice) AS m3
FROM lineitem
WHERE l_discount BETWEEN 0.05 AND 0.1
  AND l_quantity < 15
GROUP BY l_shipmode
ORDER BY sm
