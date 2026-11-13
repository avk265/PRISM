-- generated TPC-H-schema training query (seed 7, #107, family spj_agg); not an official TPC-H query
SELECT s_suppkey AS s_suppkey,
       l_linestatus AS linestatus,
       o_orderstatus AS orderstatus,
       AVG(o_totalprice) AS m0,
       COUNT(*) AS m1,
       SUM(l_quantity) AS m2
FROM lineitem, orders, customer, supplier, nation
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND l_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND n_name IN ('CHINA', 'PERU', 'KENYA')
  AND c_mktsegment = 'BUILDING'
GROUP BY s_suppkey, l_linestatus, o_orderstatus
ORDER BY m0 DESC, s_suppkey, linestatus, orderstatus
LIMIT 100
