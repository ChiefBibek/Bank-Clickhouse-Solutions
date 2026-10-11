from pyspark.sql import SparkSession
from pyspark.sql.functions import count,col
spark = SparkSession.builder.appName("NewSpark").getOrCreate()

cust_df = spark.read.csv("D:/BankScale/data/raw/customers.csv", header=True, inferSchema=True)
acc_df = spark.read.csv("D:/BankScale/data/raw/accounts.csv", header=True, inferSchema=True)

joined_df = cust_df.join(acc_df, "customer_id", "inner")

execution_df = joined_df.groupBy("customer_id", "first_name").agg(count("account_id").alias("account_count")).filter(col("account_count")>1)

execution_df.explain()

spark.stop()