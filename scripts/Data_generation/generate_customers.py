import pandas as pd
import numpy as np
import random
from faker import Faker
from pathlib import Path

# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

random.seed(42)
np.random.seed(42)

fake = Faker()
Faker.seed(42)

BASE_DIR = Path(r"D:\BankScale")
RAW_DIR = BASE_DIR / "data" / "raw"

RAW_DIR.mkdir(parents=True, exist_ok=True)

NUM_CUSTOMERS = 10_000


# --------------------------------------------------
# 2. Reference values
# --------------------------------------------------

provinces = [
    "Koshi",
    "Madhesh",
    "Bagmati",
    "Gandaki",
    "Lumbini",
    "Karnali",
    "Sudurpashchim",
]

cities = [
    "Kathmandu",
    "Lalitpur",
    "Bhaktapur",
    "Pokhara",
    "Biratnagar",
    "Birgunj",
    "Butwal",
    "Nepalgunj",
    "Dharan",
    "Bharatpur",
    "Janakpur",
    "Dhangadhi",
    "Birendranagar",
]

genders = [
    "MALE",
    "FEMALE",
    "OTHER",
]

occupations = [
    "SALARIED",
    "BUSINESS",
    "STUDENT",
    "SELF_EMPLOYED",
    "RETIRED",
    "PROFESSIONAL",
    "OTHER",
]

customer_segments = [
    "RETAIL",
    "PREMIUM",
    "SALARY",
    "BUSINESS",
    "STUDENT",
]

risk_categories = [
    "LOW",
    "MEDIUM",
    "HIGH",
]


# --------------------------------------------------
# 3. Generate customers
# --------------------------------------------------

customers = []

for i in range(1, NUM_CUSTOMERS + 1):

    customer_id = f"C{i:06d}"

    first_name = fake.first_name()
    last_name = fake.last_name()

    date_of_birth = fake.date_of_birth(
        minimum_age=18,
        maximum_age=75
    )

    gender = random.choice(genders)

    city = random.choice(cities)
    province = random.choice(provinces)

    occupation = random.choice(occupations)

    customer_segment = random.choice(customer_segments)

    registration_date = fake.date_between(
        start_date="-10y",
        end_date="today"
    )

    # Weighted risk distribution
    risk_category = random.choices(
        risk_categories,
        weights=[70, 25, 5],
        k=1
    )[0]

    customers.append(
        {
            "customer_id": customer_id,
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": date_of_birth,
            "gender": gender,
            "city": city,
            "province": province,
            "occupation": occupation,
            "customer_segment": customer_segment,
            "registration_date": registration_date,
            "risk_category": risk_category,
        }
    )


# --------------------------------------------------
# 4. Create DataFrame
# --------------------------------------------------

customers_df = pd.DataFrame(customers)


# --------------------------------------------------
# 5. Save
# --------------------------------------------------

output_path = RAW_DIR / "customers.csv"

customers_df.to_csv(
    output_path,
    index=False,
    encoding="utf-8"
)


# --------------------------------------------------
# 6. Validation
# --------------------------------------------------

print("=" * 60)
print("BankScale - Customer Generator")
print("=" * 60)

print(f"\nCustomers generated : {len(customers_df):,}")

print("\nColumns:")
print(customers_df.columns.tolist())

print("\nFirst 5 customers:")
print(customers_df.head())

print("\nCustomer segment distribution:")
print(customers_df["customer_segment"].value_counts())

print("\nRisk distribution:")
print(customers_df["risk_category"].value_counts())

print("\nUnique customer IDs:")
print(customers_df["customer_id"].nunique())

print("\nFile created:")
print(output_path)

print("\nCustomer generation completed successfully.")