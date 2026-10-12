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

NUM_TRANSACTIONS = 200_000


# --------------------------------------------------
# 2. Load existing data
# --------------------------------------------------

accounts_df = pd.read_csv(
    RAW_DIR / "accounts.csv"
)

branches_df = pd.read_csv(
    RAW_DIR / "branches.csv"
)


# --------------------------------------------------
# 3. Create account lookup
# --------------------------------------------------
# This allows us to find the customer and branch
# belonging to an account.

account_lookup = (
    accounts_df[
        [
            "account_id",
            "customer_id",
            "branch_id",
            "currency"
        ]
    ]
    .set_index("account_id")
)


account_ids = accounts_df["account_id"].tolist()


# --------------------------------------------------
# 4. Reference values
# --------------------------------------------------

transaction_types = [
    "DEPOSIT",
    "WITHDRAWAL",
    "TRANSFER",
    "PAYMENT",
    "FEE",
    "ATM",
    "POS",
]

channels = [
    "BRANCH",
    "ATM",
    "MOBILE",
    "INTERNET",
    "POS",
]

statuses = [
    "SUCCESS",
    "FAILED",
    "REVERSED",
]


# --------------------------------------------------
# 5. Generate transactions
# --------------------------------------------------

transactions = []

for i in range(1, NUM_TRANSACTIONS + 1):

    transaction_id = f"T{i:07d}"

    # Select an existing account
    account_id = random.choice(account_ids)

    # Get account information
    account_info = account_lookup.loc[account_id]

    customer_id = account_info["customer_id"]
    branch_id = account_info["branch_id"]
    currency = account_info["currency"]

    # Generate timestamp within approximately
    # the last 3 years
    random_days = random.randint(0, 1095)
    random_seconds = random.randint(0, 86399)

    transaction_timestamp = (
        pd.Timestamp("2023-01-01")
        + pd.Timedelta(days=random_days)
        + pd.Timedelta(seconds=random_seconds)
    )

    transaction_type = random.choices(
        transaction_types,
        weights=[
            20,  # DEPOSIT
            15,  # WITHDRAWAL
            20,  # TRANSFER
            15,  # PAYMENT
            5,   # FEE
            15,  # ATM
            10,  # POS
        ],
        k=1
    )[0]

    channel = random.choices(
        channels,
        weights=[
            15,  # BRANCH
            25,  # ATM
            30,  # MOBILE
            20,  # INTERNET
            10,  # POS
        ],
        k=1
    )[0]

    status = random.choices(
        statuses,
        weights=[
            97,
            2,
            1,
        ],
        k=1
    )[0]

    # Transaction amount
    amount = round(
        np.random.lognormal(
            mean=7,
            sigma=1.2
        ),
        2
    )

    # Occasionally generate very small fees
    if transaction_type == "FEE":
        amount = round(
            random.uniform(10, 500),
            2
        )

    debit_credit = random.choice(
        ["DEBIT", "CREDIT"]
    )

    transactions.append(
        {
            "transaction_id": transaction_id,
            "account_id": account_id,
            "customer_id": customer_id,
            "transaction_timestamp": transaction_timestamp,
            "transaction_date": transaction_timestamp.date(),
            "transaction_type": transaction_type,
            "channel": channel,
            "branch_id": branch_id,
            "amount": amount,
            "currency": currency,
            "debit_credit": debit_credit,
            "status": status,
        }
    )


# --------------------------------------------------
# 6. Create DataFrame
# --------------------------------------------------

transactions_df = pd.DataFrame(transactions)


# --------------------------------------------------
# 7. Introduce intentional data-quality problems
# --------------------------------------------------
# DO NOT fix these.
#
# Spark will handle them later.


# 20 NULL customer IDs
null_customer_indices = np.random.choice(
    transactions_df.index,
    size=20,
    replace=False
)

transactions_df.loc[
    null_customer_indices,
    "customer_id"
] = None


# 20 negative amounts
negative_indices = np.random.choice(
    transactions_df.index,
    size=20,
    replace=False
)

transactions_df.loc[
    negative_indices,
    "amount"
] *= -1


# 10 invalid account IDs
invalid_account_indices = np.random.choice(
    transactions_df.index,
    size=10,
    replace=False
)

transactions_df.loc[
    invalid_account_indices,
    "account_id"
] = "INVALID_ACCOUNT"


# 10 NULL branch IDs
null_branch_indices = np.random.choice(
    transactions_df.index,
    size=10,
    replace=False
)

transactions_df.loc[
    null_branch_indices,
    "branch_id"
] = None


# --------------------------------------------------
# 8. Create duplicate transaction IDs
# --------------------------------------------------
# Select 10 existing transactions and duplicate
# their transaction IDs.

duplicate_indices = np.random.choice(
    transactions_df.index,
    size=10,
    replace=False
)

for index in duplicate_indices:

    source_index = random.choice(
        list(transactions_df.index)
    )

    transactions_df.loc[
        index,
        "transaction_id"
    ] = transactions_df.loc[
        source_index,
        "transaction_id"
    ]


# --------------------------------------------------
# 9. Save
# --------------------------------------------------

output_path = RAW_DIR / "transactions.csv"

transactions_df.to_csv(
    output_path,
    index=False,
    encoding="utf-8"
)


# --------------------------------------------------
# 10. Basic validation
# --------------------------------------------------

print("=" * 60)
print("BankScale - Transaction Generator")
print("=" * 60)

print(
    f"\nTransactions generated : "
    f"{len(transactions_df):,}"
)

print(
    f"Unique transaction IDs : "
    f"{transactions_df['transaction_id'].nunique():,}"
)

print("\nTransaction type distribution:")
print(
    transactions_df["transaction_type"]
    .value_counts()
)

print("\nChannel distribution:")
print(
    transactions_df["channel"]
    .value_counts()
)

print("\nStatus distribution:")
print(
    transactions_df["status"]
    .value_counts()
)


# --------------------------------------------------
# 11. Data-quality problems
# --------------------------------------------------

print("\nIntentional data-quality problems:")

print(
    "NULL customer IDs :",
    transactions_df["customer_id"].isna().sum()
)

print(
    "Negative amounts  :",
    (transactions_df["amount"] < 0).sum()
)

print(
    "Invalid accounts  :",
    (
        transactions_df["account_id"]
        == "INVALID_ACCOUNT"
    ).sum()
)

print(
    "NULL branch IDs   :",
    transactions_df["branch_id"].isna().sum()
)

print(
    "Duplicate IDs     :",
    transactions_df["transaction_id"]
    .duplicated()
    .sum()
)


# --------------------------------------------------
# 12. Relationship validation
# --------------------------------------------------

valid_accounts = (
    transactions_df["account_id"]
    .isin(accounts_df["account_id"])
)

print("\nAccount relationship:")
print(
    "Invalid account references :",
    (~valid_accounts).sum()
)


print("\nFile created:")
print(output_path)

print("\nTransaction generation completed successfully.")