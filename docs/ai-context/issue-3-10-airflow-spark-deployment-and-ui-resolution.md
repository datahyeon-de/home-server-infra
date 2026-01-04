# Issue #3-10: Airflow & Spark Operator Deployment and UI Ingress Resolution

## 📅 날짜: 2026-01-03 ~ 2026-01-04
## 👤 참여자: [임성현], Gemini

## 1. 이슈 개요
- **목표**: Apache Airflow 및 Spark Operator를 실환경에 배포하고, 제출된 잡의 실시간/히스토리 UI 가시성을 확보하는 엔드투엔드 파이프라인 구축.
- **결과**: `KubernetesExecutor` 기반 Airflow 가동, Spark UI 인그레스 접속 성공, Spark History Server와 MinIO 연동 완료.

## 2. 주요 성과 및 상세 과정

### 2.1 Airflow 서비스 배포 및 자동화 구성
- **Executor 설정**: 클러스터 리소스의 효율적 활용을 위해 `KubernetesExecutor`를 채택하여 테스크별 독립 파드 생성 구조 확립.
- **Git-Sync 연동**: `data-platform-core` 레포지토리와 연동하여 DAG 파일의 실시간 동기화 및 형상 관리 체계 구축.
- **원격 로그(Remote Logging)**: MinIO를 S3 백엔드로 사용하여 `datalake/logs/airflow-logs/` 경로에 워커 로그가 영구 저장되도록 설정.

### 2.2 Spark Operator 및 History Server 인프라 구축
- **Spark Operator**: Helm을 통해 `uiIngress` 기능을 활성화하고, `urlFormat` 설정을 통해 잡 생성 시 인그레스 자동 생성 로직 주입.
- **History Server**: Spark 잡 종료 후에도 로그를 분석할 수 있도록 MinIO 버킷(`s3a://datalake/logs/spark-log/`)과 History Server를 완벽히 연동함.

### 2.3 [핵심 트러블슈팅] Spark UI 접속 불능 및 경로 불일치 해결
- **문제 현상**: 인그레스 생성 후 접속 시 `503 Service Unavailable` 발생 및 `//jobs/`와 같은 비정상적인 경로로 리다이렉트되며 UI 깨짐 현상 발생.
- **원인 분석**:
    1. **Suffix(난수) 메커니즘**: Spark Operator가 잡 제출 시 이름 뒤에 무작위 접미사(예: `-jhcjbr18`)를 붙여 생성하므로, 고정된 DAG 설정값과 불일치 발생.
    2. **Ingress Path Mismatch**: 사용자는 `/long-test-.../`로 접속했으나, 오퍼레이터가 실제 생성한 경로는 `/spark-ui/spark/<appName>/`였음.
- **해결 조치**:
    - **Path 정규화**: `kubectl describe ingress`로 실제 매핑된 Prefix를 확인하고, 브라우저 접속 URL을 해당 경로와 100% 일치시킴.
    - **Nginx Rewrite**: `rewrite-target: /` 어노테이션과 `x-forwarded-prefix` 설정을 조율하여 드라이버 파드 내부로 트래픽을 정확히 전달.
    - **UI 깨짐 방지**: `spark.ui.proxyBase` 설정을 상대 경로 혹은 인그레스 경로와 동기화하여 CSS/JS 정적 자원 로딩 성공.



## 3. 기술적 의사결정 기록 (Key Decisions)
- **SSH 터널링 기반 외부 접속**: 외부 망에서 Bastion 서버를 거쳐 K8s 노드의 인그레스 노드포트(30998)로 연결되는 로컬 포트 포워딩(`-L 8080:...`) 환경 구축.
- **Metadata 관리**: 3년의 실무 경험을 바탕으로, 폐쇄망 환경에서 관리하지 못했던 프로젝트 이력을 보완하기 위해 모든 인프라 설치 및 트러블슈팅 과정을 문서화하여 공유 가능한 형태로 관리하기로 결정.

## 4. 결론 및 향후 계획
- **결론**: 데이터 플랫폼의 핵심인 스케줄러(Airflow)와 연산 엔진(Spark)의 연동 및 외부 모니터링 체계를 성공적으로 안착시킴. 특히 6대의 미니 PC 환경에서 발생하는 분산 처리 환경의 복잡성을 인그레스 설정 최적화로 극복함.
- **차기 과제 (Monitoring System Setup)**:
    1. **Host-Server 모니터링**: 물리 Mini PC 6대 및 데스크탑의 하드웨어 상태 감시.
    2. **VM & K8s 노드 모니터링**: Proxmox 위에서 돌아가는 각 VM 및 쿠버네티스 클러스터 리소스 사용량 추적.
    3. **대시보드 통합**: Prometheus와 Grafana를 도입하여 인프라 전체에 대한 통합 관제 시스템 구축.

---
**💡 Action Item**: 차기 세션에서는 `Node Exporter`와 `Prometheus Operator`를 활용하여 호스트부터 컨테이너까지 이어지는 모니터링 스택 구축을 진행할 예정임.