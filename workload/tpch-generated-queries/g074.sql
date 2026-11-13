-- generated TPC-H-schema training query (seed 7, #74, family spj_agg); not an official TPC-H query
SELECT ps_suppkey AS ps_suppkey,
       COUNT(*) AS m0,
       MIN(ps_supplycost) AS m1,
       SUM(ps_supplycost * ps_availqty) AS m2
FROM partsupp
WHERE ps_supplycost < 900
GROUP BY ps_suppkey
ORDER BY m0 DESC, ps_suppkey
LIMIT 100
