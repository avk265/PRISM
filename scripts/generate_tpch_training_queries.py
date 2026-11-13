"""
Generate structurally diverse training queries on the TPC-H schema.

The 22 official TPC-H queries are too few to train an allocation model, and qgen parameter
variants only re-roll constants of the same 22 shapes. These queries instead differ in shape:
a random walk over the TPC-H foreign-key graph (0-6 joins from a random root table), random
filters with widely varying selectivity, 0-3 group-by keys of low or high cardinality, different
aggregates, optional HAVING and IN-subquery. ORDER BY is total (aggregate, then every group key),
so LIMIT returns the same rows on every run and result checksums stay comparable.

Families (share of queries): plain select-project-join-aggregate, EXISTS/NOT EXISTS semi/anti
joins, scalar and correlated subqueries, multi-level aggregation via CTEs, UNION ALL, DISTINCT,
top-N, CASE aggregates, and small-table-only queries.

They are used ONLY for training; the 22 official queries are the held-out test set.

Usage: python -I scripts/generate_tpch_training_queries.py --n 80 --seed 7
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# FK edges: (table_a, table_b, join predicate)
EDGES = [
    ("lineitem", "orders", "l_orderkey = o_orderkey"),
    ("lineitem", "part", "l_partkey = p_partkey"),
    ("lineitem", "supplier", "l_suppkey = s_suppkey"),
    ("lineitem", "partsupp", "l_partkey = ps_partkey AND l_suppkey = ps_suppkey"),
    ("orders", "customer", "o_custkey = c_custkey"),
    ("customer", "nation", "c_nationkey = n_nationkey"),
    ("supplier", "nation", "s_nationkey = n_nationkey"),
    ("partsupp", "part", "ps_partkey = p_partkey"),
    ("partsupp", "supplier", "ps_suppkey = s_suppkey"),
    ("nation", "region", "n_regionkey = r_regionkey"),
]

FILTERS = {
    "lineitem": [
        lambda r: f"l_shipdate >= DATE '{r.choice([1992, 1993, 1994, 1995, 1996, 1997])}-01-01' "
                  f"AND l_shipdate < DATE '{r.choice([1993, 1995, 1997, 1999])}-01-01'",
        lambda r: f"l_quantity < {r.choice([5, 15, 25, 40])}",
        lambda r: f"l_discount BETWEEN {r.choice([0.0, 0.02, 0.05])} AND {r.choice([0.06, 0.08, 0.1])}",
        lambda r: "l_returnflag = '" + r.choice(["R", "A", "N"]) + "'",
        lambda r: "l_shipmode IN (" + ", ".join(f"'{m}'" for m in r.sample(
            ["MAIL", "SHIP", "AIR", "RAIL", "TRUCK", "FOB", "REG AIR"], r.randint(1, 4))) + ")",
        lambda r: f"l_receiptdate > l_commitdate",
    ],
    "orders": [
        lambda r: f"o_orderdate >= DATE '{r.choice([1992, 1993, 1994, 1995, 1996])}-0{r.randint(1, 9)}-01' "
                  f"AND o_orderdate < DATE '{r.choice([1995, 1996, 1997, 1998])}-01-01'",
        lambda r: "o_orderpriority IN (" + ", ".join(f"'{p}'" for p in r.sample(
            ["1-URGENT", "2-HIGH", "3-MEDIUM", "4-NOT SPECIFIED", "5-LOW"], r.randint(1, 3))) + ")",
        lambda r: f"o_totalprice > {r.choice([1000, 50000, 150000, 300000])}",
        lambda r: "o_orderstatus = '" + r.choice(["F", "O", "P"]) + "'",
    ],
    "customer": [
        lambda r: "c_mktsegment = '" + r.choice(["BUILDING", "AUTOMOBILE", "MACHINERY", "HOUSEHOLD", "FURNITURE"]) + "'",
        lambda r: f"c_acctbal > {r.choice([-500, 0, 3000, 8000])}",
    ],
    "part": [
        lambda r: f"p_size IN ({', '.join(str(x) for x in r.sample(range(1, 51), r.randint(1, 8)))})",
        lambda r: f"p_brand = 'Brand#{r.randint(1, 5)}{r.randint(1, 5)}'",
        lambda r: "p_type LIKE '%" + r.choice(["BRASS", "STEEL", "TIN", "NICKEL", "COPPER"]) + "'",
        lambda r: "p_container LIKE '" + r.choice(["SM", "MED", "LG", "JUMBO", "WRAP"]) + "%'",
    ],
    "supplier": [lambda r: f"s_acctbal > {r.choice([-500, 0, 5000])}"],
    "partsupp": [lambda r: f"ps_availqty > {r.choice([100, 1000, 5000, 9000])}",
                 lambda r: f"ps_supplycost < {r.choice([50, 200, 500, 900])}"],
    "nation": [lambda r: "n_name IN (" + ", ".join(f"'{n}'" for n in r.sample(
        ["FRANCE", "GERMANY", "BRAZIL", "CHINA", "INDIA", "JAPAN", "UNITED STATES", "KENYA", "PERU"], r.randint(1, 4))) + ")"],
    "region": [lambda r: "r_name = '" + r.choice(["ASIA", "EUROPE", "AMERICA", "AFRICA", "MIDDLE EAST"]) + "'"],
}

GROUP_KEYS = {  # (expression, alias) low- and high-cardinality keys
    "lineitem": [("l_returnflag", "returnflag"), ("l_linestatus", "linestatus"), ("l_shipmode", "shipmode"),
                 ("year(l_shipdate)", "ship_year"), ("l_suppkey", "suppkey")],
    "orders": [("o_orderpriority", "orderpriority"), ("year(o_orderdate)", "order_year"),
               ("o_orderstatus", "orderstatus"), ("o_custkey", "custkey")],
    "customer": [("c_mktsegment", "mktsegment"), ("c_custkey", "c_custkey")],
    "part": [("p_brand", "brand"), ("p_type", "ptype"), ("p_size", "psize"), ("p_partkey", "partkey")],
    "supplier": [("s_name", "sname"), ("s_suppkey", "s_suppkey")],
    "partsupp": [("ps_suppkey", "ps_suppkey")],
    "nation": [("n_name", "nation")],
    "region": [("r_name", "region")],
}

AGGS = {
    "lineitem": ["SUM(l_extendedprice * (1 - l_discount))", "SUM(l_quantity)", "AVG(l_discount)",
                 "COUNT(*)", "COUNT(DISTINCT l_orderkey)", "MAX(l_extendedprice)"],
    "orders": ["SUM(o_totalprice)", "COUNT(*)", "AVG(o_totalprice)", "COUNT(DISTINCT o_custkey)"],
    "partsupp": ["SUM(ps_supplycost * ps_availqty)", "COUNT(*)", "MIN(ps_supplycost)"],
    "customer": ["SUM(c_acctbal)", "COUNT(*)"],
    "part": ["COUNT(*)", "AVG(p_retailprice)"],
    "supplier": ["COUNT(*)", "SUM(s_acctbal)"],
}

ROOTS = [("lineitem", 0.55), ("orders", 0.2), ("partsupp", 0.15), ("customer", 0.05), ("part", 0.05)]


def neighbours(t):
    for a, b, p in EDGES:
        if a == t:
            yield b, p
        elif b == t:
            yield a, p


def make_query(r: random.Random) -> str:
    root = r.choices([t for t, _ in ROOTS], [w for _, w in ROOTS])[0]
    tables, preds = [root], []
    for _ in range(r.choice([0, 1, 1, 2, 2, 3, 3, 4, 5, 6])):
        # only follow foreign key -> primary key (n:1) edges from tables already in the query, so the
        # join tree is a key-safe snowflake; walking "down" a key (e.g. nation -> customer) caused
        # many-to-many blow-ups at 10 GB (g106 ran executors out of memory)
        frontier = [(t, b, p) for t in tables for a, b, p in EDGES if a == t and b not in tables]
        if not frontier:
            break
        _, n, p = r.choice(frontier)
        tables.append(n)
        preds.append(p)

    filt_tables = r.sample(tables, k=min(len(tables), r.randint(0, 3)))
    for t in filt_tables:
        if t in FILTERS:
            preds.append(r.choice(FILTERS[t])(r))

    cand = [k for t in tables for k in GROUP_KEYS.get(t, [])]
    keys = r.sample(cand, k=min(len(cand), r.choice([0, 1, 1, 2, 2, 3])))
    agg_src = [a for t in tables for a in AGGS.get(t, [])] or ["COUNT(*)"]
    aggs = r.sample(agg_src, k=min(len(agg_src), r.randint(1, 3)))

    if r.random() < 0.15 and "lineitem" not in tables and "orders" in tables:
        preds.append("o_orderkey IN (SELECT l_orderkey FROM lineitem GROUP BY l_orderkey "
                     f"HAVING SUM(l_quantity) > {r.choice([150, 250, 300])})")
    elif r.random() < 0.10 and "lineitem" in tables and "part" not in tables:
        preds.append(f"l_partkey IN (SELECT p_partkey FROM part WHERE p_size < {r.choice([5, 15, 30])})")

    select = [f"{e} AS {a}" for e, a in keys] + [f"{agg} AS m{i}" for i, agg in enumerate(aggs)]
    sql = "SELECT " + ",\n       ".join(select) + "\nFROM " + ", ".join(tables)
    if preds:
        sql += "\nWHERE " + "\n  AND ".join(preds)
    if keys:
        sql += "\nGROUP BY " + ", ".join(e for e, _ in keys)
        if r.random() < 0.2:
            sql += f"\nHAVING COUNT(*) > {r.choice([1, 5, 20])}"
        sql += "\nORDER BY m0 DESC, " + ", ".join(a for _, a in keys) + "\nLIMIT 100"
    return sql


def _f(r, table, k=1):
    """k random filter predicates on `table`."""
    return [fn(r) for fn in r.sample(FILTERS[table], k=min(k, len(FILTERS[table])))]


def _where(preds):
    return ("\nWHERE " + "\n  AND ".join(preds)) if preds else ""


def fam_semi_anti(r):
    """EXISTS / NOT EXISTS semi- and anti-joins (TPC-H q4/q21/q22 style)."""
    neg = "NOT " if r.random() < 0.4 else ""
    kind = r.choice(["orders_lineitem", "customer_orders", "supplier_partsupp", "part_lineitem"])
    if kind == "orders_lineitem":
        inner = ["l_orderkey = o_orderkey"] + _f(r, "lineitem", r.randint(1, 2))
        key = r.choice([("o_orderpriority", "orderpriority"), ("o_orderstatus", "orderstatus"),
                        ("year(o_orderdate)", "order_year")])
        return (f"SELECT {key[0]} AS {key[1]}, COUNT(*) AS m0, SUM(o_totalprice) AS m1\nFROM orders"
                + _where(_f(r, "orders", r.randint(0, 1)) + [f"{neg}EXISTS (SELECT 1 FROM lineitem WHERE " + " AND ".join(inner) + ")"])
                + f"\nGROUP BY {key[0]}\nORDER BY m0 DESC, {key[1]}")
    if kind == "customer_orders":
        inner = ["o_custkey = c_custkey"] + _f(r, "orders", 1)
        return ("SELECT c_mktsegment AS mktsegment, COUNT(*) AS m0, SUM(c_acctbal) AS m1\nFROM customer"
                + _where(_f(r, "customer", r.randint(0, 1)) + [f"{neg}EXISTS (SELECT 1 FROM orders WHERE " + " AND ".join(inner) + ")"])
                + "\nGROUP BY c_mktsegment\nORDER BY m0 DESC, mktsegment")
    if kind == "supplier_partsupp":
        inner = ["ps_suppkey = s_suppkey"] + _f(r, "partsupp", 1)
        return ("SELECT n_name AS nation, COUNT(*) AS m0\nFROM supplier, nation"
                + _where(["s_nationkey = n_nationkey", f"{neg}EXISTS (SELECT 1 FROM partsupp WHERE " + " AND ".join(inner) + ")"])
                + "\nGROUP BY n_name\nORDER BY m0 DESC, nation")
    inner = ["l_partkey = p_partkey"] + _f(r, "lineitem", 1)
    return ("SELECT p_brand AS brand, COUNT(*) AS m0, AVG(p_retailprice) AS m1\nFROM part"
            + _where(_f(r, "part", 1) + [f"{neg}EXISTS (SELECT 1 FROM lineitem WHERE " + " AND ".join(inner) + ")"])
            + "\nGROUP BY p_brand\nORDER BY m0 DESC, brand\nLIMIT 100")


def fam_subquery(r):
    """Scalar and correlated subqueries (TPC-H q2/q17/q20 style)."""
    kind = r.choice(["q17", "scalar_orders", "q2", "scalar_lineitem"])
    if kind == "q17":
        frac = r.choice([0.2, 0.5, 0.8])
        return ("SELECT SUM(l_extendedprice) AS m0, COUNT(*) AS m1\nFROM lineitem, part"
                + _where(["p_partkey = l_partkey"] + _f(r, "part", r.randint(1, 2)) +
                         [f"l_quantity < (SELECT {frac} * AVG(l_quantity) FROM lineitem WHERE l_partkey = p_partkey)"]))
    if kind == "scalar_orders":
        return ("SELECT o_orderpriority AS orderpriority, COUNT(*) AS m0\nFROM orders"
                + _where(_f(r, "orders", r.randint(0, 1)) +
                         [f"o_totalprice > (SELECT {r.choice([1.0, 1.5, 2.0])} * AVG(o_totalprice) FROM orders)"])
                + "\nGROUP BY o_orderpriority\nORDER BY m0 DESC, orderpriority")
    if kind == "q2":
        return ("SELECT p_partkey AS partkey, s_suppkey AS suppkey, ps_supplycost AS m0\nFROM part, partsupp, supplier"
                + _where(["p_partkey = ps_partkey", "s_suppkey = ps_suppkey"] + _f(r, "part", r.randint(1, 2)) +
                         ["ps_supplycost = (SELECT MIN(ps2.ps_supplycost) FROM partsupp ps2 WHERE ps2.ps_partkey = p_partkey)"])
                + "\nORDER BY m0, partkey, suppkey\nLIMIT 100")
    return ("SELECT l_returnflag AS returnflag, COUNT(*) AS m0, SUM(l_extendedprice) AS m1\nFROM lineitem"
            + _where(_f(r, "lineitem", 1) +
                     [f"l_extendedprice > (SELECT {r.choice([1.0, 2.0])} * AVG(l_extendedprice) FROM lineitem)"])
            + "\nGROUP BY l_returnflag\nORDER BY m0 DESC, returnflag")


def fam_cte(r):
    """Multi-level aggregation through CTEs (TPC-H q13/q15/q18 style)."""
    kind = r.choice(["cust_dist", "supp_revenue", "join_aggs", "big_orders"])
    if kind == "cust_dist":
        return ("WITH c AS (SELECT c_custkey, COUNT(o_orderkey) AS n FROM customer LEFT OUTER JOIN orders "
                "ON c_custkey = o_custkey" + (" AND " + _f(r, "orders", 1)[0] if r.random() < 0.6 else "") +
                " GROUP BY c_custkey)\nSELECT n AS c_count, COUNT(*) AS m0\nFROM c\nGROUP BY n\nORDER BY m0 DESC, c_count")
    if kind == "supp_revenue":
        return ("WITH rev AS (SELECT l_suppkey AS sk, SUM(l_extendedprice * (1 - l_discount)) AS v FROM lineitem"
                + _where(_f(r, "lineitem", 1)) + " GROUP BY l_suppkey)\n"
                "SELECT FLOOR(v / 100000) AS bucket, COUNT(*) AS m0, MAX(v) AS m1\nFROM rev\nGROUP BY FLOOR(v / 100000)\n"
                "ORDER BY m0 DESC, bucket\nLIMIT 100")
    if kind == "join_aggs":
        return ("WITH a AS (SELECT o_custkey AS ck, SUM(o_totalprice) AS spend FROM orders" + _where(_f(r, "orders", 1))
                + " GROUP BY o_custkey),\n     b AS (SELECT c_custkey AS ck, c_nationkey AS nk FROM customer"
                + _where(_f(r, "customer", r.randint(0, 1))) + ")\n"
                "SELECT n_name AS nation, COUNT(*) AS m0, SUM(spend) AS m1\nFROM a, b, nation\n"
                "WHERE a.ck = b.ck AND b.nk = n_nationkey\nGROUP BY n_name\nORDER BY m1 DESC, nation")
    return ("WITH big AS (SELECT l_orderkey AS ok FROM lineitem GROUP BY l_orderkey "
            f"HAVING SUM(l_quantity) > {r.choice([200, 250, 300])})\n"
            "SELECT o_orderpriority AS orderpriority, COUNT(*) AS m0, SUM(o_totalprice) AS m1\nFROM orders, big\n"
            "WHERE o_orderkey = big.ok\nGROUP BY o_orderpriority\nORDER BY m0 DESC, orderpriority")


def fam_union(r):
    a, b = r.sample(FILTERS["lineitem"], 2)
    return ("WITH u AS (\n  SELECT l_returnflag AS f, l_extendedprice AS v FROM lineitem WHERE " + a(r) +
            "\n  UNION ALL\n  SELECT l_returnflag AS f, l_extendedprice AS v FROM lineitem WHERE " + b(r) + ")\n"
            "SELECT f AS returnflag, COUNT(*) AS m0, SUM(v) AS m1\nFROM u\nGROUP BY f\nORDER BY m0 DESC, returnflag")


def fam_distinct(r):
    kind = r.choice(["count_distinct", "select_distinct"])
    if kind == "count_distinct":
        col = r.choice(["l_partkey", "l_suppkey", "l_orderkey"])
        return (f"SELECT l_shipmode AS shipmode, COUNT(DISTINCT {col}) AS m0\nFROM lineitem"
                + _where(_f(r, "lineitem", r.randint(1, 2))) + "\nGROUP BY l_shipmode\nORDER BY m0 DESC, shipmode")
    return ("SELECT DISTINCT o_custkey AS custkey, o_orderpriority AS orderpriority\nFROM orders"
            + _where(_f(r, "orders", r.randint(1, 2))) + "\nORDER BY custkey, orderpriority\nLIMIT 100")


def fam_topn(r):
    if r.random() < 0.6:
        return ("SELECT l_orderkey AS ok, l_linenumber AS ln, l_extendedprice AS m0\nFROM lineitem"
                + _where(_f(r, "lineitem", r.randint(1, 2))) + "\nORDER BY m0 DESC, ok, ln\nLIMIT 100")
    return ("SELECT o_orderkey AS ok, o_totalprice AS m0, o_orderdate AS od\nFROM orders"
            + _where(_f(r, "orders", r.randint(1, 2))) + "\nORDER BY m0 DESC, ok\nLIMIT 100")


def fam_case(r):
    """Conditional aggregates (TPC-H q12/q14 style)."""
    if r.random() < 0.5:
        return ("SELECT l_shipmode AS shipmode,\n"
                "       SUM(CASE WHEN o_orderpriority IN ('1-URGENT', '2-HIGH') THEN 1 ELSE 0 END) AS m0,\n"
                "       SUM(CASE WHEN o_orderpriority NOT IN ('1-URGENT', '2-HIGH') THEN 1 ELSE 0 END) AS m1\n"
                "FROM orders, lineitem" + _where(["o_orderkey = l_orderkey"] + _f(r, "lineitem", r.randint(1, 2)))
                + "\nGROUP BY l_shipmode\nORDER BY shipmode")
    return ("SELECT year(l_shipdate) AS ship_year,\n"
            "       SUM(CASE WHEN p_type LIKE 'PROMO%' THEN l_extendedprice * (1 - l_discount) ELSE 0 END) AS m0,\n"
            "       SUM(l_extendedprice * (1 - l_discount)) AS m1\n"
            "FROM lineitem, part" + _where(["l_partkey = p_partkey"] + _f(r, "lineitem", r.randint(0, 1)))
            + "\nGROUP BY year(l_shipdate)\nORDER BY ship_year")


def fam_small_tables(r):
    """Queries that never touch lineitem/orders (small inputs)."""
    kind = r.choice(["ps", "cust", "part"])
    if kind == "ps":
        return ("SELECT n_name AS nation, SUM(ps_supplycost * ps_availqty) AS m0, COUNT(*) AS m1\n"
                "FROM partsupp, supplier, nation" + _where(["ps_suppkey = s_suppkey", "s_nationkey = n_nationkey"]
                                                           + _f(r, "partsupp", 1)) + "\nGROUP BY n_name\nORDER BY m0 DESC, nation")
    if kind == "cust":
        return ("SELECT r_name AS region, c_mktsegment AS mktsegment, COUNT(*) AS m0, AVG(c_acctbal) AS m1\n"
                "FROM customer, nation, region" + _where(["c_nationkey = n_nationkey", "n_regionkey = r_regionkey"]
                                                         + _f(r, "customer", r.randint(0, 1)))
                + "\nGROUP BY r_name, c_mktsegment\nORDER BY m0 DESC, region, mktsegment")
    return ("SELECT p_brand AS brand, p_size AS psize, COUNT(*) AS m0\nFROM part" + _where(_f(r, "part", r.randint(1, 2)))
            + "\nGROUP BY p_brand, p_size\nORDER BY m0 DESC, brand, psize\nLIMIT 100")


FAMILIES = [  # (name, generator, share)
    ("spj_agg", lambda r: make_query(r), 0.36), ("semi_anti", fam_semi_anti, 0.11),
    ("subquery", fam_subquery, 0.10), ("cte", fam_cte, 0.11), ("union", fam_union, 0.06),
    ("distinct", fam_distinct, 0.07), ("topn", fam_topn, 0.07), ("case", fam_case, 0.07),
    ("small_tables", fam_small_tables, 0.05),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=360)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "workload" / "tpch-generated-queries")
    ap.add_argument("--replace", nargs="*", default=[],
                    help="only regenerate these query ids (spj_agg family, key-safe), keep every other file")
    args = ap.parse_args()
    r = random.Random(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.replace:
        existing = {f.read_text().split("\n", 1)[1] for f in args.out.glob("g*.sql")}
        for qid in args.replace:
            for _ in range(1000):
                sql = make_query(r)
                if sql not in existing:
                    break
            existing.add(sql)
            (args.out / f"{qid}.sql").write_text(
                f"-- generated TPC-H-schema training query (seed {args.seed}, replacement for a many-to-many "
                f"join query, family spj_agg); not an official TPC-H query\n{sql}\n")
        print(f"replaced {len(args.replace)} queries")
        return
    for old in args.out.glob("g*.sql"):
        old.unlink()
    plan = [name for name, _, share in FAMILIES for _ in range(round(share * args.n))]
    plan = (plan + ["spj_agg"] * args.n)[:args.n]
    r.shuffle(plan)
    gen = {name: fn for name, fn, _ in FAMILIES}
    seen, counts = set(), {}
    for i, fam_name in enumerate(plan, 1):
        for _ in range(200):
            sql = gen[fam_name](r)
            if sql not in seen:
                break
        seen.add(sql)
        counts[fam_name] = counts.get(fam_name, 0) + 1
        (args.out / f"g{i:03d}.sql").write_text(
            f"-- generated TPC-H-schema training query (seed {args.seed}, #{i}, family {fam_name}); "
            f"not an official TPC-H query\n{sql}\n")
    print(f"wrote {args.n} queries to {args.out}: {counts}")


if __name__ == "__main__":
    main()
