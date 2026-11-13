-- generated TPC-H-schema training query (seed 11, #111, family scan_agg); not an official TPC-H query
SELECT l_shipmode AS sm, COUNT(*) AS m0, SUM(l_quantity) AS m1, SUM(l_extendedprice * (1 - l_discount) * (1 + l_tax)) AS m2
FROM lineitem
WHERE l_returnflag = 'A'
  AND l_quantity < 5
  AND l_discount BETWEEN 0.05 AND 0.1
GROUP BY l_shipmode
ORDER BY sm
