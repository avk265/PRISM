-- generated TPC-H-schema training query (seed 7, #353, family spj_agg); not an official TPC-H query
SELECT c_mktsegment AS mktsegment,
       AVG(p_retailprice) AS m0
FROM lineitem, orders, partsupp, part, supplier, customer, nation
WHERE l_orderkey = o_orderkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_partkey = p_partkey
  AND ps_suppkey = s_suppkey
  AND o_custkey = c_custkey
  AND s_nationkey = n_nationkey
  AND o_orderstatus = 'P'
  AND l_quantity < 40
GROUP BY c_mktsegment
HAVING COUNT(*) > 20
ORDER BY m0 DESC, mktsegment
LIMIT 100
