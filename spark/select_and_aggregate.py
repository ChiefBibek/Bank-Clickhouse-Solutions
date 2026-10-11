from pyspark.sql import SparkSession
 
spark = SparkSession.builder.appName("New Spark Session").getOrCreate()



df = spark.read.option('header','true').option('inferSchema','true').option('delimiter',',').csv('D:/BankScale/data/raw/customers.csv')

cust_bagmati = df.filter(df.province == 'Bagmati') 

cust_bagmati.groupBy("customer_segment").count().show(n = 10 , truncate = False) 


spark.stop()