-- generated TPC-H-schema training query (seed 7, #33, family spj_agg); not an official TPC-H query
SELECT l_suppkey AS suppkey,
       COUNT(*) AS m0,
       AVG(p_retailprice) AS m1
FROM lineitem, partsupp, supplier, part
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_suppkey = s_suppkey
  AND l_partkey = p_partkey
  AND p_brand = 'Brand#24'
  AND l_returnflag = 'A'
GROUP BY l_suppkey
ORDER BY m0 DESC, suppkey
LIMIT 100
