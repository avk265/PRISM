-- generated TPC-H-schema training query (seed 7, #13, family spj_agg); not an official TPC-H query
SELECT year(o_orderdate) AS order_year,
       l_suppkey AS suppkey,
       o_orderstatus AS orderstatus,
       COUNT(DISTINCT l_orderkey) AS m0
FROM lineitem, orders
WHERE l_orderkey = o_orderkey
GROUP BY year(o_orderdate), l_suppkey, o_orderstatus
ORDER BY m0 DESC, order_year, suppkey, orderstatus
LIMIT 100
