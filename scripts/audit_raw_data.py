import pandas as pd
from pathlib import Path


# ==================================================
# 1. Configuration
# ==================================================

BASE_DIR = Path(r"D:\BankScale")
RAW_DIR = BASE_DIR / "data" / "raw"


# ==================================================
# 2. Files we expect
# ==================================================

expected_files = [
    "branches.csv",
    "products.csv",
    "customers.csv",
    "accounts.csv",
    "transactions.csv",
    "loans.csv",
    "cards.csv",
]


# ==================================================
# 3. Load all datasets
# ==================================================

data = {}

print("=" * 70)
print("BankScale - RAW DATA AUDIT")
print("=" * 70)

for filename in expected_files:

    path = RAW_DIR / filename

    if not path.exists():
        print(f"\nMISSING: {filename}")
        continue

    df = pd.read_csv(path)

    data[filename] = df

    print(
        f"\n{filename:<20} "
        f"{len(df):>10,} rows | "
        f"{len(df.columns):>3} columns | "
        f"{path.stat().st_size / 1024:.2f} KB"
    )


# ==================================================
# 4. Row count summary
# ==================================================

print("\n")
print("=" * 70)
print("ROW COUNT SUMMARY")
print("=" * 70)

for filename, df in data.items():

    print(
        f"{filename:<20} "
        f"{len(df):>10,}"
    )


# ==================================================
# 5. Column information
# ==================================================

print("\n")
print("=" * 70)
print("COLUMN INFORMATION")
print("=" * 70)

for filename, df in data.items():

    print(f"\n--- {filename} ---")

    for column in df.columns:

        print(
            f"{column:<25} "
            f"{str(df[column].dtype):<12} "
            f"nulls={df[column].isna().sum():>5,}"
        )


# ==================================================
# 6. Duplicate ID checks
# ==================================================

print("\n")
print("=" * 70)
print("DUPLICATE ID CHECK")
print("=" * 70)

id_columns = {
    "branches.csv": "branch_id",
    "products.csv": "product_id",
    "customers.csv": "customer_id",
    "accounts.csv": "account_id",
    "transactions.csv": "transaction_id",
    "loans.csv": "loan_id",
    "cards.csv": "card_id",
}

for filename, id_column in id_columns.items():

    df = data[filename]

    duplicates = df[id_column].duplicated().sum()

    print(
        f"{filename:<20} "
        f"duplicate {id_column}: "
        f"{duplicates:,}"
    )


# ==================================================
# 7. Foreign-key validation
# ==================================================

print("\n")
print("=" * 70)
print("FOREIGN KEY VALIDATION")
print("=" * 70)


customers = data["customers.csv"]
accounts = data["accounts.csv"]
transactions = data["transactions.csv"]
loans = data["loans.csv"]
cards = data["cards.csv"]
branches = data["branches.csv"]


# Accounts → Customers
invalid = (
    ~accounts["customer_id"]
    .isin(customers["customer_id"])
).sum()

print(
    f"Accounts → Customers : "
    f"{invalid:,} invalid"
)


# Accounts → Branches
invalid = (
    ~accounts["branch_id"]
    .isin(branches["branch_id"])
).sum()

print(
    f"Accounts → Branches   : "
    f"{invalid:,} invalid"
)


# Transactions → Accounts
invalid = (
    ~transactions["account_id"]
    .isin(accounts["account_id"])
).sum()

print(
    f"Transactions → Accounts : "
    f"{invalid:,} invalid"
)


# Loans → Customers
invalid = (
    ~loans["customer_id"]
    .isin(customers["customer_id"])
).sum()

print(
    f"Loans → Customers     : "
    f"{invalid:,} invalid"
)


# Loans → Branches
invalid = (
    ~loans["branch_id"]
    .isin(branches["branch_id"])
).sum()

print(
    f"Loans → Branches       : "
    f"{invalid:,} invalid"
)


# Cards → Customers
invalid = (
    ~cards["customer_id"]
    .isin(customers["customer_id"])
).sum()

print(
    f"Cards → Customers     : "
    f"{invalid:,} invalid"
)


# Cards → Accounts
invalid = (
    ~cards["account_id"]
    .isin(accounts["account_id"])
).sum()

print(
    f"Cards → Accounts      : "
    f"{invalid:,} invalid"
)


# ==================================================
# 8. Transaction quality checks
# ==================================================

print("\n")
print("=" * 70)
print("TRANSACTION DATA QUALITY")
print("=" * 70)

print(
    "Total transactions       :",
    f"{len(transactions):,}"
)

print(
    "NULL customer IDs        :",
    f"{transactions['customer_id'].isna().sum():,}"
)

print(
    "Negative amounts         :",
    f"{(transactions['amount'] < 0).sum():,}"
)

print(
    "Invalid account IDs      :",
    f"{(transactions['account_id'] == 'INVALID_ACCOUNT').sum():,}"
)

print(
    "NULL branch IDs          :",
    f"{transactions['branch_id'].isna().sum():,}"
)

print(
    "Duplicate transaction IDs:",
    f"{transactions['transaction_id'].duplicated().sum():,}"
)


# ==================================================
# 9. Transaction date range
# ==================================================

transactions["transaction_timestamp"] = pd.to_datetime(
    transactions["transaction_timestamp"]
)

print("\n")
print("=" * 70)
print("TRANSACTION DATE RANGE")
print("=" * 70)

print(
    "Earliest transaction:",
    transactions["transaction_timestamp"].min()
)

print(
    "Latest transaction  :",
    transactions["transaction_timestamp"].max()
)


# ==================================================
# 10. Transaction volume by year/month
# ==================================================

transactions["year_month"] = (
    transactions["transaction_timestamp"]
    .dt.to_period("M")
)

monthly_volume = (
    transactions
    .groupby("year_month")
    .size()
)

print("\n")
print("=" * 70)
print("MONTHLY TRANSACTION VOLUME")
print("=" * 70)

print(monthly_volume)


# ==================================================
# 11. Transaction amount analysis
# ==================================================

print("\n")
print("=" * 70)
print("TRANSACTION AMOUNT ANALYSIS")
print("=" * 70)

print(
    "Total transaction amount :",
    f"{transactions['amount'].sum():,.2f}"
)

print(
    "Average transaction      :",
    f"{transactions['amount'].mean():,.2f}"
)

print(
    "Maximum transaction      :",
    f"{transactions['amount'].max():,.2f}"
)

print(
    "Minimum transaction      :",
    f"{transactions['amount'].min():,.2f}"
)


# ==================================================
# 12. Channel analysis
# ==================================================

print("\n")
print("=" * 70)
print("TRANSACTIONS BY CHANNEL")
print("=" * 70)

print(
    transactions["channel"]
    .value_counts()
)


# ==================================================
# 13. Transaction type analysis
# ==================================================

print("\n")
print("=" * 70)
print("TRANSACTIONS BY TYPE")
print("=" * 70)

print(
    transactions["transaction_type"]
    .value_counts()
)


# ==================================================
# 14. Customer account distribution
# ==================================================

print("\n")
print("=" * 70)
print("ACCOUNTS PER CUSTOMER")
print("=" * 70)

accounts_per_customer = (
    accounts
    .groupby("customer_id")
    .size()
)

print(
    "Customers with accounts:",
    f"{accounts_per_customer.count():,}"
)

print(
    "Customers without accounts:",
    f"{len(customers) - accounts_per_customer.count():,}"
)

print(
    "Average accounts/customer:",
    f"{accounts_per_customer.mean():.2f}"
)

print(
    "Maximum accounts/customer:",
    f"{accounts_per_customer.max()}"
)


# ==================================================
# 15. Final summary
# ==================================================

print("\n")
print("=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)

total_size_mb = sum(
    (RAW_DIR / filename).stat().st_size
    for filename in expected_files
    if (RAW_DIR / filename).exists()
) / (1024 * 1024)

print(
    f"Total raw data size: "
    f"{total_size_mb:.2f} MB"
)

print("\nAll expected datasets have been inspected.")