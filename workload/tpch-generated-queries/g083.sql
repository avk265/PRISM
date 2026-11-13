-- generated TPC-H-schema training query (seed 7, #83, family semi_anti); not an official TPC-H query
SELECT n_name AS nation, COUNT(*) AS m0
FROM supplier, nation
WHERE s_nationkey = n_nationkey
  AND NOT EXISTS (SELECT 1 FROM partsupp WHERE ps_suppkey = s_suppkey AND ps_supplycost < 900)
GROUP BY n_name
ORDER BY m0 DESC, nation
