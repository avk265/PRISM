-- generated TPC-H-schema training query (seed 7, #235, family spj_agg); not an official TPC-H query
SELECT COUNT(*) AS m0
FROM orders, customer, lineitem, supplier
WHERE o_custkey = c_custkey
  AND l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND l_discount BETWEEN 0.0 AND 0.06
