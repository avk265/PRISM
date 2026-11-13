-- generated TPC-H-schema training query (seed 7, #1, family small_tables); not an official TPC-H query
SELECT n_name AS nation, SUM(ps_supplycost * ps_availqty) AS m0, COUNT(*) AS m1
FROM partsupp, supplier, nation
WHERE ps_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND ps_supplycost < 50
GROUP BY n_name
ORDER BY m0 DESC, nation
