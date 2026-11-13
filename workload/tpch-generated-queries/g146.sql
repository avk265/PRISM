-- generated TPC-H-schema training query (seed 7, #146, family subquery); not an official TPC-H query
SELECT p_partkey AS partkey, s_suppkey AS suppkey, ps_supplycost AS m0
FROM part, partsupp, supplier
WHERE p_partkey = ps_partkey
  AND s_suppkey = ps_suppkey
  AND p_brand = 'Brand#13'
  AND p_container LIKE 'SM%'
  AND ps_supplycost = (SELECT MIN(ps2.ps_supplycost) FROM partsupp ps2 WHERE ps2.ps_partkey = p_partkey)
ORDER BY m0, partkey, suppkey
LIMIT 100
