-- generated TPC-H-schema training query (seed 7, #299, family semi_anti); not an official TPC-H query
SELECT o_orderstatus AS orderstatus, COUNT(*) AS m0, SUM(o_totalprice) AS m1
FROM orders
WHERE o_orderstatus = 'P'
  AND EXISTS (SELECT 1 FROM lineitem WHERE l_orderkey = o_orderkey AND l_discount BETWEEN 0.0 AND 0.06)
GROUP BY o_orderstatus
ORDER BY m0 DESC, orderstatus
