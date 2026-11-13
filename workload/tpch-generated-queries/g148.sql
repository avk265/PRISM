-- generated TPC-H-schema training query (seed 7, #148, family spj_agg); not an official TPC-H query
SELECT AVG(l_discount) AS m0,
       MAX(l_extendedprice) AS m1
FROM lineitem, part
WHERE l_partkey = p_partkey
  AND l_receiptdate > l_commitdate
  AND p_brand = 'Brand#42'
