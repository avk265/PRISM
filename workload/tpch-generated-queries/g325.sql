-- generated TPC-H-schema training query (seed 7, #325, family spj_agg); not an official TPC-H query
SELECT ps_suppkey AS ps_suppkey,
       MIN(ps_supplycost) AS m0
FROM partsupp
WHERE ps_availqty > 5000
GROUP BY ps_suppkey
ORDER BY m0 DESC, ps_suppkey
LIMIT 100
