-- generated TPC-H-schema training query (seed 7, #285, family semi_anti); not an official TPC-H query
SELECT p_brand AS brand, COUNT(*) AS m0, AVG(p_retailprice) AS m1
FROM part
WHERE p_brand = 'Brand#12'
  AND EXISTS (SELECT 1 FROM lineitem WHERE l_partkey = p_partkey AND l_returnflag = 'A')
GROUP BY p_brand
ORDER BY m0 DESC, brand
LIMIT 100
