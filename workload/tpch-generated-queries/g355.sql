-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT l_returnflag AS returnflag,
       AVG(l_discount) AS m0
FROM lineitem, partsupp
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_shipdate >= DATE '1997-01-01' AND l_shipdate < DATE '1995-01-01'
GROUP BY l_returnflag
ORDER BY m0 DESC, returnflag
LIMIT 100
