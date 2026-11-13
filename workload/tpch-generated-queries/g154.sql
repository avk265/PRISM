-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT l_returnflag AS returnflag,
       l_suppkey AS suppkey,
       p_size AS psize,
       SUM(l_quantity) AS m0
FROM lineitem, part, supplier
WHERE l_partkey = p_partkey
  AND l_suppkey = s_suppkey
  AND p_type LIKE '%NICKEL'
  AND l_returnflag = 'N'
  AND s_acctbal > 5000
GROUP BY l_returnflag, l_suppkey, p_size
ORDER BY m0 DESC, returnflag, suppkey, psize
LIMIT 100
