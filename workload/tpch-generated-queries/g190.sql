-- generated TPC-H-schema training query (seed 7, #190, family spj_agg); not an official TPC-H query
SELECT year(l_shipdate) AS ship_year,
       ps_suppkey AS ps_suppkey,
       s_suppkey AS s_suppkey,
       MIN(ps_supplycost) AS m0
FROM lineitem, partsupp, supplier
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_suppkey = s_suppkey
  AND ps_availqty > 5000
  AND l_returnflag = 'N'
GROUP BY year(l_shipdate), ps_suppkey, s_suppkey
ORDER BY m0 DESC, ship_year, ps_suppkey, s_suppkey
LIMIT 100
