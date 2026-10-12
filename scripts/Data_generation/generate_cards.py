import pandas as pd
import random
from pathlib import Path


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

random.seed(42)

BASE_DIR = Path(r"D:\BankScale")
RAW_DIR = BASE_DIR / "data" / "raw"

NUM_CARDS = 8_000


# --------------------------------------------------
# 2. Load existing data
# --------------------------------------------------

customers_df = pd.read_csv(
    RAW_DIR / "customers.csv"
)

accounts_df = pd.read_csv(
    RAW_DIR / "accounts.csv"
)

customer_ids = customers_df["customer_id"].tolist()
account_ids = accounts_df["account_id"].tolist()


# --------------------------------------------------
# 3. Create account → customer lookup
# --------------------------------------------------

account_lookup = (
    accounts_df[
        [
            "account_id",
            "customer_id"
        ]
    ]
    .set_index("account_id")
)


# --------------------------------------------------
# 4. Reference values
# --------------------------------------------------

card_types = [
    "DEBIT",
    "CREDIT",
]

networks = [
    "VISA",
    "MASTERCARD",
]

statuses = [
    "ACTIVE",
    "BLOCKED",
    "EXPIRED",
]


# --------------------------------------------------
# 5. Generate cards
# --------------------------------------------------

cards = []

for i in range(1, NUM_CARDS + 1):

    card_id = f"CARD{i:06d}"

    # Select an existing account
    account_id = random.choice(account_ids)

    # IMPORTANT:
    # Customer comes from the selected account.
    customer_id = account_lookup.loc[
        account_id,
        "customer_id"
    ]

    card_type = random.choices(
        card_types,
        weights=[
            75,  # DEBIT
            25,  # CREDIT
        ],
        k=1
    )[0]

    network = random.choice(networks)

    issue_date = (
        pd.Timestamp("2019-01-01")
        + pd.to_timedelta(
            random.randint(0, 2555),
            unit="D"
        )
    )

    # Card normally valid for approximately 5 years
    expiry_date = (
        issue_date
        + pd.DateOffset(years=5)
    )

    status = random.choices(
        statuses,
        weights=[
            85,  # ACTIVE
            5,   # BLOCKED
            10,  # EXPIRED
        ],
        k=1
    )[0]

    cards.append(
        {
            "card_id": card_id,
            "customer_id": customer_id,
            "account_id": account_id,
            "card_type": card_type,
            "network": network,
            "issue_date": issue_date.date(),
            "expiry_date": expiry_date.date(),
            "status": status,
        }
    )


# --------------------------------------------------
# 6. Create DataFrame
# --------------------------------------------------

cards_df = pd.DataFrame(cards)


# --------------------------------------------------
# 7. Save
# --------------------------------------------------

output_path = RAW_DIR / "cards.csv"

cards_df.to_csv(
    output_path,
    index=False,
    encoding="utf-8"
)


# --------------------------------------------------
# 8. Validation
# --------------------------------------------------

print("=" * 60)
print("BankScale - Card Generator")
print("=" * 60)

print(
    f"\nCards generated : "
    f"{len(cards_df):,}"
)

print("\nCard type distribution:")
print(
    cards_df["card_type"]
    .value_counts()
)

print("\nNetwork distribution:")
print(
    cards_df["network"]
    .value_counts()
)

print("\nCard status distribution:")
print(
    cards_df["status"]
    .value_counts()
)


# --------------------------------------------------
# 9. Relationship validation
# --------------------------------------------------

invalid_customers = (
    ~cards_df["customer_id"].isin(
        customers_df["customer_id"]
    )
).sum()

invalid_accounts = (
    ~cards_df["account_id"].isin(
        accounts_df["account_id"]
    )
).sum()

duplicate_cards = (
    cards_df["card_id"].duplicated()
).sum()


# Check whether customer_id actually
# matches the customer's account
account_customer_check = (
    cards_df[
        ["card_id", "account_id", "customer_id"]
    ]
    .merge(
        accounts_df[
            ["account_id", "customer_id"]
        ],
        on="account_id",
        how="left",
        suffixes=(
            "_card",
            "_account"
        )
    )
)

incorrect_customer_relationships = (
    account_customer_check["customer_id_card"]
    !=
    account_customer_check["customer_id_account"]
).sum()


print("\nRelationship validation:")

print(
    f"Invalid customer IDs : "
    f"{invalid_customers}"
)

print(
    f"Invalid account IDs  : "
    f"{invalid_accounts}"
)

print(
    f"Duplicate card IDs   : "
    f"{duplicate_cards}"
)

print(
    f"Incorrect customer/account relationships : "
    f"{incorrect_customer_relationships}"
)


print("\nFile created:")
print(output_path)

print("\nCard generation completed successfully.")