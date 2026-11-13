-- generated TPC-H-schema training query (seed 7, #35, family spj_agg); not an official TPC-H query
SELECT ps_suppkey AS ps_suppkey,
       l_suppkey AS suppkey,
       AVG(l_discount) AS m0
FROM orders, lineitem, supplier, partsupp
WHERE l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND o_orderstatus = 'O'
GROUP BY ps_suppkey, l_suppkey
ORDER BY m0 DESC, ps_suppkey, suppkey
LIMIT 100
