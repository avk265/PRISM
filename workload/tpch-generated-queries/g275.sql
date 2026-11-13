-- generated TPC-H-schema training query (seed 7, #275, family spj_agg); not an official TPC-H query
SELECT l_returnflag AS returnflag,
       year(l_shipdate) AS ship_year,
       l_suppkey AS suppkey,
       COUNT(DISTINCT l_orderkey) AS m0
FROM lineitem, partsupp, part, supplier, orders, nation, region
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_partkey = p_partkey
  AND ps_suppkey = s_suppkey
  AND l_orderkey = o_orderkey
  AND s_nationkey = n_nationkey
  AND n_regionkey = r_regionkey
  AND l_quantity < 40
  AND s_acctbal > 0
GROUP BY l_returnflag, year(l_shipdate), l_suppkey
ORDER BY m0 DESC, returnflag, ship_year, suppkey
LIMIT 100
