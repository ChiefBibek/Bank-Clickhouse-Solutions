import os
from pathlib import Path
from decimal import Decimal

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    TimestampType,
    DateType,
    DecimalType,
)

# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_FILE = PROJECT_ROOT / "data" / "raw" / "transactions.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "transactions"
REJECTED_DIR = PROJECT_ROOT / "data" / "rejected" / "transactions"


# --------------------------------------------------
# 2. Explicit source schema
# --------------------------------------------------

TRANSACTION_SCHEMA = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("account_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("transaction_timestamp", TimestampType(), True),
    StructField("transaction_date", DateType(), True),
    StructField("transaction_type", StringType(), True),
    StructField("channel", StringType(), True),
    StructField("branch_id", StringType(), True),
    StructField("amount", DecimalType(18, 2), True),
    StructField("currency", StringType(), True),
    StructField("debit_credit", StringType(), True),
    StructField("status", StringType(), True),
])


# --------------------------------------------------
# 3. Start Spark
# --------------------------------------------------

def create_spark_session():
    hadoop_home = PROJECT_ROOT / "tools" / "hadoop"
    hadoop_bin = hadoop_home / "bin"

    if not (hadoop_bin / "winutils.exe").exists():
        raise FileNotFoundError(
            f"winutils.exe not found in {hadoop_bin}"
        )

    if not (hadoop_bin / "hadoop.dll").exists():
        raise FileNotFoundError(
            f"hadoop.dll not found in {hadoop_bin}"
        )

    os.environ["HADOOP_HOME"] = str(hadoop_home)
    os.environ["hadoop.home.dir"] = str(hadoop_home)

    # Make Hadoop's native DLL discoverable by Java.
    os.environ["PATH"] = (
        str(hadoop_bin) + os.pathsep + os.environ.get("PATH", "")
    )

    return (
        SparkSession.builder
        .appName("BankScale-Transaction-ETL")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.hadoop.hadoop.home.dir", str(hadoop_home))
        .getOrCreate()
    )

# --------------------------------------------------
# 4. Read raw transactions
# --------------------------------------------------

def read_transactions(spark):
    print("Reading raw transactions...")

    return (
        spark.read
        .option("header", True)
        .schema(TRANSACTION_SCHEMA)
        .csv(str(RAW_FILE))
    )


# --------------------------------------------------
# 5. Validate records
# --------------------------------------------------

def validate_transactions(df):
    print("Validating transactions...")

    # Count repeated transaction IDs.
    # Every occurrence of a duplicated ID is rejected.
    duplicate_ids = (
        df.groupBy("transaction_id")
        .count()
        .filter(F.col("count") > 1)
        .select("transaction_id")
        .withColumn("is_duplicate", F.lit(True))
    )

    checked = df.join(duplicate_ids, "transaction_id", "left")

    checked = checked.withColumn(
        "rejection_reason",
        F.concat_ws(
            "; ",
            F.when(
                F.col("transaction_id").isNull()
                | (F.trim(F.col("transaction_id")) == ""),
                F.lit("Missing transaction ID"),
            ),
            F.when(
                F.col("is_duplicate") == True,
                F.lit("Duplicate transaction ID"),
            ),
            F.when(
                F.col("account_id").isNull()
                | (F.trim(F.col("account_id")) == ""),
                F.lit("Missing account ID"),
            ),
            F.when(
                F.col("customer_id").isNull()
                | (F.trim(F.col("customer_id")) == ""),
                F.lit("Missing customer ID"),
            ),
            F.when(
                F.col("branch_id").isNull()
                | (F.trim(F.col("branch_id")) == ""),
                F.lit("Missing branch ID"),
            ),
            F.when(
                F.col("transaction_timestamp").isNull()
                | F.col("transaction_date").isNull(),
                F.lit("Invalid transaction date/time"),
            ),
            F.when(
                F.col("amount").isNull(),
                F.lit("Missing or invalid amount"),
            ),
        ),
    ).drop("is_duplicate")

    valid = checked.filter(F.col("rejection_reason") == "")
    rejected = checked.filter(F.col("rejection_reason") != "")

    return valid, rejected


# --------------------------------------------------
# 6. Write Parquet outputs
# --------------------------------------------------

def write_outputs(valid, rejected):
    print("Writing curated Parquet data...")

    valid.write.mode("overwrite").parquet(str(PROCESSED_DIR))

    print("Writing rejected records...")

    rejected.write.mode("overwrite").parquet(str(REJECTED_DIR))


# --------------------------------------------------
# 7. Run pipeline
# --------------------------------------------------

def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Raw CSV not found: {RAW_FILE}")

    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    try:
        raw = read_transactions(spark)

        raw_count = raw.count()
        valid, rejected = validate_transactions(raw)

        valid_count = valid.count()
        rejected_count = rejected.count()

        write_outputs(valid, rejected)

        print("\n========== ETL SUMMARY ==========")
        print(f"Raw records:      {raw_count}")
        print(f"Valid records:    {valid_count}")
        print(f"Rejected records: {rejected_count}")
        print(f"Reconciliation:   {valid_count + rejected_count == raw_count}")
        print(f"Curated output:   {PROCESSED_DIR}")
        print(f"Rejected output:  {REJECTED_DIR}")
        print("=================================")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
