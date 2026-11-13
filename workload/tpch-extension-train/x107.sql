-- generated TPC-H-schema training query (seed 11, #107, family wide_agg); not an official TPC-H query
WITH g AS (SELECT l_orderkey, SUM(l_quantity) AS q, COUNT(*) AS c FROM lineitem GROUP BY l_orderkey HAVING SUM(l_quantity) > 50)
SELECT COUNT(*) AS m0, SUM(q) AS m1, MAX(c) AS m2 FROM g
