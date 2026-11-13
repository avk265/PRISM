-- generated TPC-H-schema training query (seed 7, #51, family semi_anti); not an official TPC-H query
SELECT o_orderstatus AS orderstatus, COUNT(*) AS m0, SUM(o_totalprice) AS m1
FROM orders
WHERE EXISTS (SELECT 1 FROM lineitem WHERE l_orderkey = o_orderkey AND l_quantity < 25 AND l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1997-01-01')
GROUP BY o_orderstatus
ORDER BY m0 DESC, orderstatus
