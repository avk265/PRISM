-- generated TPC-H-schema training query (seed 7, #264, family spj_agg); not an official TPC-H query
SELECT MAX(l_extendedprice) AS m0
FROM lineitem
WHERE l_shipmode IN ('SHIP', 'MAIL', 'RAIL')
