-- generated TPC-H-schema training query (seed 7, #160, family spj_agg); not an official TPC-H query
SELECT l_suppkey AS suppkey,
       l_returnflag AS returnflag,
       SUM(l_extendedprice * (1 - l_discount)) AS m0
FROM lineitem, supplier
WHERE l_suppkey = s_suppkey
  AND l_discount BETWEEN 0.05 AND 0.06
  AND s_acctbal > 0
GROUP BY l_suppkey, l_returnflag
ORDER BY m0 DESC, suppkey, returnflag
LIMIT 100
