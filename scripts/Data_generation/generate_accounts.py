import pandas as pd
import numpy as np
import random
from pathlib import Path


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

random.seed(42)
np.random.seed(42)

BASE_DIR = Path(r"D:\BankScale")
RAW_DIR = BASE_DIR / "data" / "raw"

NUM_ACCOUNTS = 15_000


# --------------------------------------------------
# 2. Load customers
# --------------------------------------------------

customers_path = RAW_DIR / "customers.csv"

customers_df = pd.read_csv(customers_path)

customer_ids = customers_df["customer_id"].tolist()


# --------------------------------------------------
# 3. Load branches
# --------------------------------------------------

branches_path = RAW_DIR / "branches.csv"

branches_df = pd.read_csv(branches_path)

branch_ids = branches_df["branch_id"].tolist()


# --------------------------------------------------
# 4. Reference values
# --------------------------------------------------

account_types = [
    "SAVINGS",
    "CURRENT",
    "SALARY",
]

currencies = [
    "NPR",
    "USD",
    "EUR",
]

statuses = [
    "ACTIVE",
    "DORMANT",
    "CLOSED",
]


# --------------------------------------------------
# 5. Generate accounts
# --------------------------------------------------

accounts = []

for i in range(1, NUM_ACCOUNTS + 1):

    account_id = f"A{i:06d}"

    # Select an existing customer
    customer_id = random.choice(customer_ids)

    # Select an existing branch
    branch_id = random.choice(branch_ids)

    account_type = random.choice(account_types)

    currency = random.choices(
        currencies,
        weights=[95, 3, 2],
        k=1
    )[0]

    opening_date = pd.Timestamp(
        "2016-01-01"
    ) + pd.to_timedelta(
        random.randint(0, 3650),
        unit="D"
    )

    status = random.choices(
        statuses,
        weights=[90, 7, 3],
        k=1
    )[0]

    # Generate a realistic-looking balance
    if status == "CLOSED":
        current_balance = 0
    else:
        current_balance = round(
            np.random.lognormal(
                mean=9,
                sigma=1.2
            ),
            2
        )

    accounts.append(
        {
            "account_id": account_id,
            "customer_id": customer_id,
            "branch_id": branch_id,
            "account_type": account_type,
            "currency": currency,
            "opening_date": opening_date.date(),
            "status": status,
            "current_balance": current_balance,
        }
    )


# --------------------------------------------------
# 6. Create DataFrame
# --------------------------------------------------

accounts_df = pd.DataFrame(accounts)


# --------------------------------------------------
# 7. Save
# --------------------------------------------------

output_path = RAW_DIR / "accounts.csv"

accounts_df.to_csv(
    output_path,
    index=False,
    encoding="utf-8"
)


# --------------------------------------------------
# 8. Validation
# --------------------------------------------------

print("=" * 60)
print("BankScale - Account Generator")
print("=" * 60)

print(f"\nAccounts generated : {len(accounts_df):,}")

print("\nFirst 5 accounts:")
print(accounts_df.head())

print("\nAccount type distribution:")
print(accounts_df["account_type"].value_counts())

print("\nAccount status distribution:")
print(accounts_df["status"].value_counts())

print("\nCurrency distribution:")
print(accounts_df["currency"].value_counts())


# --------------------------------------------------
# 9. Relationship validation
# --------------------------------------------------

invalid_customers = (
    ~accounts_df["customer_id"].isin(
        customers_df["customer_id"]
    )
).sum()

invalid_branches = (
    ~accounts_df["branch_id"].isin(
        branches_df["branch_id"]
    )
).sum()

duplicate_accounts = (
    accounts_df["account_id"].duplicated().sum()
)


print("\nRelationship validation:")
print(f"Invalid customer IDs : {invalid_customers}")
print(f"Invalid branch IDs   : {invalid_branches}")
print(f"Duplicate account IDs: {duplicate_accounts}")


# --------------------------------------------------
# 10. Customer account statistics
# --------------------------------------------------

accounts_per_customer = (
    accounts_df
    .groupby("customer_id")
    .size()
)

print("\nCustomer account statistics:")
print(
    f"Customers with accounts : "
    f"{accounts_per_customer.count():,}"
)

print(
    f"Maximum accounts/customer : "
    f"{accounts_per_customer.max()}"
)

print(
    f"Average accounts/customer : "
    f"{accounts_per_customer.mean():.2f}"
)


print("\nFile created:")
print(output_path)

print("\nAccount generation completed successfully.")