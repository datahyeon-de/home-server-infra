# 🏗️ Home-Server Infrastructure: IaC on Proxmox Cluster

"Automated, Hybrid, and Resource-Optimized Infrastructure"

> 이 레포지토리는 6대의 Mini PC를 활용한 **Proxmox VE 8.x 클러스터** 환경에서 고가용성 데이터 플랫폼을 구축하기 위한 **Infrastructure as Code (IaC)** 관리 도구입니다. Ansible을 통해 Bare-metal 상의 VM 프로비저닝부터 K8s 클러스터링, 하이브리드 모니터링 체계 구축까지의 전 과정을 자동화합니다.

## 📌 Infrastructure Focus

본 인프라는 저사양 Mini PC 환경에서 초당 3,000건 이상의 Spike 트래픽(Kafka/Spark)을 견뎌낼 수 있는 목표를 설정하고 **가변형 리소스 할당(Throttling)** 및 **워크로드 격리**에 초점을 두고 설계하고 있습니다.

- **Proxmox Automation**: Proxmox API 및 Ansible을 연동하여 12대 이상의 VM을 10분 내에 일관되게 배포.
- **Hybrid Architecture**: 데이터 지속성이 중요한 Kafka/MinIO/DB는 독립 VM으로, 연산 확장성이 필요한 Spark/Airflow는 K8s 상에 배치하여 안정성과 유연성 동시 확보.
- **Resource Engineering**: 호스트별 물리 코어 및 메모리 한계를 고려한 3단계 자원 할당 전략(Basic/Core/High-Load) 적용.

## 🏗️ Infrastructure Architecture

### 📊 Physical 6-Node Cluster Configuration
물리적 하드웨어 사양에 맞춘 최적의 워크로드 배치 전략입니다.

| Node | Physical Spec | Assigned Roles (VMs) | Strategy |
| :--- | :--- | :--- | :--- |
| **Server 01** | 6c/12t, 32GB | `kafka-01`, `k8s-master-01` | **Control Plane & Ingestion** |
| **Server 02** | 6c/12t, 32GB | `kafka-02`, `k8s-worker-01` | **Message Broker & Services** |
| **Server 03** | 8c/16t, 32GB | `kafka-03`, `k8s-worker-02` | **Spark Compute (High-Load)** |
| **Server 04** | 8c/16t, 32GB | `minio-server`, `k8s-worker-03` | **Storage I/O & Spark Compute** |
| **Server 05** | 8c/16t, 32GB | `postgres-dw`, `k8s-worker-04` | **DW Persistence & Data Gen** |
| **Server 06** | 8c/16t, 32GB | `vm-bastion`, `k8s-worker-05` | **Management & Monitoring** |

### 🖥️ Resource Allocation Strategy
- **Basic (2C/4G)**: 모니터링 에이전트, 데이터 생성기 등 일반 서비스.
- **Core (4C/8G)**: Kafka Broker, K8s Master, MinIO, PostgreSQL 등 핵심 인프라.
- **High-Load (6C/12G)**: 실질적인 데이터 연산을 담당하는 Spark Worker 전용.

### ⚙️ Software Environment & Versioning
| 분류 | 컴포넌트 | 현재 버전 (Current) | 상태 및 추천 버전 (Note / Recommended) |
| :--- | :--- | :--- | :--- |
| **Infra** | **Proxmox VE** | 9.1.0 (Kernel 6.17) | 최신 메이저 버전 운영 중 |
| | **Kubernetes** | v1.35.0 | Control Plane & Nodes 일치 (최신) |
| | **Nginx (Bastion)** | 1.24.0 (Ubuntu) | 외부 게이트웨이용 |
| | **Nginx (Ingress)** | 1.27.1 (Chart 4.14.1) | K8s 내부 컨트롤러 v1.14.1 기반 |
| | **Ansible** | core 2.15.13 | Python 3.12.3 venv 기반 운영 중 |
| | **Python** | 3.12.3 | Bastion/Airflow 메인 런타임 |
| **Data** | **Apache Airflow** | 2.10.4 (Chart 1.15.0) | App 2.9.3 기반에서 2.10.4 이미지 교체됨 |
| | **Apache Spark** | 3.5.7 | Scala 2.12 / Java 11 기반 (AWS 커스텀 이미지) |
| | **Spark Operator** | 2.4.0 | K8s 내 Spark Job 관리용 |
| | **Kafka (Confluent)** | 6.2.14-ccs | Confluent 6.2 계열 안정 버전 |
| | **Zookeeper** | 3.8.5 | Kafka와 연동된 안정 버전 |
| | **MinIO** | RELEASE.2025-04-22 | 웹 UI 제공의 마지막 버전의 오브젝트 스토리지 |
| | **PostgreSQL** | **설치 예정** | **추천: 17.2** (Spark/Airflow 메타 DB용 최적) |
| | **Delta Lake** | **설치 예정** | **추천: 3.3.0** (Spark 3.5.x와 완벽 호환) |
| | **dbt-core** | **설치 예정** | **추천: 1.9.1** (Python 3.12와 안정적 연동) |
| **Mon** | **Prometheus (K8s)** | 3.8.1 | K8s 내부 메트릭 수집용 (v0.87.1 Operator) |
| | **Prometheus (VM)** | 3.0.1 | 16번 VM (Host-VM) 외부 수집용 |
| | **Grafana** | 12.3.1 | 통합 대시보드 시각화 (v12 최신) |
| **Network** | **Calico (CNI)** | v3.26.1 | K8s 네트워크 및 보안 정책 담당 |

## 🛠️ Key Components & Management
- **Provisioning**: `ansible-playbook` 기반의 VM Lifecycle 관리 (Clone, Migrate, Cloud-init injection).
- **Networking**: Tailscale VPN 기반의 관리망 및 Nginx Ingress를 통한 단일 진입점(Bastion) 구축.
- **Storage**: 각 노드의 Local-LVM을 주 저장소로 사용하고, NFS를 템플릿 및 초기 배포용으로 활용.
- **Observability**: Host VM(Node Exporter)과 K8s Pod 지표를 통합하여 물리 서버와 논리 서비스 간의 상관관계 분석 가능.

## 📂 Repository Structure (Infra-Specific)
```bash
.
├── docs                              # 인프라 사양서 및 기술 결정 로그 (ai-context)
│   └── ai-context
├── img
├── k8s                               # Helm 기반의 플랫폼 스택 설정 (values.yaml)
│   ├── airflow
│   ├── prom-grfana
│   └── spark-operator
└── playbooks
    ├── 01-provision-vms              # Proxmox API 연동 VM 생성 자동화
    │   └── tasks
    ├── 02-modify-vm-resources        # 실시간 리소스 Throttling/Scaling 적용
    │   └── tasks
    ├── 03-setup-monitoring-services  # Prometheus/Grafana 모니터링 에이전트 배포
    ├── group_vars
    ├── inventory                     # 인프라 자원 관리 (hosts.ini, vm_list.yml)
    ├── tests
    │   ├── k8s-base
    │   ├── kvm-test
    │   ├── resource-throttling
    │   └── ubuntu-base
    └── vars
```

## 📈 Infrastructure Roadmap & Status
- [x] Proxmox VM Provisioning (12.29~12.30): Ansible 기반 VM 12대 자동화 배포 완료.
- [x] K8s Cluster Initialization (12.31): v1.31 클러스터 구축 및 CNI/StorageClass 설정 완료.
- [x] Resource Scaling Strategy (01.03): Spark 연산 노드 대상 6C/12G 리소스 Throttling 적용.
- [x] Unified Monitoring (01.05): VM 및 K8s 지표 통합 대시보드 v12 구축 완료.
- [x] Bastion Gateway (01.06): Nginx 기반 L7 도메인 프록시 및 Ingress 연동 완료.
- [ ] Infra Optimization (01.07~): Spike 트래픽 시 Proxmox Host 부하 분석 및 튜닝.

## 🤖 AI Agent & Collaboration Rules
이 프로젝트는 AI Thought Partner와 협업하여 문서 중심 개발(Spec-driven Development) 을 수행합니다.
- **Commit Message**: type: Verb Description #issue (예: feat: Add Spark streaming #12)
- **Context Log**: 모든 주요 의사결정은 docs/ai-context/에 실시간으로 기록됩니다. 세션 재개 시 에이전트는 해당 로그를 읽어 맥락을 복구합니다.

## 🔗 Repository Roles
- 이 레포지토리는 전체 CRM 데이터 플랫폼의 **"신경망과 골격"** 을 담당합니다.
- 비즈니스 로직 및 Spark 코드는 `data-platform-core` 에서 관리합니다.
- 부하 생성 및 테스트 시나리오는 `data-generator` 에서 관리합니다.

### 📂 Repository Structure

| Repository | Description | Key Tech |
|------------|-------------|----------|
| `home-server-infra` | 기반 시설 및 K8s/Kafka 클러스터 제어 | Ansible, Proxmox, K8s, Kafka |
| `data-platform-core` | 비즈니스 로직 및 데이터 가공 엔진 | Spark, dbt, Airflow, Delta Lake |
| `data-generator` | 부하 테스트용 데이터 및 시나리오 생성 | Python, Faker, Redis |

## 📧 Contact
[hyeondata@gmail.com]

