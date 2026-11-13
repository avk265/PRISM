-- generated TPC-H-schema training query (seed 7, #306, family spj_agg); not an official TPC-H query
SELECT p_type AS ptype,
       p_partkey AS partkey,
       AVG(o_totalprice) AS m0,
       SUM(l_extendedprice * (1 - l_discount)) AS m1
FROM lineitem, part, orders, partsupp
WHERE l_partkey = p_partkey
  AND l_orderkey = o_orderkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND o_totalprice > 300000
  AND l_discount BETWEEN 0.05 AND 0.08
GROUP BY p_type, p_partkey
ORDER BY m0 DESC, ptype, partkey
LIMIT 100
