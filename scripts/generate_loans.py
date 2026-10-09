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

NUM_LOANS = 3_000


# --------------------------------------------------
# 2. Load existing data
# --------------------------------------------------

customers_df = pd.read_csv(
    RAW_DIR / "customers.csv"
)

branches_df = pd.read_csv(
    RAW_DIR / "branches.csv"
)

customer_ids = customers_df["customer_id"].tolist()
branch_ids = branches_df["branch_id"].tolist()


# --------------------------------------------------
# 3. Reference values
# --------------------------------------------------

loan_types = [
    "PERSONAL",
    "HOME",
    "AUTO",
    "EDUCATION",
    "BUSINESS",
]

statuses = [
    "ACTIVE",
    "CLOSED",
    "DEFAULTED",
]


# --------------------------------------------------
# 4. Generate loans
# --------------------------------------------------

loans = []

for i in range(1, NUM_LOANS + 1):

    loan_id = f"L{i:06d}"

    customer_id = random.choice(customer_ids)
    branch_id = random.choice(branch_ids)

    loan_type = random.choices(
        loan_types,
        weights=[
            35,  # PERSONAL
            20,  # HOME
            15,  # AUTO
            10,  # EDUCATION
            20,  # BUSINESS
        ],
        k=1
    )[0]

    # Generate principal based on loan type
    if loan_type == "PERSONAL":
        principal = random.uniform(50_000, 1_000_000)

    elif loan_type == "HOME":
        principal = random.uniform(
            1_000_000,
            15_000_000
        )

    elif loan_type == "AUTO":
        principal = random.uniform(
            500_000,
            5_000_000
        )

    elif loan_type == "EDUCATION":
        principal = random.uniform(
            100_000,
            2_000_000
        )

    else:
        principal = random.uniform(
            500_000,
            10_000_000
        )

    principal = round(principal, 2)

    # Interest rate
    interest_rate = round(
        random.uniform(7.0, 15.0),
        2
    )

    # Loan start date
    start_date = (
        pd.Timestamp("2018-01-01")
        + pd.to_timedelta(
            random.randint(0, 2920),
            unit="D"
        )
    )

    # Loan duration: 1–20 years
    duration_months = random.choice([
        12,
        24,
        36,
        48,
        60,
        84,
        120,
        180,
        240,
    ])

    maturity_date = (
        start_date
        + pd.DateOffset(
            months=duration_months
        )
    )

    status = random.choices(
        statuses,
        weights=[
            80,  # ACTIVE
            15,  # CLOSED
            5,   # DEFAULTED
        ],
        k=1
    )[0]

    loans.append(
        {
            "loan_id": loan_id,
            "customer_id": customer_id,
            "branch_id": branch_id,
            "loan_type": loan_type,
            "principal_amount": principal,
            "interest_rate": interest_rate,
            "start_date": start_date.date(),
            "maturity_date": maturity_date.date(),
            "status": status,
        }
    )


# --------------------------------------------------
# 5. Create DataFrame
# --------------------------------------------------

loans_df = pd.DataFrame(loans)


# --------------------------------------------------
# 6. Save
# --------------------------------------------------

output_path = RAW_DIR / "loans.csv"

loans_df.to_csv(
    output_path,
    index=False,
    encoding="utf-8"
)


# --------------------------------------------------
# 7. Validation
# --------------------------------------------------

print("=" * 60)
print("BankScale - Loan Generator")
print("=" * 60)

print(
    f"\nLoans generated : "
    f"{len(loans_df):,}"
)

print("\nLoan type distribution:")
print(
    loans_df["loan_type"]
    .value_counts()
)

print("\nLoan status distribution:")
print(
    loans_df["status"]
    .value_counts()
)

print("\nTotal principal amount:")
print(
    f"NPR {loans_df['principal_amount'].sum():,.2f}"
)


# --------------------------------------------------
# 8. Relationship validation
# --------------------------------------------------

invalid_customers = (
    ~loans_df["customer_id"].isin(
        customers_df["customer_id"]
    )
).sum()

invalid_branches = (
    ~loans_df["branch_id"].isin(
        branches_df["branch_id"]
    )
).sum()

duplicate_loans = (
    loans_df["loan_id"].duplicated()
).sum()


print("\nRelationship validation:")
print(
    f"Invalid customer IDs : {invalid_customers}"
)

print(
    f"Invalid branch IDs   : {invalid_branches}"
)

print(
    f"Duplicate loan IDs   : {duplicate_loans}"
)


print("\nFile created:")
print(output_path)

print("\nLoan generation completed successfully.")