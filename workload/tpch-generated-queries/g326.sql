-- generated TPC-H-schema training query (seed 7, #326, family spj_agg); not an official TPC-H query
SELECT MIN(ps_supplycost) AS m0
FROM partsupp
WHERE ps_supplycost < 50
