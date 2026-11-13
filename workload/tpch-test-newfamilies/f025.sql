-- generated TPC-H-schema test-only query (seed 23, #25, family two_fact_cte); not an official TPC-H query
WITH sold AS (SELECT l_partkey AS pk, l_suppkey AS sk, SUM(l_quantity) AS q FROM lineitem
WHERE l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1996-01-01' GROUP BY l_partkey, l_suppkey),
     stock AS (SELECT ps_partkey AS pk, ps_suppkey AS sk, ps_availqty AS a, ps_supplycost AS c FROM partsupp
WHERE ps_availqty > 9000)
SELECT COUNT(*) AS m0, SUM(sold.q * stock.c) AS m1, SUM(CASE WHEN stock.a > 2.0 * sold.q THEN 1 ELSE 0 END) AS m2
FROM sold, stock WHERE sold.pk = stock.pk AND sold.sk = stock.sk
