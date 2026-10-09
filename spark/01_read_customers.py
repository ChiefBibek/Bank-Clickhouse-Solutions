from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
spark = SparkSession.builder.appName("Read Customers").getOrCreate()

df = spark.read.option('header','true').option('inferSchema','true').option('delimiter',',').csv('D:/BankScale/data/raw/customers.csv')


print('Schema of the DataFrame:')
df.printSchema() # Check the schema of the DataFrame

print('Data in the DataFrame:')
df.show(n = 5, truncate = False) # Show the first 5 rows of the DataFrame without truncating the values

print("The total no. of records in the DataFrame is: ", df.count()) # Count the total number of records in the DataFrame

spark.stop() # Stop the SparkSession    