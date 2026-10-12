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

RAW_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Branch Data
# --------------------------------------------------

branches = [
    ("BR0001", "Kathmandu Main", "Bagmati", "Kathmandu", "Kathmandu", "MAIN"),
    ("BR0002", "Lalitpur Branch", "Bagmati", "Lalitpur", "Lalitpur", "URBAN"),
    ("BR0003", "Bhaktapur Branch", "Bagmati", "Bhaktapur", "Bhaktapur", "URBAN"),
    ("BR0004", "Pokhara Branch", "Gandaki", "Kaski", "Pokhara", "MAIN"),
    ("BR0005", "Biratnagar Branch", "Koshi", "Morang", "Biratnagar", "URBAN"),
    ("BR0006", "Birgunj Branch", "Madhesh", "Parsa", "Birgunj", "URBAN"),
    ("BR0007", "Butwal Branch", "Lumbini", "Rupandehi", "Butwal", "URBAN"),
    ("BR0008", "Nepalgunj Branch", "Lumbini", "Banke", "Nepalgunj", "URBAN"),
    ("BR0009", "Dharan Branch", "Koshi", "Sunsari", "Dharan", "URBAN"),
    ("BR0010", "Bharatpur Branch", "Bagmati", "Chitwan", "Bharatpur", "URBAN"),
]

# Generate additional branches
province_locations = [
    ("Koshi", "Morang", "Biratnagar"),
    ("Koshi", "Sunsari", "Dharan"),
    ("Madhesh", "Parsa", "Birgunj"),
    ("Madhesh", "Dhanusha", "Janakpur"),
    ("Bagmati", "Kathmandu", "Kathmandu"),
    ("Bagmati", "Lalitpur", "Lalitpur"),
    ("Bagmati", "Bhaktapur", "Bhaktapur"),
    ("Bagmati", "Chitwan", "Bharatpur"),
    ("Gandaki", "Kaski", "Pokhara"),
    ("Gandaki", "Tanahun", "Damauli"),
    ("Lumbini", "Rupandehi", "Butwal"),
    ("Lumbini", "Banke", "Nepalgunj"),
    ("Karnali", "Surkhet", "Birendranagar"),
    ("Sudurpashchim", "Kailali", "Dhangadhi"),
]

branch_types = ["URBAN", "RURAL", "MAIN"]

while len(branches) < 50:
    branch_number = len(branches) + 1

    province, district, city = random.choice(province_locations)

    branches.append(
        (
            f"BR{branch_number:04d}",
            f"{city} Branch {branch_number}",
            province,
            district,
            city,
            random.choice(branch_types),
        )
    )

branches_df = pd.DataFrame(
    branches,
    columns=[
        "branch_id",
        "branch_name",
        "province",
        "district",
        "city",
        "branch_type",
    ],
)


# --------------------------------------------------
# 3. Product Data
# --------------------------------------------------

products = [
    ("P001", "Savings Account", "DEPOSIT"),
    ("P002", "Current Account", "DEPOSIT"),
    ("P003", "Salary Account", "DEPOSIT"),
    ("P004", "Fixed Deposit", "DEPOSIT"),
    ("P005", "Recurring Deposit", "DEPOSIT"),

    ("P006", "Personal Loan", "LOAN"),
    ("P007", "Home Loan", "LOAN"),
    ("P008", "Auto Loan", "LOAN"),
    ("P009", "Education Loan", "LOAN"),
    ("P010", "Business Loan", "LOAN"),

    ("P011", "Debit Card", "CARD"),
    ("P012", "Credit Card", "CARD"),

    ("P013", "Mobile Banking", "DIGITAL"),
    ("P014", "Internet Banking", "DIGITAL"),
    ("P015", "Mobile Wallet", "DIGITAL"),

    ("P016", "Remittance", "PAYMENT"),
    ("P017", "Fund Transfer", "PAYMENT"),
    ("P018", "Bill Payment", "PAYMENT"),
    ("P019", "QR Payment", "PAYMENT"),
    ("P020", "ATM Service", "PAYMENT"),
]

products_df = pd.DataFrame(
    products,
    columns=[
        "product_id",
        "product_name",
        "product_category",
    ],
)


# --------------------------------------------------
# 4. Save CSV files
# --------------------------------------------------

branches_path = RAW_DIR / "branches.csv"
products_path = RAW_DIR / "products.csv"

branches_df.to_csv(branches_path, index=False, encoding="utf-8")
products_df.to_csv(products_path, index=False, encoding="utf-8")


# --------------------------------------------------
# 5. Validation
# --------------------------------------------------

print("=" * 60)
print("BankScale - Reference Data Generator")
print("=" * 60)

print(f"\nBranches generated : {len(branches_df):,}")
print(f"Products generated : {len(products_df):,}")

print("\nBranch sample:")
print(branches_df.head())

print("\nProduct sample:")
print(products_df.head())

print("\nFiles created:")
print(branches_path)
print(products_path)

print("\nReference data generation completed successfully.")