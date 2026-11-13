-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT year(l_shipdate) AS ship_year,
       s_suppkey AS s_suppkey,
       COUNT(*) AS m0,
       SUM(o_totalprice) AS m1,
       SUM(ps_supplycost * ps_availqty) AS m2
FROM lineitem, partsupp, part, orders, supplier, nation, region
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_partkey = p_partkey
  AND l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND n_regionkey = r_regionkey
GROUP BY year(l_shipdate), s_suppkey
ORDER BY m0 DESC, ship_year, s_suppkey
LIMIT 100
