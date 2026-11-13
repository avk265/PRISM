-- generated TPC-H-schema training query (seed 7, #64, family spj_agg); not an official TPC-H query
SELECT year(o_orderdate) AS order_year,
       l_shipmode AS shipmode,
       AVG(l_discount) AS m0
FROM orders, lineitem, supplier
WHERE l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND s_acctbal > -500
  AND l_quantity < 5
  AND o_orderstatus = 'P'
GROUP BY year(o_orderdate), l_shipmode
ORDER BY m0 DESC, order_year, shipmode
LIMIT 100
