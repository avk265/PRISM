-- generated TPC-H-schema training query (seed 7, #347, family spj_agg); not an official TPC-H query
SELECT ps_suppkey AS ps_suppkey,
       SUM(ps_supplycost * ps_availqty) AS m0,
       COUNT(*) AS m1,
       MIN(ps_supplycost) AS m2
FROM partsupp
WHERE ps_supplycost < 500
GROUP BY ps_suppkey
HAVING COUNT(*) > 20
ORDER BY m0 DESC, ps_suppkey
LIMIT 100
