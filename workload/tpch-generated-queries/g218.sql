-- generated TPC-H-schema training query (seed 7, #218, family spj_agg); not an official TPC-H query
SELECT AVG(l_discount) AS m0,
       COUNT(*) AS m1,
       MAX(l_extendedprice) AS m2
FROM lineitem, orders
WHERE l_orderkey = o_orderkey
  AND o_orderpriority IN ('1-URGENT', '4-NOT SPECIFIED')
  AND l_receiptdate > l_commitdate
