-- generated TPC-H-schema training query (seed 7, #168, family spj_agg); not an official TPC-H query
SELECT l_linestatus AS linestatus,
       year(o_orderdate) AS order_year,
       SUM(l_quantity) AS m0
FROM lineitem, orders
WHERE l_orderkey = o_orderkey
  AND l_quantity < 15
  AND o_orderdate >= DATE '1996-06-01' AND o_orderdate < DATE '1996-01-01'
GROUP BY l_linestatus, year(o_orderdate)
ORDER BY m0 DESC, linestatus, order_year
LIMIT 100
