-- generated TPC-H-schema training query (seed 7, #338, family spj_agg); not an official TPC-H query
SELECT year(l_shipdate) AS ship_year,
       COUNT(*) AS m0,
       COUNT(*) AS m1
FROM lineitem, supplier
WHERE l_suppkey = s_suppkey
  AND l_discount BETWEEN 0.05 AND 0.08
GROUP BY year(l_shipdate)
ORDER BY m0 DESC, ship_year
LIMIT 100
