-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT c_mktsegment AS mktsegment,
       COUNT(*) AS m0
FROM customer, nation
WHERE c_nationkey = n_nationkey
  AND n_name IN ('FRANCE', 'JAPAN')
  AND c_acctbal > -500
GROUP BY c_mktsegment
ORDER BY m0 DESC, mktsegment
LIMIT 100
