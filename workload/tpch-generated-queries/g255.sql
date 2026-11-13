-- generated TPC-H-schema training query (seed 7, #255, family spj_agg); not an official TPC-H query
SELECT n_name AS nation,
       SUM(ps_supplycost * ps_availqty) AS m0,
       MIN(ps_supplycost) AS m1
FROM lineitem, orders, supplier, partsupp, nation
WHERE l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND s_nationkey = n_nationkey
  AND s_acctbal > 0
  AND l_shipmode IN ('FOB', 'MAIL')
  AND n_name IN ('UNITED STATES', 'GERMANY')
GROUP BY n_name
HAVING COUNT(*) > 1
ORDER BY m0 DESC, nation
LIMIT 100
