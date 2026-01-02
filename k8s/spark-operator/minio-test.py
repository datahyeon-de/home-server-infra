from pyspark.sql import SparkSession
import os

access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
endpoint = "http://192.168.0.14:9000"

spark = SparkSession.builder \
    .appName("spark-minio-test") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.endpoint", endpoint) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.endpoint.region", "us-east-1") \
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.EnvironmentVariableCredentialsProvider") \
    .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2") \
    .getOrCreate()

data = [("Proxmox", 1), ("Kubernetes", 1), ("MinIO-Final-Victory", 1)]
df = spark.createDataFrame(data, ["item", "count"])

# 사용자님이 찾으신 해결책: 하위 폴더 명시
target_path = "s3a://datalake/test-output/"

try:
    print(f"Target Path: {target_path}")
    df.write.mode("overwrite").parquet(target_path)
    print("Write Success!")
    spark.read.parquet(target_path).show()
except Exception as e:
    print(f"Error occurred: {e}")

spark.stop()