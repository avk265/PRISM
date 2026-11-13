-- generated TPC-H-schema training query (seed 7, #342, family spj_agg); not an official TPC-H query
SELECT o_orderstatus AS orderstatus,
       year(l_shipdate) AS ship_year,
       l_suppkey AS suppkey,
       SUM(l_extendedprice * (1 - l_discount)) AS m0,
       SUM(ps_supplycost * ps_availqty) AS m1,
       MIN(ps_supplycost) AS m2
FROM lineitem, partsupp, part, orders
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_partkey = p_partkey
  AND l_orderkey = o_orderkey
  AND ps_availqty > 9000
  AND l_quantity < 25
GROUP BY o_orderstatus, year(l_shipdate), l_suppkey
ORDER BY m0 DESC, orderstatus, ship_year, suppkey
LIMIT 100
