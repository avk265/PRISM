-- generated TPC-H-schema training query (seed 11, #31, family scan_agg); not an official TPC-H query
SELECT l_shipmode AS sm, SUM(l_extendedprice * l_discount) AS m0, AVG(l_extendedprice) AS m1, SUM(l_extendedprice * (1 - l_discount) * (1 + l_tax)) AS m2
FROM lineitem
WHERE l_receiptdate > l_commitdate
  AND l_shipdate >= DATE '1993-01-01' AND l_shipdate < DATE '1999-01-01'
  AND l_quantity < 5
GROUP BY l_shipmode
ORDER BY sm
