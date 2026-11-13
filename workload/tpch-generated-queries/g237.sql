-- generated TPC-H-schema training query (seed 7, #237, family spj_agg); not an official TPC-H query
SELECT s_name AS sname,
       AVG(l_discount) AS m0
FROM lineitem, supplier
WHERE l_suppkey = s_suppkey
GROUP BY s_name
ORDER BY m0 DESC, sname
LIMIT 100
