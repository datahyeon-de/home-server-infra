# Issue #3-01: 플랫폼 스택 배치를 위한 자원 재할당 및 노드 전략 수립

## 📅 날짜: 2025-12-30
## 👤 참여자: 임성현, Gemini

## 1. 이슈 개요
- **목표**: Spark Operator 및 데이터 플랫폼 스택(Kafka, MinIO, Airflow)의 안정적 구동을 위해 기존 VM 자원을 최적화하고 K8s 노드 레이블링 전략을 수립함.
- **결과**: 각 컴포넌트별 권장 vCPU/Memory 할당안 도출 및 용도별 노드 태깅 계획 수립 완료.

## 2. 주요 성과 및 대화 요약
- **자원 불균형 해소**: 물리 서버의 스펙 차이(6c/12t vs 8c/16t)를 고려하여 Spark 워커와 Kafka 브로커의 자원을 차등 배분함으로써 병목 현상 방지.
- **노드 정체성 확립**: `workload-type` 레이블링을 통해 Spark 연산, 오케스트레이션, 데이터 생성 등 각 역할별로 노드를 논리적으로 격리함.
- **대화 요약**: Spark Operator 설치에 앞서, 인프라의 확장성과 성능을 보장하기 위한 하드웨어 수준의 자원 할당과 K8s 스케줄링 전략을 구체화함.

## 3. 기술적 의사결정 및 트러블슈팅
- **기술적 선택**: Spark Executor의 성능을 극대화하기 위해 물리 자원이 넉넉한 서버군을 활용하도록 배치 계획 수립.
- **트러블슈팅**: (예정) Proxmox에서 VM 리소스 수정 후 K8s 노드 `Ready` 상태 확인 및 배분된 자원이 스케줄러에 정상 반영되는지 검토.

## 4. 결론 및 향후 계획
- **결론**: 플랫폼의 기반이 되는 자원 맵(Resource Map)이 확정되었으며, 이를 토대로 인프라 구성을 변경함.
- **차기 과제**: 확정된 사양으로 VM 수정 후, Spark Operator 설치 및 MinIO 연동 테스트 진행.

---

### [부록] 세부 자원 및 레이블링 계획

#### 1. VM 자원 재할당 안 (vCPU / RAM) 💻
| VM 구분 | Hostname | 추천 사양 | 사유 |
| :--- | :--- | :--- | :--- |
| **K8s Master** | `k8s-master-01` | 4 / 8GB | API Server 및 컨트롤 플레인 안정성 |
| **Spark Worker** | `k8s-worker-01~02` | 6 / 12GB | 실질적인 데이터 연산 핵심 노드 |
| **Airflow/Service**| `k8s-worker-03` | 4 / 8GB | Scheduler 및 Web UI 구동용 |
| **Kafka Broker** | `kafka-01~03` | 4 / 8GB | JVM Heap 및 OS Page Cache 확보 |
| **Storage/DB** | `minio`, `postgres`| 4 / 8GB | I/O 처리 및 쿼리 연산 성능 확보 |
| **Monitoring** | `k8s-worker-05` | 4 / 8GB | Prometheus/Grafana 부하 반영 |

#### 2. K8s 노드 레이블링 전략 🏷️
- **Spark 전용**: `kubectl label nodes k8s-worker-01 workload-type=spark-executor`
- **공통 서비스**: `kubectl label nodes k8s-worker-03 workload-type=orchestration`
- **데이터 생성**: `kubectl label nodes k8s-worker-04 workload-type=data-gen`