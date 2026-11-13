-- generated TPC-H-schema training query (seed 7, #27, family spj_agg); not an official TPC-H query
SELECT p_size AS psize,
       p_type AS ptype,
       p_partkey AS partkey,
       COUNT(*) AS m0,
       COUNT(*) AS m1
FROM part, partsupp
WHERE ps_partkey = p_partkey
GROUP BY p_size, p_type, p_partkey
ORDER BY m0 DESC, psize, ptype, partkey
LIMIT 100
