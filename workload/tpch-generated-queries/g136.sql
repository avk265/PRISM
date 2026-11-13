-- generated TPC-H-schema training query (seed 7, #136, family spj_agg); not an official TPC-H query
SELECT ps_suppkey AS ps_suppkey,
       COUNT(*) AS m0,
       MIN(ps_supplycost) AS m1
FROM partsupp
WHERE ps_supplycost < 900
GROUP BY ps_suppkey
HAVING COUNT(*) > 20
ORDER BY m0 DESC, ps_suppkey
LIMIT 100
