
import logging
from pathlib import Path

import pyarrow.parquet as pq
import requests


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARQUET_DIR = PROJECT_ROOT / "data" / "processed" / "transactions"

CLICKHOUSE_URL = "http://localhost:8106"
CLICKHOUSE_USER = "bankscale_user"
CLICKHOUSE_PASSWORD = "BankScaleDemo2026"

TARGET_TABLE = "bankscale.transactions_curated"
STAGING_TABLE = "bankscale.transactions_curated_staging"

REQUEST_TIMEOUT = 600


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# ClickHouse helpers
# --------------------------------------------------

def execute_query(query: str) -> str:
    """Execute a ClickHouse SQL query over HTTP."""

    response = requests.post(
        CLICKHOUSE_URL,
        params={"query": query},
        auth=(CLICKHOUSE_USER, CLICKHOUSE_PASSWORD),
        timeout=120,
    )

    response.raise_for_status()
    return response.text.strip()


# --------------------------------------------------
# Parquet helpers
# --------------------------------------------------

def get_parquet_files() -> list[Path]:
    """Find the Parquet part files produced by Spark."""

    files = sorted(PARQUET_DIR.glob("part-*.parquet"))

    if not files:
        raise FileNotFoundError(
            f"No Parquet files found in: {PARQUET_DIR}"
        )

    return files


def count_parquet_rows(files: list[Path]) -> int:
    """Count Parquet records using metadata, without reading all rows."""

    total_rows = 0

    for file_path in files:
        parquet_file = pq.ParquetFile(file_path)
        total_rows += parquet_file.metadata.num_rows

    return total_rows


# --------------------------------------------------
# Loading and validation
# --------------------------------------------------

def load_curated_data() -> None:
    """Load Parquet into staging and publish after validation."""

    logger.info("Starting ClickHouse loading step.")

    # 1. Discover output files and determine expected row count.
    files = get_parquet_files()
    expected_rows = count_parquet_rows(files)

    logger.info("Found %s Parquet files.", len(files))
    logger.info("Expected rows from Parquet: %s", expected_rows)

    if expected_rows == 0:
        raise RuntimeError("Parquet output contains zero rows.")

    # 2. Create staging with the target table's schema and engine.
    execute_query(
        f"CREATE TABLE IF NOT EXISTS {STAGING_TABLE} "
        f"AS {TARGET_TABLE}"
    )

    # Clear only staging. The reporting table remains untouched.
    execute_query(f"TRUNCATE TABLE {STAGING_TABLE}")

    # 3. Load every Parquet file into staging.
    for file_path in files:
        logger.info("Loading %s", file_path.name)

        with file_path.open("rb") as parquet_file:
            response = requests.post(
                CLICKHOUSE_URL,
                params={
                    "query": (
                        f"INSERT INTO {STAGING_TABLE} FORMAT Parquet"
                    )
                },
                auth=(CLICKHOUSE_USER, CLICKHOUSE_PASSWORD),
                data=parquet_file,
                timeout=REQUEST_TIMEOUT,
            )

        response.raise_for_status()
        logger.info("Loaded %s successfully.", file_path.name)

    # 4. Validate staging before publishing.
    staged_rows = int(
        execute_query(f"SELECT count() FROM {STAGING_TABLE}")
    )

    logger.info("Expected rows: %s", expected_rows)
    logger.info("Staged rows: %s", staged_rows)

    if staged_rows != expected_rows:
        raise RuntimeError(
            "Staging validation failed. "
            f"Expected {expected_rows} rows, found {staged_rows}. "
            "The reporting table has not been swapped."
        )

    # 5. Publish only after staging passes validation.
    logger.info("Staging validation passed. Publishing data.")

    execute_query(
        f"EXCHANGE TABLES {TARGET_TABLE} AND {STAGING_TABLE}"
    )

    # 6. Verify the published table.
    final_rows = int(
        execute_query(f"SELECT count() FROM {TARGET_TABLE}")
    )

    logger.info("Final reporting row count: %s", final_rows)

    if final_rows != expected_rows:
        raise RuntimeError(
            "Post-publish row-count mismatch. "
            f"Expected {expected_rows}, found {final_rows}."
        )

    logger.info("ClickHouse loading completed successfully.")


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":
    try:
        load_curated_data()
    except Exception:
        logger.exception("ClickHouse loading failed.")
        raise SystemExit(1)
