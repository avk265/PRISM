-- generated TPC-H-schema training query (seed 7, #322, family semi_anti); not an official TPC-H query
SELECT p_brand AS brand, COUNT(*) AS m0, AVG(p_retailprice) AS m1
FROM part
WHERE p_size IN (16, 8)
  AND EXISTS (SELECT 1 FROM lineitem WHERE l_partkey = p_partkey AND l_discount BETWEEN 0.0 AND 0.08)
GROUP BY p_brand
ORDER BY m0 DESC, brand
LIMIT 100
