# Issue #3-09: Airflow Infrastructure Resource Provisioning & Security Setup

## 📅 날짜: 2026-01-02
## 👤 참여자: [임성현], Gemini

## 1. 이슈 개요
- **목표**: Airflow 설치 전 필수 인프라 자원(Namespace, Storage, Security)을 확보하고, 메타데이터 보존 및 로그 연동을 위한 환경 구축.
- **결과**: `airflow` 네임스페이스 생성, `manual` StorageClass 및 PV/PVC 배포 완료, MinIO 내 Airflow 전용 권한 설정 완료.

## 2. 주요 성과 및 대화 요약
- **Namespace 격리**: Airflow 운영 자원을 별도로 관리하기 위해 `airflow` 네임스페이스를 생성하고 모든 PVC 리소스를 해당 스코프 내에 배치.
- **Static Persistence 구축**: `manual` StorageClass와 `k8s-worker-01` 노드에 종속된 50GB PV/PVC를 생성하여 PostgreSQL 메타데이터의 영속성 확보.
- **로그 저장소 보안 강화**: MinIO에 `airflow-admin` 계정을 생성하고, `datalake` 버킷의 로그 경로에 특화된 `airflow-log-policy`를 적용하여 보안성 제고.

## 3. 기술적 의사결정 및 트러블슈팅

### 3.1 StorageClass 및 정적 프로비저닝 (Static Provisioning)
- **결정**: `provisioner: kubernetes.io/no-provisioner`를 사용하는 `manual` StorageClass 정의.
- **이유**: 클러스터 내 자동 프로비저너가 없는 환경에서 사용자가 물리적으로 추가한 디스크를 PV와 PVC에 정확하게 바인딩하기 위함. `volumeBindingMode: WaitForFirstConsumer`를 설정하여 파드 스케줄링 시점에 최종 바인딩되도록 유도.

### 3.2 리소스 네임스페이스 바인딩 (Namespaced PVC)
- **트러블슈팅**: PVC는 특정 네임스페이스에 종속되므로, Helm 배포가 이루어질 `airflow` 네임스페이스에 PVC가 존재해야 함을 확인.
- **조치**: `airflow` 네임스페이스 생성 후, 해당 네임스페이스를 명시한 PVC 매니페스트를 재배포하여 Helm 차트와의 연동성 확보.

### 3.3 MinIO 기반 Remote Logging 보안 정책
- **정책 내용**: `datalake/logs/airflow-logs/*` 경로에 대해서만 `PutObject`, `GetObject`, `DeleteObject` 권한을 허용하는 최소 권한 정책 수립.
- **설정**: `mc` 명령어를 통해 `airflow-log-policy` 정책을 등록하고 `airflow-admin` 사용자에게 연결 완료.

## 4. 결론 및 향후 계획
- **결론**: Airflow 실행을 위한 '땅(Storage)'과 '열쇠(MinIO Key)' 준비가 최종 완료되었으며, 인프라 준비 단계에서 발생할 수 있는 자원 바인딩 오류를 사전에 방지함.
- **차기 과제**: 
    1. Apache Airflow 공식 Helm Chart 레포지토리 추가.
    2. `KubernetesExecutor`, `Git-Sync`, `S3 Logging` 설정을 포함한 최종 `values.yaml` 작성.
    3. Airflow 서비스 배포 및 가동 테스트.

---
**💡 Action Item**: 모든 리소스(SC, PV, PVC, MinIO User)가 준비되었으므로, 차기 단계에서 최종 Helm 배포용 `values.yaml` 구성을 진행할 예정임.