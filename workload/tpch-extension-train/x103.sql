-- generated TPC-H-schema training query (seed 11, #103, family wide_agg); not an official TPC-H query
WITH g AS (SELECT l_partkey, SUM(l_quantity) AS q, COUNT(*) AS c FROM lineitem
WHERE l_shipmode IN ('RAIL') GROUP BY l_partkey HAVING SUM(l_quantity) > 50)
SELECT COUNT(*) AS m0, SUM(q) AS m1, MAX(c) AS m2 FROM g
