-- generated TPC-H-schema training query (seed 7, #341, family spj_agg); not an official TPC-H query
SELECT l_linestatus AS linestatus,
       l_suppkey AS suppkey,
       year(l_shipdate) AS ship_year,
       COUNT(DISTINCT l_orderkey) AS m0,
       SUM(ps_supplycost * ps_availqty) AS m1
FROM lineitem, supplier, partsupp
WHERE l_suppkey = s_suppkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_supplycost < 500
  AND l_receiptdate > l_commitdate
  AND s_acctbal > -500
GROUP BY l_linestatus, l_suppkey, year(l_shipdate)
ORDER BY m0 DESC, linestatus, suppkey, ship_year
LIMIT 100
