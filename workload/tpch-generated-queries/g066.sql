-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT p_partkey AS partkey,
       s_name AS sname,
       AVG(p_retailprice) AS m0,
       COUNT(*) AS m1,
       COUNT(*) AS m2
FROM partsupp, part, supplier, nation, region
WHERE ps_partkey = p_partkey
  AND ps_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND n_regionkey = r_regionkey
  AND n_name IN ('CHINA', 'FRANCE', 'UNITED STATES')
  AND p_container LIKE 'LG%'
GROUP BY p_partkey, s_name
ORDER BY m0 DESC, partkey, sname
LIMIT 100
