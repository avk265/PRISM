-- generated TPC-H-schema training query (seed 7, #294, family spj_agg); not an official TPC-H query
SELECT p_size AS psize,
       p_partkey AS partkey,
       COUNT(*) AS m0,
       AVG(p_retailprice) AS m1
FROM part, partsupp
WHERE ps_partkey = p_partkey
  AND p_size IN (24, 32, 34)
  AND ps_availqty > 5000
GROUP BY p_size, p_partkey
ORDER BY m0 DESC, psize, partkey
LIMIT 100
