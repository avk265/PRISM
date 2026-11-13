-- generated TPC-H-schema training query (seed 7, #25, family semi_anti); not an official TPC-H query
SELECT p_brand AS brand, COUNT(*) AS m0, AVG(p_retailprice) AS m1
FROM part
WHERE p_brand = 'Brand#15'
  AND EXISTS (SELECT 1 FROM lineitem WHERE l_partkey = p_partkey AND l_discount BETWEEN 0.02 AND 0.06)
GROUP BY p_brand
ORDER BY m0 DESC, brand
LIMIT 100
