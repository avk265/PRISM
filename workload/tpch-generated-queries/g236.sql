-- generated TPC-H-schema training query (seed 7, #236, family case); not an official TPC-H query
SELECT year(l_shipdate) AS ship_year,
       SUM(CASE WHEN p_type LIKE 'PROMO%' THEN l_extendedprice * (1 - l_discount) ELSE 0 END) AS m0,
       SUM(l_extendedprice * (1 - l_discount)) AS m1
FROM lineitem, part
WHERE l_partkey = p_partkey
  AND l_shipdate >= DATE '1993-01-01' AND l_shipdate < DATE '1999-01-01'
GROUP BY year(l_shipdate)
ORDER BY ship_year
