from pyspark.sql import SparkSession
import os

access_key = os.getenv("ACCESS_KEY") # Secret의 키값과 맞춰야 함
secret_key = os.getenv("SECRET_KEY")
endpoint = os.getenv("S3_ENDPOINT", "http://192.168.0.14:9000")

print(f"DEBUG: Access Key exists: {access_key is not None}")

if not access_key or not secret_key:
    raise ValueError("MinIO credentials are missing in environment variables!")

spark = SparkSession.builder \
    .appName("spark-minio-test") \
    .config("spark.hadoop.fs.s3a.access.key", access_key) \
    .config("spark.hadoop.fs.s3a.secret.key", secret_key) \
    .config("spark.hadoop.fs.s3a.endpoint", endpoint) \
    .getOrCreate()

# 테스트 데이터 생성
data = [("Proxmox-Node", 6), ("K8s-Worker", 5), ("MinIO-Connected", 1)]
columns = ["infrastructure", "count"]
df = spark.createDataFrame(data, columns)

# MinIO에 Parquet 파일로 쓰기 (s3a 경로 사용)
target_path = "s3a://datalake/test-output"
print(f"Writing data to {target_path}...")

try:
    df.write.mode("overwrite").parquet(target_path)
    print("Write Success!")

    # 다시 읽어서 확인
    print("Reading data back from MinIO...")
    read_df = spark.read.parquet(target_path)
    read_df.show()
    print("Read Success!")
except Exception as e:
    print(f"Connection Failed: {str(e)}")

spark.stop()
