-- generated TPC-H-schema training query (seed 7, #68, family spj_agg); not an official TPC-H query
SELECT year(l_shipdate) AS ship_year,
       o_custkey AS custkey,
       SUM(o_totalprice) AS m0,
       MAX(l_extendedprice) AS m1
FROM customer, orders, lineitem, nation
WHERE o_custkey = c_custkey
  AND l_orderkey = o_orderkey
  AND c_nationkey = n_nationkey
GROUP BY year(l_shipdate), o_custkey
ORDER BY m0 DESC, ship_year, custkey
LIMIT 100
