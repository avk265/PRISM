-- generated TPC-H-schema training query (seed 7, #24, family spj_agg); not an official TPC-H query
SELECT year(l_shipdate) AS ship_year,
       l_suppkey AS suppkey,
       AVG(p_retailprice) AS m0
FROM lineitem, part
WHERE l_partkey = p_partkey
  AND p_container LIKE 'JUMBO%'
  AND l_returnflag = 'R'
GROUP BY year(l_shipdate), l_suppkey
ORDER BY m0 DESC, ship_year, suppkey
LIMIT 100
