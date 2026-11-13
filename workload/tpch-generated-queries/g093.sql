-- generated TPC-H-schema training query (seed 7, #93, family cte); not an official TPC-H query
WITH c AS (SELECT c_custkey, COUNT(o_orderkey) AS n FROM customer LEFT OUTER JOIN orders ON c_custkey = o_custkey AND o_totalprice > 1000 GROUP BY c_custkey)
SELECT n AS c_count, COUNT(*) AS m0
FROM c
GROUP BY n
ORDER BY m0 DESC, c_count
