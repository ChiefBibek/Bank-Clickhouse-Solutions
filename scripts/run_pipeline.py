
import csv
import logging
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

ETL_SCRIPT = PROJECT_ROOT / "spark" / "etl_transactions.py"
LOAD_SCRIPT = PROJECT_ROOT / "scripts" / "load_curated_to_clickhouse.py"

RUN_ID = str(uuid.uuid4())
STARTED_AT = datetime.now().astimezone()
LOG_FILE = LOG_DIR / f"pipeline_{STARTED_AT:%Y%m%d_%H%M%S}.log"
AUDIT_FILE = LOG_DIR / "pipeline_audit.csv"

logger = logging.getLogger("bankscale")
logger.setLevel(logging.INFO)
logger.handlers.clear()

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


def run_step(step_name: str, script_path: Path) -> str:
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    logger.info("Starting step: %s", step_name)

    result = subprocess.run(
        [sys.executable, "-u", str(script_path)],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # Preserve child script output in the main log.
    if result.stdout:
        logger.info("%s output:\n%s", step_name, result.stdout.strip())

    if result.stderr:
        logger.info("%s messages:\n%s", step_name, result.stderr.strip())

    logger.info("Completed step: %s", step_name)
    return result.stdout


def parse_etl_summary(output: str) -> dict:
    patterns = {
        "raw_records": r"Raw records:\s*(\d+)",
        "valid_records": r"Valid records:\s*(\d+)",
        "rejected_records": r"Rejected records:\s*(\d+)",
        "reconciliation": r"Reconciliation:\s*(True|False)",
    }

    summary = {}

    for field, pattern in patterns.items():
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            value = match.group(1)
            summary[field] = (
                value.lower() == "true"
                if field == "reconciliation"
                else int(value)
            )

    required = set(patterns)
    missing = required - summary.keys()

    if missing:
        raise ValueError(
            f"Could not read ETL summary fields: {sorted(missing)}"
        )

    return summary


def write_audit(summary: dict) -> None:
    fields = [
        "run_id",
        "started_at",
        "finished_at",
        "duration_seconds",
        "raw_records",
        "valid_records",
        "rejected_records",
        "reconciliation",
        "status",
        "error",
    ]

    file_exists = AUDIT_FILE.exists()

    with AUDIT_FILE.open(
        "a", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fields)

        if not file_exists or AUDIT_FILE.stat().st_size == 0:
            writer.writeheader()

        writer.writerow({field: summary.get(field, "") for field in fields})


def main() -> None:
    started_clock = time.perf_counter()
    summary = {
        "run_id": RUN_ID,
        "started_at": STARTED_AT.isoformat(timespec="seconds"),
        "status": "FAILED",
        "error": "",
    }

    logger.info("BankScale pipeline started. Run ID: %s", RUN_ID)
    logger.info("Detailed log: %s", LOG_FILE)

    try:
        etl_output = run_step("PySpark ETL", ETL_SCRIPT)
        etl_summary = parse_etl_summary(etl_output)
        summary.update(etl_summary)

        if not summary["reconciliation"]:
            raise RuntimeError("ETL reconciliation failed.")

        run_step("ClickHouse load", LOAD_SCRIPT)

        summary["status"] = "SUCCESS"
        logger.info("BANKSCALE PIPELINE SUCCEEDED.")

    except Exception as exc:
        summary["error"] = str(exc)
        logger.exception("BANKSCALE PIPELINE FAILED.")

    finally:
        summary["finished_at"] = datetime.now().astimezone().isoformat(
            timespec="seconds"
        )
        summary["duration_seconds"] = round(
            time.perf_counter() - started_clock, 2
        )

        write_audit(summary)
        logger.info("Audit summary saved: %s", AUDIT_FILE)

    if summary["status"] != "SUCCESS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
