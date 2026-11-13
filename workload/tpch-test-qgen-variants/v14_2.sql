-- qgen variant of official TPC-H q14 (test only)
-- using 1129725411 as a seed to the RNG


select
	100.00 * sum(case
		when p_type like 'PROMO%'
			then l_extendedprice * (1 - l_discount)
		else 0
	end) / sum(l_extendedprice * (1 - l_discount)) as promo_revenue
from
	lineitem,
	part
where
	l_partkey = p_partkey
	and l_shipdate >= date '1996-02-01'
	and l_shipdate < date '1996-02-01' + interval '1' month;
--#SET ROWS_FETCH -1
