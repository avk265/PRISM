-- generated TPC-H-schema training query (seed 7, #137, family semi_anti); not an official TPC-H query
SELECT year(o_orderdate) AS order_year, COUNT(*) AS m0, SUM(o_totalprice) AS m1
FROM orders
WHERE o_orderdate >= DATE '1996-08-01' AND o_orderdate < DATE '1998-01-01'
  AND NOT EXISTS (SELECT 1 FROM lineitem WHERE l_orderkey = o_orderkey AND l_shipmode IN ('FOB'))
GROUP BY year(o_orderdate)
ORDER BY m0 DESC, order_year
