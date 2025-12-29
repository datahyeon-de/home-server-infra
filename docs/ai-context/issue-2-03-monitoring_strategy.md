# Issue #2-03: K8s 중심의 통합 모니터링 설계 (Revised)

## 📅 날짜: 2025-12-29
## 👤 참여자: 임성현, Gemini (AI Thought Partner)

## 💬 대화 요약
1. **Grafana 통합**: 관리 편의성과 Helm 차트 활용을 위해 Grafana를 K8s 클러스터 내부(k8s-monitor-01)에 배치하여 애플리케이션 및 인프라 대시보드를 일원화함.
2. **데이터 소스 이원화 (Multi-Prometheus)**:
   - **DataSource 1 (Internal)**: K8s 내부 Prometheus (Kube-stack). Pod, Service, Spark Job, Airflow 메트릭 수집.
   - **DataSource 2 (External)**: VM 기반 Standalone Prometheus. Proxmox 호스트(6대) 및 Kafka, MinIO, Postgres VM 메트릭 수집.
3. **접근성 및 통합**: K8s 내부에서 구동되는 Grafana가 클러스터 내부 서비스 주소와 외부 고정 IP(192.168.0.106)를 통해 두 프로메테우스의 데이터를 동시에 쿼리함.

## 🛠️ 결정된 사항
- `infra-prom-01(106)` VM은 오직 **VM/Host 메트릭 수집(Prometheus)** 전용 서버로 운영한다.
- `k8s-monitor-01(206)` 워커 노드에 **Grafana와 K8s Prometheus(Operator)**를 함께 배포한다.
- Grafana 설정에서 두 개의 Prometheus를 각각 데이터 소스로 등록하여, 하나의 대시보드에서 인프라부터 앱까지의 전체 가시성을 확보한다.

---

## 📊 최종 확정 VM 리스트 (모니터링 역할 수정 반영)

| 구분 | VM ID | Hostname | IP (192.168.0.x) | Target Node | Template | 비고 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **기존** | 100 | `vm-bastion` | .10 | server-06 | - | Tailscale/Ansible Host |
| **기존** | 101 | `kafka-01` | .11 | server-01 | - | Broker 01 |
| **기존** | 102 | `kafka-02` | .12 | server-02 | - | Broker 02 |
| **기존** | 103 | `kafka-03` | .13 | server-03 | - | Broker 03 |
| **신규** | **104** | `minio-server` | .104 | server-04 | 901 | Object Storage (VM) |
| **신규** | **105** | `postgres-dw` | .105 | server-05 | 901 | Data Warehouse (VM) |
| **신규** | **106** | **`infra-prom-01`** | .106 | **server-06** | 901 | **VM/Host Prometheus 전용** |
| **신규** | **201** | `k8s-master-01` | .201 | server-01 | 902 | Control Plane |
| **신규** | **202** | `k8s-worker-01` | .202 | server-02 | 902 | Spark Worker 01 |
| **신규** | **203** | `k8s-worker-02` | .203 | server-03 | 902 | Spark Worker 02 |
| **신규** | **204** | `k8s-worker-03` | .204 | server-04 | 902 | Airflow/Services |
| **신규** | **205** | `data-gen-worker` | .205 | server-05 | 902 | Spike Generator |
| **신규** | **206** | **`k8s-monitor-01`** | .206 | **server-06** | 902 | **Grafana + K8s Prom Stack** |

---

## 🏗️ 모니터링 아키텍처 흐름

1.  **인프라 레이어**: 6대의 Proxmox 호스트와 Kafka/MinIO/Postgres VM들에 `node-exporter` 설치.
2.  **수집 레이어 (VM)**: `infra-prom-01(106)`이 위 노드들의 메트릭을 `scrape` 하여 저장.
3.  **수집 레이어 (K8s)**: `k8s-monitor-01(206)`의 Prometheus Operator가 Pod/Service/Node 메트릭 수집.
4.  **시각화 레이어**: **K8s 내부 Grafana**가 다음 두 엔드포인트를 데이터 소스로 연결:
    * **Internal**: `http://prometheus-operated.monitoring.svc:9090`
    * **External**: `http://192.168.0.106:9090`

---
**Next Step**: `vars/vm_list.yml` 및 `group_vars/all.yml` 파일 생성 및 Ansible 플레이북 구현 시작.