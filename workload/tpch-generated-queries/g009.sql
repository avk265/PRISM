-- generated TPC-H-schema training query (seed 7, #9, family spj_agg); not an official TPC-H query
SELECT p_brand AS brand,
       p_partkey AS partkey,
       l_suppkey AS suppkey,
       COUNT(*) AS m0,
       COUNT(*) AS m1,
       AVG(p_retailprice) AS m2
FROM partsupp, part, lineitem
WHERE ps_partkey = p_partkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_discount BETWEEN 0.0 AND 0.1
  AND p_brand = 'Brand#41'
  AND ps_supplycost < 50
GROUP BY p_brand, p_partkey, l_suppkey
ORDER BY m0 DESC, brand, partkey, suppkey
LIMIT 100
