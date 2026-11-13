-- generated TPC-H-schema training query (seed 11, #100, family wide_agg); not an official TPC-H query
WITH g AS (SELECT l_orderkey, SUM(l_quantity) AS q, COUNT(*) AS c FROM lineitem
WHERE l_returnflag = 'A'
  AND l_shipmode IN ('REG AIR', 'AIR') GROUP BY l_orderkey HAVING SUM(l_quantity) > 250)
SELECT COUNT(*) AS m0, SUM(q) AS m1, MAX(c) AS m2 FROM g
