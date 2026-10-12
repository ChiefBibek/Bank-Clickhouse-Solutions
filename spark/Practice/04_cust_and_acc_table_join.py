from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("CustomerAccountJoin").getOrCreate()

cust_df = spark.read.csv("D:/BankScale/data/raw/customers.csv", header=True, inferSchema=True)
acc_df = spark.read.csv("D:/BankScale/data/raw/accounts.csv", header=True, inferSchema=True)

joined_df = cust_df.join(acc_df, cust_df.customer_id == acc_df.customer_id, "inner")



joined_df.select(cust_df["customer_id"], "first_name", "province", "account_id", "account_type", "current_balance").show(n=10, truncate=False)