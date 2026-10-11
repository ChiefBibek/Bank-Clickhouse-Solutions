from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("New Spark Session").getOrCreate()

df = spark.read.option('header','true').option('inferSchema','true').option('delimiter',',').csv('D:/BankScale/data/raw/customers.csv')

cust_bagmati = df.filter(df.province == 'Bagmati') #transformation

cust_bagmati.show(n = 10 , truncate = False) #action

print("The total no. of customers in bagmati province is: ", cust_bagmati.count()) 

