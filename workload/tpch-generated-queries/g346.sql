-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT c_custkey AS c_custkey,
       SUM(c_acctbal) AS m0,
       COUNT(*) AS m1
FROM customer, nation, region
WHERE c_nationkey = n_nationkey
  AND n_regionkey = r_regionkey
GROUP BY c_custkey
ORDER BY m0 DESC, c_custkey
LIMIT 100
