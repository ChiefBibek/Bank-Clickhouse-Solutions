
import os
import logging
from pathlib import Path

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


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "transactions"
REJECTED_DIR = PROJECT_ROOT / "data" / "rejected" / "transactions"

RAW_FILE = RAW_DIR / "transactions.csv"
ACCOUNTS_FILE = RAW_DIR / "accounts.csv"
CUSTOMERS_FILE = RAW_DIR / "customers.csv"
BRANCHES_FILE = RAW_DIR / "branches.csv"

HADOOP_HOME = PROJECT_ROOT / "tools" / "hadoop"
HADOOP_BIN = HADOOP_HOME / "bin"

TRANSACTION_COLUMNS = [
    "transaction_id",
    "account_id",
    "customer_id",
    "transaction_timestamp",
    "transaction_date",
    "transaction_type",
    "channel",
    "branch_id",
    "amount",
    "currency",
    "debit_credit",
    "status",
]


# ============================================================
# 2. EXPLICIT TRANSACTION SCHEMA
# ============================================================

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


# ============================================================
# 3. LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("BankScaleETL")


# ============================================================
# 4. CREATE SPARK SESSION
# ============================================================

def create_spark_session():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Missing raw file: {RAW_FILE}")

    # Configure Windows Hadoop helpers when available.
    if (HADOOP_BIN / "winutils.exe").exists():
        os.environ["HADOOP_HOME"] = str(HADOOP_HOME)
        os.environ["hadoop.home.dir"] = str(HADOOP_HOME)
        os.environ["PATH"] = (
            str(HADOOP_BIN) + os.pathsep + os.environ.get("PATH", "")
        )

    return (
        SparkSession.builder
        .appName("BankScale-Transaction-ETL")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.hadoop.hadoop.home.dir", str(HADOOP_HOME))
        .getOrCreate()
    )


# ============================================================
# 5. READ RAW DATA
# ============================================================

def read_transactions(spark):
    logger.info("Reading raw transactions")

    return (
        spark.read
        .option("header", True)
        .schema(TRANSACTION_SCHEMA)
        .csv(str(RAW_FILE))
    )


def read_master_data(spark):
    logger.info("Reading account, customer and branch master data")

    accounts = (
        spark.read
        .option("header", True)
        .csv(str(ACCOUNTS_FILE))
        .select("account_id", "customer_id")
    )

    customers = (
        spark.read
        .option("header", True)
        .csv(str(CUSTOMERS_FILE))
        .select("customer_id")
    )

    branches = (
        spark.read
        .option("header", True)
        .csv(str(BRANCHES_FILE))
        .select("branch_id")
    )

    return accounts, customers, branches


# ============================================================
# 6. VALIDATE TRANSACTIONS
# ============================================================

def validate_transactions(df, accounts, customers, branches):
    logger.info("Building reference lookups")

    # IDs appearing more than once: quarantine every occurrence.
    duplicate_ids = (
        df.groupBy("transaction_id")
        .count()
        .filter(
            F.col("transaction_id").isNotNull()
            & (F.col("count") > 1)
        )
        .select("transaction_id")
        .withColumn("is_duplicate", F.lit(True))
    )

    valid_account_ids = (
        accounts
        .select("account_id")
        .filter(F.col("account_id").isNotNull())
        .distinct()
        .withColumn("account_exists", F.lit(True))
    )

    valid_customer_ids = (
        customers
        .select("customer_id")
        .filter(F.col("customer_id").isNotNull())
        .distinct()
        .withColumn("customer_exists", F.lit(True))
    )

    valid_branch_ids = (
        branches
        .select("branch_id")
        .filter(F.col("branch_id").isNotNull())
        .distinct()
        .withColumn("branch_exists", F.lit(True))
    )

    # Map each account to its customer.
    account_owners = (
        accounts
        .select(
            "account_id",
            F.col("customer_id").alias("account_customer_id"),
        )
        .dropDuplicates(["account_id"])
    )

    logger.info("Applying validation rules")

    checked = (
        df
        .join(duplicate_ids, "transaction_id", "left")
        .join(valid_account_ids, "account_id", "left")
        .join(account_owners, "account_id", "left")
        .join(valid_customer_ids, "customer_id", "left")
        .join(valid_branch_ids, "branch_id", "left")
    )

    # Multiple issues can be recorded for the same transaction.
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
                F.col("account_id").isNotNull()
                & (F.trim(F.col("account_id")) != "")
                & F.col("account_exists").isNull(),
                F.lit("Account ID not found in accounts"),
            ),

            F.when(
                F.col("customer_id").isNull()
                | (F.trim(F.col("customer_id")) == ""),
                F.lit("Missing customer ID"),
            ),

            F.when(
                F.col("customer_id").isNotNull()
                & (F.trim(F.col("customer_id")) != "")
                & F.col("customer_exists").isNull(),
                F.lit("Customer ID not found in customers"),
            ),

            F.when(
                F.col("customer_id").isNotNull()
                & F.col("account_customer_id").isNotNull()
                & (
                    F.col("customer_id")
                    != F.col("account_customer_id")
                ),
                F.lit("Customer ID does not match account owner"),
            ),

            F.when(
                F.col("branch_id").isNull()
                | (F.trim(F.col("branch_id")) == ""),
                F.lit("Missing branch ID"),
            ),

            F.when(
                F.col("branch_id").isNotNull()
                & (F.trim(F.col("branch_id")) != "")
                & F.col("branch_exists").isNull(),
                F.lit("Branch ID not found in branches"),
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

            # Demo policy: negative amounts are anomalies.
            # Real banking rules must handle reversals/refunds.
            F.when(
                F.col("amount") < 0,
                F.lit("Negative amount requires review"),
            ),
        ),
    )

    checked = checked.drop(
        "is_duplicate",
        "account_exists",
        "customer_exists",
        "branch_exists",
        "account_customer_id",
    )

    valid = checked.filter(F.col("rejection_reason") == "")

    rejected = checked.filter(F.col("rejection_reason") != "")

    return valid, rejected


# ============================================================
# 7. WRITE CURATED AND REJECTED PARQUET
# ============================================================

def write_outputs(valid, rejected):
    logger.info("Writing curated Parquet data")

    # Keep only the business columns in the analytical dataset.
    (
        valid.select(*TRANSACTION_COLUMNS)
        .write
        .mode("overwrite")
        .parquet(str(PROCESSED_DIR))
    )

    logger.info("Writing rejected records with rejection reasons")

    (
        rejected
        .write
        .mode("overwrite")
        .parquet(str(REJECTED_DIR))
    )


# ============================================================
# 8. REPORT DATA QUALITY AND RECONCILIATION
# ============================================================

def report_results(raw_count, valid, rejected):
    valid_count = valid.count()
    rejected_count = rejected.count()

    logger.info("Rejection breakdown:")

    (
        rejected
        .select(F.explode(F.split("rejection_reason", "; ")).alias("reason"))
        .groupBy("reason")
        .count()
        .orderBy(F.desc("count"))
        .show(truncate=False)
    )

    reconciled = valid_count + rejected_count == raw_count

    print("\n========== BANKSCALE ETL SUMMARY ==========")
    print(f"Raw records:       {raw_count}")
    print(f"Valid records:     {valid_count}")
    print(f"Rejected records:  {rejected_count}")
    print(f"Reconciliation:    {reconciled}")
    print(f"Curated output:    {PROCESSED_DIR}")
    print(f"Rejected output:   {REJECTED_DIR}")
    print("===========================================\n")

    if not reconciled:
        raise RuntimeError(
            "Reconciliation failed: valid + rejected != raw records"
        )


# ============================================================
# 9. MAIN PIPELINE
# ============================================================

def main():
    required_files = [
        RAW_FILE,
        ACCOUNTS_FILE,
        CUSTOMERS_FILE,
        BRANCHES_FILE,
    ]

    missing_files = [str(path) for path in required_files if not path.exists()]

    if missing_files:
        raise FileNotFoundError(
            "Required input files are missing:\n"
            + "\n".join(missing_files)
        )

    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    try:
        raw = read_transactions(spark)
        accounts, customers, branches = read_master_data(spark)

        raw_count = raw.count()
        logger.info("Raw transaction count: %s", raw_count)

        valid, rejected = validate_transactions(
            raw,
            accounts,
            customers,
            branches,
        )

        write_outputs(valid, rejected)
        report_results(raw_count, valid, rejected)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
