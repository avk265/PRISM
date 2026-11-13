-- generated TPC-H-schema training query (seed 7, #36, family spj_agg); not an official TPC-H query
SELECT c_mktsegment AS mktsegment,
       AVG(o_totalprice) AS m0
FROM orders, lineitem, part, customer
WHERE l_orderkey = o_orderkey
  AND l_partkey = p_partkey
  AND o_custkey = c_custkey
  AND l_returnflag = 'N'
  AND c_acctbal > 8000
GROUP BY c_mktsegment
ORDER BY m0 DESC, mktsegment
LIMIT 100
