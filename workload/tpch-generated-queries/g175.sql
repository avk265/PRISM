-- generated TPC-H-schema training query (seed 7, #175, family spj_agg); not an official TPC-H query
SELECT l_shipmode AS shipmode,
       year(l_shipdate) AS ship_year,
       ps_suppkey AS ps_suppkey,
       SUM(l_quantity) AS m0
FROM lineitem, part, partsupp, supplier
WHERE l_partkey = p_partkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_suppkey = s_suppkey
  AND p_brand = 'Brand#52'
GROUP BY l_shipmode, year(l_shipdate), ps_suppkey
ORDER BY m0 DESC, shipmode, ship_year, ps_suppkey
LIMIT 100
