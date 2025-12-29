# 프로젝트 정의서 #1

## 1. 프로젝트 개요 (Project Overview)

### 제목
고가용성 하이브리드 인프라 기반 실시간 CRM 데이터 파이프라인 구축

### 목표
- 저수준 트래픽부터 대규모 부하(Spike) 상황까지 유연하게 대응하는 데이터 엔지니어링 역량 증명
- 실제 비즈니스 시나리오(CRM)를 바탕으로 데이터 수집-저장-가공-시각화 전 과정을 1주일 내 구현
- 단순 구축을 넘어 인프라 최적화 및 트래픽 폭주 시의 해결 과정을 성과로 도출

## 2. 레포지토리 구성 (Repository Strategy)

| 레포지토리 명 | 역할 및 포함 내용 |
|--------------|------------------|
| `home-server-infra` | 기반 시설 (Base)<br>- Proxmox 호스트 제어 및 VM 생성 (Ansible)<br>- K8s 클러스터 구성 및 관리<br>- Kafka 클러스터(3-Node) 및 모니터링(Prometheus/Grafana) 인프라 설치 |
| `data-platform-core` | 비즈니스 엔진 (Logic)<br>- Spark on K8s (Streaming/Batch) 로직<br>- dbt 기반의 DW/DM 모델링<br>- Airflow DAG (워크플로우 자동화) 및 비즈니스 데이터 처리 스키마 |
| `data-generator` | 부하 생성기 (Source)<br>- Python 기반 데이터 생성기<br>- Spike 시나리오(트래픽 급증) 및 1년치 데이터 백필 생성 로직 |

## 3. 기술 스택 및 데이터 아키텍처 (Technical Stack)

### 3.1 계층별 상세 스택

- **Infrastructure**: Proxmox VE 8.x, Ubuntu 24.04 LTS, Kubernetes(K8s)
- **Message Broker**: Confluent Kafka (3-Node VM Cluster, Zookeeper Quorum)
- **Storage Layer**: MinIO (Object Storage) + Delta Lake (ACID 트랜잭션 및 Time Travel 보장)
- **Processing**: Spark Structured Streaming / Batch (on K8s Operator)
- **Transformation**: dbt (PostgreSQL DW 기반 데이터 모델링)
- **Monitoring**: Prometheus Operator, Grafana (VM 및 K8s 서비스 상태 모니터링)

## 4. 데이터 시나리오 및 분석 주제

### 4.1 주요 엔티티

- **Events**: 유저 행동 로그 (Page View, Add to Cart, Click 등)
- **Orders**: 결제 완료 및 취소 데이터
- **Products**: 상품 마스터 데이터 (카테고리, 가격, 재고)
- **Profiles**: 고객 마스터 (등급, 세그먼트, 가입 정보)

### 4.2 부하 시나리오

- **Normal**: 평상시 저수준 트래픽 처리 (10~100 TPS)
- **Spike**: 특정 이벤트 발생 시 급격한 트래픽 증가 (3K TPS 이상) 상황 재현
- **Resolution**: 컨슈머 렉(Lag) 발생 시 파티션 확장, Spark 리소스 동적 할당 등을 통한 해결 과정 기록

## 5. 작업 및 협업 규칙 (AI Agent Friendly)

### 5.1 커밋 메시지 규칙

#### 기본 형식

**형식**: `접두어: 동사(대문자 시작) 기능설명 #이슈번호`

**구성 요소**:
- **접두어 (Type)**: 변경 유형을 나타내는 키워드 (소문자)
- **동사 (Verb)**: 동작을 나타내는 동사 (대문자로 시작, 명령형 사용 권장)
- **기능설명**: 변경 사항에 대한 간결한 설명 (50자 이내 권장)
- **이슈번호**: 관련 이슈 번호 (# 뒤에 숫자)

#### 접두어 (Type) 종류

| 접두어 | 사용 시점 | 예시 |
|--------|----------|------|
| `feat` | 새로운 기능 추가 | `feat: Add Kafka consumer for Events #12` |
| `fix` | 버그 수정 | `fix: Correct Spark job memory allocation #15` |
| `docs` | 문서 수정/추가 | `docs: Update deployment guide #8` |
| `perf` | 성능 개선 | `perf: Optimize Delta Lake write operations #20` |
| `refactor` | 코드 리팩토링 (기능 변경 없음) | `refactor: Simplify dbt model structure #18` |
| `chore` | 빌드/설정 파일 변경 | `chore: Update Ansible playbook for VM setup #5` |
| `test` | 테스트 코드 추가/수정 | `test: Add integration test for streaming pipeline #22` |

#### 커밋 메시지 작성 예시

```
feat: Add Product entity to streaming source #13

- Kafka producer에 Product 마스터 데이터 생성 로직 추가
- 상품 카테고리, 가격, 재고 정보 포함
- 스키마 버전 v1.0 적용

Related to: data-generator
```

#### 작성 가이드라인

1. **첫 번째 줄**: 핵심 메시지 (50자 이내 권장)
2. **빈 줄**: 첫 번째 줄과 본문 구분
3. **본문**: 변경 이유, 영향 범위, 관련 이슈 등 상세 설명
4. **동사 사용**: 
   - ✅ `Add`, `Fix`, `Update`, `Remove`, `Implement`
   - ❌ `Added`, `Fixed`, `Updates`, `Adding`
5. **명확성**: 무엇을(What) 변경했는지 명확히 표현
6. **이슈 번호**: 항상 포함 (이슈가 없는 경우 제외 가능)

### 5.2 이슈 및 컨텍스트 관리

- 각 레포지토리의 `docs/ai-context/` 디렉토리에 이슈별 대화 기록 및 기술 결정 사안 보존
- 터미널 세션 재시작 시, 에이전트가 해당 디렉토리를 읽어 이전 맥락을 즉시 파악하도록 유도

## 6. 1주일 로드맵
- [Day 1-2] 인프라 구축: Proxmox VM 생성 자동화, K8s/Kafka/MinIO 클러스터 가동.

- [Day 3-4] 소스 개발: data-generator 개발 및 Kafka Ingestion, Spark 기초 파이프라인 연결.

- [Day 5-6] 고도화 및 분석: Delta Lake 적재, dbt 모델링, Grafana 모니터링 대시보드 완성.

- [Day 7] 테스트 및 최적화: Spike 부하 테스트 및 해결 과정 문서화, 최종 데모 영상 준비.
