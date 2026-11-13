-- generated TPC-H-schema training query (seed 7, #111, family small_tables); not an official TPC-H query
SELECT r_name AS region, c_mktsegment AS mktsegment, COUNT(*) AS m0, AVG(c_acctbal) AS m1
FROM customer, nation, region
WHERE c_nationkey = n_nationkey
  AND n_regionkey = r_regionkey
GROUP BY r_name, c_mktsegment
ORDER BY m0 DESC, region, mktsegment
