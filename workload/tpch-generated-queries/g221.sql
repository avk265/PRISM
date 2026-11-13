-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT n_name AS nation,
       s_name AS sname,
       COUNT(*) AS m0,
       COUNT(*) AS m1
FROM lineitem, supplier, nation, part
WHERE l_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND l_partkey = p_partkey
  AND p_brand = 'Brand#32'
GROUP BY n_name, s_name
ORDER BY m0 DESC, nation, sname
LIMIT 100
