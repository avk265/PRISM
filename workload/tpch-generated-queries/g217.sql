-- generated TPC-H-schema training query (seed 7, #217, family spj_agg); not an official TPC-H query
SELECT p_type AS ptype,
       COUNT(*) AS m0,
       MAX(l_extendedprice) AS m1
FROM lineitem, partsupp, supplier, part
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_suppkey = s_suppkey
  AND l_partkey = p_partkey
  AND p_brand = 'Brand#24'
  AND s_acctbal > 5000
GROUP BY p_type
ORDER BY m0 DESC, ptype
LIMIT 100
