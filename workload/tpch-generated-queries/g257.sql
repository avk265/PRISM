-- generated TPC-H-schema training query (seed 7, #257, family spj_agg); not an official TPC-H query
SELECT s_name AS sname,
       year(o_orderdate) AS order_year,
       MAX(l_extendedprice) AS m0,
       AVG(l_discount) AS m1
FROM lineitem, partsupp, supplier, orders, nation, customer
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_suppkey = s_suppkey
  AND l_orderkey = o_orderkey
  AND s_nationkey = n_nationkey
  AND o_custkey = c_custkey
  AND n_name IN ('BRAZIL', 'PERU', 'GERMANY')
  AND s_acctbal > 5000
  AND ps_supplycost < 900
GROUP BY s_name, year(o_orderdate)
ORDER BY m0 DESC, sname, order_year
LIMIT 100
