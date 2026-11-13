-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT p_size AS psize,
       ps_suppkey AS ps_suppkey,
       r_name AS region,
       MIN(ps_supplycost) AS m0,
       COUNT(*) AS m1,
       AVG(p_retailprice) AS m2
FROM partsupp, part, supplier, nation, region
WHERE ps_partkey = p_partkey
  AND ps_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND n_regionkey = r_regionkey
GROUP BY p_size, ps_suppkey, r_name
HAVING COUNT(*) > 20
ORDER BY m0 DESC, psize, ps_suppkey, region
LIMIT 100
