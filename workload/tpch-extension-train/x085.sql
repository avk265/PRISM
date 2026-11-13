-- generated TPC-H-schema training query (seed 11, #85, family window); not an official TPC-H query
WITH c AS (SELECT o_custkey AS ck, year(o_orderdate) AS yr, SUM(o_totalprice) AS spend
           FROM orders
WHERE o_orderpriority IN ('2-HIGH', '4-NOT SPECIFIED', '3-MEDIUM') GROUP BY o_custkey, year(o_orderdate)),
     w AS (SELECT ck, yr, spend, SUM(spend) OVER (PARTITION BY ck ORDER BY yr) AS cum,
                  ROW_NUMBER() OVER (PARTITION BY yr ORDER BY spend DESC, ck) AS rn FROM c)
SELECT yr, ck, spend AS m0, cum AS m1 FROM w WHERE rn <= 20
ORDER BY yr, m0 DESC, ck
