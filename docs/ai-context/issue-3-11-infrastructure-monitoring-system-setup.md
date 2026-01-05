# Issue #3-11: Full-Stack Infrastructure Monitoring with Dual Prometheus Setup

## 📅 날짜: 2026-01-05
## 👤 참여자: [임성현], Gemini

## 1. 이슈 개요
- **목표**: 6대의 물리 호스트(Proxmox)와 13대 이상의 VM(Kafka, K8s, DB 등)에 대한 자원 사용량, 하드웨어 온도, 프로세스별 매트릭을 수집하는 중앙 집중형 모니터링 체계 구축.
- **결과**: 모든 서버에 Exporter 배치 완료, VM 16번에 Prometheus A(중앙 서버) 설치 및 19개 타겟 연동 성공.

## 2. 인프라 구성 현황
- **Host Servers (Proxmox)**: 192.168.0.101 ~ 106 (계정: `datahyeon`)
- **VM Servers**: 
  - Bastion: 192.168.0.100
  - Kafka: 192.168.0.11 ~ 13 (전용 SSH 키 `kafka-ssh` 사용)
  - Prometheus A: 192.168.0.16 (CentOS/Ubuntu VM)
  - K8s Cluster: 192.168.0.30 ~ 35 (Master 1, Worker 5)
  - 기타: MinIO(14), Postgres(15)

## 3. 주요 작업 내용 및 자동화 (Ansible)

### 3.1 에이전트(Exporter) 통합 설치 및 전략 변경
- **Node Exporter (v1.10.2)**: 
  - 모든 서버에 배포. 물리 호스트(101~106)는 `--collector.hwmon` 옵션을 통해 AMD 라이젠 CPU 온도 수집 활성화.
  - **[중요 결정]**: 초기에는 K8s 노드(30~35)도 VM 16번 Prometheus에서 수집하도록 설정했으나, 이후 K8s 내부 헬름 차트(Prometheus B)와의 포트(9100) 충돌 및 데이터 중복을 방지하기 위해 **K8s 노드들의 수동 node_exporter 서비스를 중단하고 VM 16번 수집 대상에서 제외함.**
- **Process Exporter (v0.8.7)**: `config.yml` 설정을 통해 모든 프로세스(`{{.Comm}}`)의 개별 자원 점유율 수집.
- **lm-sensors**: 물리 호스트의 하드웨어 온도 감지를 위해 설치 및 `sensors-detect` 자동화.
- **Ansible 특이사항**: 
  - `all:vars`로 공통 SSH 키(`id_rsa`)를 설정하되, `kafka_servers:vars`에서 전용 키(`kafka-ssh`)를 설정하여 변수 우선순위 적용.

### 3.2 Prometheus A (VM 16) 서버 구축
- **버전**: Prometheus v3.0.1 (최신 메이저 버전)
- **설정 (`prometheus.yml`)**: 
  - `proxmox-nodes`: 101~106 노드의 9100 포트 수집.
  - `kafka-nodes`: 11~13 노드 수집.
  - `vm-nodes`: K8s를 제외한 일반 VM(10, 14, 15, 16)의 9100 포트 수집 (K8s 노드는 헬름 차트로 이관).
  - `process-stats`: 물리 서버 및 전체 VM의 9256 포트 수집.

## 4. [트러블슈팅 기록] 시행착오와 해결

### 4.1 Prometheus v3.0 변경점 대응
- **문제**: 플레이북 실행 중 `consoles` 및 `console_libraries` 폴더 복사 실패.
- **원인**: v3.0부터 해당 레거시 폴더들이 기본 바이너리에서 삭제됨.
- **해결**: Ansible 플레이북에서 관련 복사 태스크를 제거하여 설치 완료.

### 4.2 Systemd 문법 오류 (Backslash)
- **문제**: 서비스 실행 시 `Error parsing command line arguments: unexpected Restart=always`.
- **원인**: `ExecStart` 명령어의 마지막 인자 줄 끝에 백슬래시(`\`)가 포함되어 다음 줄인 `Restart=always`를 실행 옵션으로 인식함.
- **해결**: 명령어 마지막 줄의 백슬래시를 제거하여 `Restart` 지시어와 분리.

### 4.3 YAML 문법 오류 (Quoting)
- **문제**: `too many colons in address` 에러 발생.
- **원인**: `targets` 리스트 중 `192.168.0.16:9100` 주소에 싱글 따옴표(`'`)가 누락되어 YAML 파서가 콜론을 특수 문자로 오인함.
- **해결**: 모든 주소값을 따옴표로 감싸 명시적 문자열로 처리.

## 5. 검증 및 확인
- **터널링**: 로컬 PC에서 `ssh -L 9090:192.168.0.16:9090`을 통해 Prometheus UI 접속 환경 구축.
- **데이터 확인**: `Status -> Targets`에서 16번 VM이 수집하는 물리 서버 및 기타 VM 타겟들이 **UP** 상태임을 확인.