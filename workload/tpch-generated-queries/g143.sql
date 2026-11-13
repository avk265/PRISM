-- generated TPC-H-schema training query (seed 7, #143, family spj_agg); not an official TPC-H query
SELECT ps_suppkey AS ps_suppkey,
       SUM(ps_supplycost * ps_availqty) AS m0
FROM partsupp
WHERE ps_availqty > 9000
GROUP BY ps_suppkey
ORDER BY m0 DESC, ps_suppkey
LIMIT 100
