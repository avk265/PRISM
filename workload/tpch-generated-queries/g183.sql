-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT p_partkey AS partkey,
       p_brand AS brand,
       COUNT(*) AS m0,
       AVG(p_retailprice) AS m1
FROM part
WHERE p_type LIKE '%STEEL'
GROUP BY p_partkey, p_brand
ORDER BY m0 DESC, partkey, brand
LIMIT 100
