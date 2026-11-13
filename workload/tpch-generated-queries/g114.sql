-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT year(l_shipdate) AS ship_year,
       SUM(l_extendedprice * (1 - l_discount)) AS m0
FROM lineitem
WHERE l_shipmode IN ('AIR', 'SHIP')
  AND l_partkey IN (SELECT p_partkey FROM part WHERE p_size < 15)
GROUP BY year(l_shipdate)
ORDER BY m0 DESC, ship_year
LIMIT 100
