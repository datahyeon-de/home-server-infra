from pyspark.sql import SparkSession
import os

# 환경 변수 및 엔드포인트 설정
access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
endpoint = os.getenv("S3_ENDPOINT", "http://192.168.0.14:9000")

spark = SparkSession.builder \
    .appName("spark-minio-test") \
    .config("spark.hadoop.fs.s3a.access.key", access_key) \
    .config("spark.hadoop.fs.s3a.secret.key", secret_key) \
    .config("spark.hadoop.fs.s3a.endpoint", endpoint) \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.metadatastore.impl", "org.apache.hadoop.fs.s3a.s3guard.NullMetadataStore") \
    .config("spark.hadoop.fs.s3a.endpoint.region", "us-east-1") \
    .config("spark.hadoop.fs.s3a.signing-algorithm", "S3SignerType") \
    .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2") \
    .getOrCreate()

# 테스트 데이터 생성
data = [("Proxmox-Node", 6), ("K8s-Worker", 5), ("MinIO-Success", 1)]
df = spark.createDataFrame(data, ["infrastructure", "count"])

# 반드시 하위 폴더(test-output)를 포함한 경로 사용
target_path = "s3a://datalake/test-output/"

try:
    print(f"Writing data to {target_path}...")
    df.write.mode("overwrite").parquet(target_path)
    print("Write Success!")
    
    print("Reading data back...")
    read_df = spark.read.parquet(target_path)
    read_df.show()
    print("Read Success!")
except Exception as e:
    print(f"Operation Failed: {str(e)}")

spark.stop()