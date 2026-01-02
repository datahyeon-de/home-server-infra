# Issue #3-07: Spark Operator, MinIO Integration & History Server Setup

## 1. 개요
Kubernetes(Proxmox 환경)에서 Spark Operator를 통해 실행되는 Spark Job과 MinIO(S3 호환 저장소)를 연동하고, 이벤트 로그를 기록하여 Spark History Server(SHS)에서 모니터링할 수 있는 데이터 파이프라인 인프라를 구축한다.

## 2. 데이터 레이크 아키텍처 및 경로 규칙
효율적인 데이터 관리를 위해 `datalake` 버킷 하나로 통합하고 내부 디렉토리 구조를 다음과 같이 정의한다.

* **이벤트 로그**: `s3a://datalake/logs/spark-log/`
* **테스트 데이터**: `s3a://datalake/data/test/`
* **비즈니스 데이터**: `s3a://datalake/data/{domain}/{table_name}/`

---

## 3. 주요 트러블슈팅 및 해결 방안

### ❌ 이슈 1: `java.lang.IllegalArgumentException: path must be absolute`
* **현상**: SHS 및 Spark Job 기동 시 `s3a://` 경로를 인식하지 못하고 종료됨.
* **원인**: 
    1. 하둡 S3A 핸들러(`S3AFileSystem`)가 등록되지 않아 `s3a` 주소를 로컬 파일 경로로 오인함.
    2. S3 버킷의 루트(`s3a://bucket/`)에 직접 쓰려고 할 때 하둡 라이브러리가 경로 해석 오류를 일으킴.
* **해결**: 
    * `spark.hadoop.fs.s3a.impl` 명시적 설정.
    * 경로 사용 시 반드시 **하위 폴더(Sub-directory)**를 포함하여 명시 (`s3a://datalake/logs/spark-log/`).

### ❌ 이슈 2: `AuthorizationHeaderMalformed: 'ap-northeast-2'`
* **현상**: MinIO 연결 시 400 Bad Request 에러 발생.
* **원인**: AWS SDK가 인증 헤더를 생성할 때 기본 리전 정보를 포함하나, MinIO는 이를 해석하지 못함.
* **해결**: 
    * 리전을 **`us-east-1`**로 강제 고정.
    * 서명 알고리즘을 **`S3SignerType`**으로 명시하여 리전 체크 무력화.

### ❌ 이슈 3: SHS 기동 시 `FileNotFoundException` (Directory not found)
* **현상**: SHS가 기동되자마자 에러를 뱉으며 종료됨.
* **원인**: 오브젝트 스토리지는 파일이 없으면 해당 Prefix(폴더)가 논리적으로 존재하지 않음. SHS는 감시할 디렉토리가 없으면 죽도록 설계됨.
* **해결**: 
    * `mc cp` 명령어로 해당 경로에 **더미 파일**을 생성하거나, **Spark Job을 먼저 실행**하여 로그 디렉토리를 물리적으로 생성함.

### ❌ 이슈 4: `java.lang.Exception: spark.executor.extraJavaOptions is not allowed...`
* **현상**: SparkApplication 실행 시 유효성 검사 에러 발생.
* **원인**: Spark 3.x부터 자바 옵션 필드에 `spark.xxx` 설정을 넣는 것을 금지함.
* **해결**: 
    * Spark Operator YAML 스펙에 맞춰 `driver.javaOptions` 필드를 사용하거나, 모든 설정을 `sparkConf` 섹션으로 통합함.

### ❌ 이슈 5: Parquet 저장 중 `FileNotFoundException` (Rename failure)
* **현상**: 데이터 쓰기 작업 마지막 단계에서 임시 파일(`_temporary`)을 찾지 못해 실패함.
* **원인**: S3/MinIO의 비원자적(Non-atomic) Rename 특성 때문임.
* **해결**: 
    * **`FileOutputCommitter` 알고리즘 버전 2**를 사용하여 Rename 과정을 최적화함.

---

## 4. 최종 확정 코드 및 설정

### ① `minio-test.py`
```python
from pyspark.sql import SparkSession
import os

access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
endpoint = "[http://192.168.0.14:9000](http://192.168.0.14:9000)"

spark = SparkSession.builder \
    .appName("spark-minio-test") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.endpoint", endpoint) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.endpoint.region", "us-east-1") \
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.EnvironmentVariableCredentialsProvider") \
    .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2") \
    .getOrCreate()

data = [("Proxmox", 6), ("Kubernetes", 5), ("MinIO-Connected", 1)]
df = spark.createDataFrame(data, ["infrastructure", "count"])

target_path = "s3a://datalake/data/test/"

try:
    df.write.mode("overwrite").parquet(target_path)
    print("--- Write Success! ---")
    spark.read.parquet(target_path).show()
except Exception as e:
    print(f"Failed: {e}")

spark.stop()
```

### ② spark-minio-test.yaml
```yaml
apiVersion: "sparkoperator.k8s.io/v1beta2"
kind: SparkApplication
metadata:
  name: spark-minio-test
spec:
  type: Python
  mode: cluster
  image: "hyeondata/spark-py-aws:3.5.7-v1"
  mainApplicationFile: "local:///opt/spark/work-dir/minio-test.py"
  sparkVersion: "3.5.7"
  sparkConf:
    "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem"
    "spark.hadoop.fs.s3a.endpoint": "[http://192.168.0.14:9000](http://192.168.0.14:9000)"
    "spark.hadoop.fs.s3a.path.style.access": "true"
    "spark.hadoop.fs.s3a.aws.credentials.provider": "com.amazonaws.auth.EnvironmentVariableCredentialsProvider"
    "spark.hadoop.fs.s3a.metadatastore.impl": "org.apache.hadoop.fs.s3a.s3guard.NullMetadataStore"
    "spark.hadoop.fs.s3a.endpoint.region": "us-east-1"
    "spark.hadoop.fs.s3a.signing-algorithm": "S3SignerType"
    "spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version": "2"
    "spark.eventLog.enabled": "true"
    "spark.eventLog.dir": "s3a://datalake/logs/spark-log/"
  driver:
    cores: 1
    memory: "512m"
    serviceAccount: spark-sa
    env:
      - name: AWS_ACCESS_KEY_ID
        valueFrom: { secretKeyRef: { name: minio-s3-keys, key: access-key } }
      - name: AWS_SECRET_ACCESS_KEY
        valueFrom: { secretKeyRef: { name: minio-s3-keys, key: secret-key } }
    volumeMounts:
      - name: "test-script"
        mountPath: "/opt/spark/work-dir"
  executor:
    cores: 1
    instances: 1
    memory: "512m"
    env:
      - name: AWS_ACCESS_KEY_ID
        valueFrom: { secretKeyRef: { name: minio-s3-keys, key: access-key } }
      - name: AWS_SECRET_ACCESS_KEY
        valueFrom: { secretKeyRef: { name: minio-s3-keys, key: secret-key } }
  volumes:
    - name: "test-script"
      configMap:
        name: spark-test-script
```

### ③ spark-history-server.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: spark-history-server
spec:
  clusterIP: None
  selector:
    app: spark-history-server
  ports:
    - port: 18080
      targetPort: 18080
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spark-history-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: spark-history-server
  template:
    metadata:
      labels:
        app: spark-history-server
    spec:
      nodeSelector:
        workload-type: monitoring
      containers:
      - name: spark-history-server
        image: "hyeondata/spark-py-aws:3.5.7-v1"
        args: ["/opt/spark/bin/spark-class", "org.apache.spark.deploy.history.HistoryServer"]
        env:
        - name: SPARK_HISTORY_OPTS
          value: >-
            -Dspark.history.fs.logDirectory=s3a://datalake/logs/spark-log/
            -Dspark.hadoop.fs.s3a.endpoint=[http://192.168.0.14:9000](http://192.168.0.14:9000)
            -Dspark.hadoop.fs.s3a.path.style.access=true
            -Dspark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem
            -Dspark.hadoop.fs.s3a.aws.credentials.provider=com.amazonaws.auth.EnvironmentVariableCredentialsProvider
            -Dspark.hadoop.fs.s3a.endpoint.region=us-east-1
            -Dspark.hadoop.fs.s3a.signing-algorithm=S3SignerType
            -Dspark.hadoop.fs.s3a.metadatastore.impl=org.apache.hadoop.fs.s3a.s3guard.NullMetadataStore
        - name: AWS_ACCESS_KEY_ID
          valueFrom: { secretKeyRef: { name: minio-s3-keys, key: access-key } }
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom: { secretKeyRef: { name: minio-s3-keys, key: secret-key } }
        ports:
        - containerPort: 18080
```

---

## 5. 인프라 설정 (Ingress Nginx)

### Monitoring 노드에 Ingress Controller를 배치하여 외부 브라우저에서 History Server UI에 접속한다.
* **설치**: Helm 사용 (monitoring 노드 셀렉터 포함)
* **접속 도메인**: spark-history.local
* **접속 방법**: PC의 `hosts` 파일에 `Monitoring_Node_IP spark-history.local` 등록 후 `http://spark-history.local:{NodePort}` 접속

---

## 6. 결론

### MinIO와 같은 S3 호환 저장소 연동 시 경로의 절대성, 리전 고정, 커미터 알고리즘 세 가지가 핵심임을 확인하였다. 본 인프라를 바탕으로 향후 대규모 가상 데이터셋을 활용한 파이프라인 실습을 진행한다.
