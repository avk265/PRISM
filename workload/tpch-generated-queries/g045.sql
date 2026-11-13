-- generated TPC-H-schema training query (seed 7, #45, family semi_anti); not an official TPC-H query
SELECT year(o_orderdate) AS order_year, COUNT(*) AS m0, SUM(o_totalprice) AS m1
FROM orders
WHERE NOT EXISTS (SELECT 1 FROM lineitem WHERE l_orderkey = o_orderkey AND l_returnflag = 'R')
GROUP BY year(o_orderdate)
ORDER BY m0 DESC, order_year
