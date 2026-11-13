-- generated TPC-H-schema training query (seed 7, #86, family cte); not an official TPC-H query
WITH rev AS (SELECT l_suppkey AS sk, SUM(l_extendedprice * (1 - l_discount)) AS v FROM lineitem
WHERE l_receiptdate > l_commitdate GROUP BY l_suppkey)
SELECT FLOOR(v / 100000) AS bucket, COUNT(*) AS m0, MAX(v) AS m1
FROM rev
GROUP BY FLOOR(v / 100000)
ORDER BY m0 DESC, bucket
LIMIT 100
