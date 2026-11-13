-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT p_size AS psize,
       AVG(p_retailprice) AS m0
FROM part
WHERE p_container LIKE 'SM%'
GROUP BY p_size
HAVING COUNT(*) > 5
ORDER BY m0 DESC, psize
LIMIT 100
