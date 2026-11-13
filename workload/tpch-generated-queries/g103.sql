-- generated TPC-H-schema training query (seed 7, #103, family semi_anti); not an official TPC-H query
SELECT o_orderstatus AS orderstatus, COUNT(*) AS m0, SUM(o_totalprice) AS m1
FROM orders
WHERE o_totalprice > 300000
  AND NOT EXISTS (SELECT 1 FROM lineitem WHERE l_orderkey = o_orderkey AND l_returnflag = 'R' AND l_shipdate >= DATE '1992-01-01' AND l_shipdate < DATE '1995-01-01')
GROUP BY o_orderstatus
ORDER BY m0 DESC, orderstatus
