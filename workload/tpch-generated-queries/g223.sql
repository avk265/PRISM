-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT s_suppkey AS s_suppkey,
       p_partkey AS partkey,
       p_size AS psize,
       COUNT(*) AS m0
FROM partsupp, part, supplier, nation
WHERE ps_partkey = p_partkey
  AND ps_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND n_name IN ('KENYA', 'UNITED STATES')
  AND ps_availqty > 5000
  AND p_container LIKE 'WRAP%'
GROUP BY s_suppkey, p_partkey, p_size
ORDER BY m0 DESC, s_suppkey, partkey, psize
LIMIT 100
