-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT l_returnflag AS returnflag,
       COUNT(*) AS m0,
       AVG(l_discount) AS m1
FROM lineitem, partsupp, supplier
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_suppkey = s_suppkey
  AND l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1993-01-01'
  AND s_acctbal > 0
GROUP BY l_returnflag
ORDER BY m0 DESC, returnflag
LIMIT 100
