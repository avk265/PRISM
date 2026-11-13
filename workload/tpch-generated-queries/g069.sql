-- generated TPC-H-schema training query (seed 7, #69, family spj_agg); not an official TPC-H query
SELECT n_name AS nation,
       SUM(c_acctbal) AS m0
FROM customer, nation
WHERE c_nationkey = n_nationkey
  AND c_acctbal > 3000
GROUP BY n_name
ORDER BY m0 DESC, nation
LIMIT 100
