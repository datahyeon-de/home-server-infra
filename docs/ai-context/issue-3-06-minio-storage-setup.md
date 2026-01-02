# Issue #3-06: MinIO 데이터 레이크 구축 및 Spark-S3A 연동 최적화

## 📅 날짜: 2026-01-01
## 👤 참여자: 임성현, Gemini

## 1. 이슈 개요
- **목표**: Proxmox VM 환경에 MinIO를 구축하고, Kubernetes 상의 Spark와 S3A 프로토콜로 연동하여 홈 랩의 중앙 데이터 저장소(Data Lake)를 완성함.
- **결과**: 인프라(디스크 마운트), 보안(IAM), 애플리케이션(Spark) 레이어의 모든 설정을 완료하고, 실제 Parquet 데이터 쓰기/읽기 테스트에 성공함.

## 2. 주요 성과 및 수행 작업
### **A. 스토리지 인프라 레이어 (Infrastructure)**
- **물리 디스크 확장**: Proxmox GUI에서 500GB 가상 디스크 추가 (SSD Emulation 및 Backup 옵션 적용).
- **스토리지 마운트**: `/dev/sdb` 디스크를 `ext4`로 포맷하고, `UUID` 기반으로 `/etc/fstab`에 등록하여 재부팅 시 자동 마운트 보장.
- **전용 권한 설정**: `minio-user` 시스템 계정 생성 및 데이터 디렉토리(`/mnt/minio_data`) 소유권 부여.

### **B. 오브젝트 스토리지 거버넌스 레이어 (Governance)**
- **표준 리전 설정**: `ap-northeast-2` (Seoul) 리전 코드를 적용하여 AWS S3 표준 라이브러리와의 호환성 확보.
- **버킷 거버넌스**: `datalake` 버킷 생성 시 **Versioning**과 **Object Locking**을 활성화하여 데이터 불변성(Immutability) 시뮬레이션 환경 구축.
- **용량 제한(Quota)**: 데이터 레이크용 버킷에 100GiB Hard Quota를 설정하여 시스템 자원 보호.

### **C. 통합 및 보안 레이어 (Integration & Security)**
- **최소 권한 IAM**: `spark-user` 계정 생성 및 `datalake` 버킷에 한정된 전용 Policy(JSON) 할당.
- **K8s Secret 연동**: 배스티언 서버에서 `minio-s3-keys` 시크릿을 생성하여 Spark 파드에 안전하게 인증 정보 주입.

## 3. 주요 트러블슈팅 로그 (Critical Issues)

| 상황 | 발생 원인 | 해결책 |
| :--- | :--- | :--- |
| **서비스 무한 재시작 (Fatal)** | `Enterprise` 바이너리 설치로 인한 라이선스 키 요구 에러 | 라이선스 제약이 없는 **Community Edition (AGPLv3)** 바이너리로 교체 |
| **Exec format error** | 로컬(Mac M2/ARM64) 도커에서 추출한 바이너리와 서버(AMD64) 아키텍처 불일치 | Docker 실행 시 `--platform linux/amd64` 옵션을 강제하여 바이너리 재추출 |
| **ServiceAccount Forbidden** | YAML에 명시된 `spark-operator-spark` 계정 부재 | 기존에 권한이 검증된 **`spark-sa`** 계정으로 스펙 수정 |
| **S3A 400 Bad Request** | Spark 설정 내 리전(Region) 정보 누락 및 서명 방식 충돌 | `spark.hadoop.fs.s3a.endpoint.region` 설정 및 서명 최적화 옵션 추가 |
| **Credential Null Error** | Secret의 Key(`access-key`)와 Python 코드의 변수명(`ACCESS_KEY`) 불일치 | YAML의 `env` 섹션에서 명시적 매핑을 통해 환경 변수 주입 성공 |

## 4. 최종 검증 결과
- **테스트 시나리오**: PySpark를 통해 생성한 인프라 현황 데이터프레임을 MinIO에 Parquet로 적재 후 재조회.
- **로그 결과**:
    - `DEBUG: Access Key exists: True`
    - `Write Success!`
    - `Read Success!` (MinIO로부터 읽어온 데이터프레임 UI 출력 확인)
- **MinIO UI**: `datalake/test-output/` 경로 내 실제 `.parquet` 파일 및 메타데이터 저장 확인.

## 5. 결론 및 향후 계획
- **결론**: Spark와 MinIO 간의 데이터 통신 고속도로가 개통됨. 홈 랩의 스토리지 인프라 구축 단계 완료.
- **차기 과제**: 
    - **살아있는 데이터 시뮬레이터**: Python 기반 핀테크 데이터 생성기를 Kafka와 연동.
    - **Streaming Pipeline**: Kafka -> Spark Streaming -> MinIO 적재 파이프라인 완성.
    - **모니터링**: Spark 잡 리소스 사용량 실시간 관제 대시보드 구축.