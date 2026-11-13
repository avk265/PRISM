"""Typed conversion of official dbgen TPC-H flat files to Parquet.

The caller records the dbgen command separately in the mandatory data manifest.
This program does not generate data and does not label arbitrary .tbl files as
official; it only converts the supplied files with the canonical TPC-H schema.
"""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

SCHEMAS = {
    "region": "r_regionkey long,r_name string,r_comment string",
    "nation": "n_nationkey long,n_name string,n_regionkey long,n_comment string",
    "supplier": "s_suppkey long,s_name string,s_address string,s_nationkey long,s_phone string,s_acctbal decimal(15,2),s_comment string",
    "customer": "c_custkey long,c_name string,c_address string,c_nationkey long,c_phone string,c_acctbal decimal(15,2),c_mktsegment string,c_comment string",
    "part": "p_partkey long,p_name string,p_mfgr string,p_brand string,p_type string,p_size int,p_container string,p_retailprice decimal(15,2),p_comment string",
    "partsupp": "ps_partkey long,ps_suppkey long,ps_availqty int,ps_supplycost decimal(15,2),ps_comment string",
    "orders": "o_orderkey long,o_custkey long,o_orderstatus string,o_totalprice decimal(15,2),o_orderdate date,o_orderpriority string,o_clerk string,o_shippriority int,o_comment string",
    "lineitem": "l_orderkey long,l_partkey long,l_suppkey long,l_linenumber int,l_quantity decimal(15,2),l_extendedprice decimal(15,2),l_discount decimal(15,2),l_tax decimal(15,2),l_returnflag string,l_linestatus string,l_shipdate date,l_commitdate date,l_receiptdate date,l_shipinstruct string,l_shipmode string,l_comment string",
}

def main() -> None:
    parser = argparse.ArgumentParser(description="Convert official TPC-H dbgen .tbl files to typed Parquet")
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    missing = [name for name in SCHEMAS if not (args.raw_dir / f"{name}.tbl").is_file()]
    if missing: raise ValueError(f"missing required dbgen files: {missing}")
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName("PRISM-TPCH-Parquet-Import").getOrCreate()
    try:
        counts = {}
        for table, schema in SCHEMAS.items():
            target = args.out / table
            if target.exists() and not args.overwrite: raise FileExistsError(f"target already exists: {target}; use --overwrite explicitly")
            frame = spark.read.option("sep", "|").option("dateFormat", "yyyy-MM-dd").schema(schema).csv(str(args.raw_dir / f"{table}.tbl"))
            frame.write.mode("overwrite").parquet(str(target))
            counts[table] = spark.read.parquet(str(target)).count()
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "TPCH_PARQUET_IMPORT.json").write_text(json.dumps({"created_utc": datetime.now(timezone.utc).isoformat(), "raw_dir": str(args.raw_dir), "tables": counts, "schema_version": 1}, indent=2, sort_keys=True))
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
