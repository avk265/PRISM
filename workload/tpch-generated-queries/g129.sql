-- generated TPC-H-schema training query (seed 7, #129, family spj_agg); not an official TPC-H query
SELECT c_custkey AS c_custkey,
       l_linestatus AS linestatus,
       MIN(ps_supplycost) AS m0,
       SUM(o_totalprice) AS m1,
       COUNT(*) AS m2
FROM partsupp, part, lineitem, orders, customer
WHERE ps_partkey = p_partkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND l_quantity < 40
  AND o_orderdate >= DATE '1994-06-01' AND o_orderdate < DATE '1996-01-01'
  AND c_acctbal > 3000
GROUP BY c_custkey, l_linestatus
HAVING COUNT(*) > 20
ORDER BY m0 DESC, c_custkey, linestatus
LIMIT 100
