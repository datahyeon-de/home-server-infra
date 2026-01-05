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
  - Kafka: 192.168.0.11 ~ 13 (전용 SSH 키 사용)
  - Prometheus A: 192.168.0.16
  - K8s Cluster: 192.168.0.30 ~ 35
  - 기타: MinIO(14), Postgres(15)

## 3. 주요 작업 내용 및 자동화 (Ansible)

### 3.1 에이전트(Exporter) 통합 설치
- **Node Exporter (v1.10.2)**: OS 기본 매트릭 수집. 물리 호스트는 `--collector.hwmon` 옵션을 통해 온도 수집 활성화.
- **Process Exporter (v0.8.7)**: `config.yml` 설정을 통해 모든 프로세스(`{{.Comm}}`)의 개별 자원 점유율 수집.
- **lm-sensors**: 물리 호스트의 하드웨어 온도 감지를 위해 설치 및 `sensors-detect` 자동화.
- **Ansible 특이사항**: 
  - `all:vars`로 공통 SSH 키(`id_rsa`)를 설정하되, `kafka_servers:vars`에서 전용 키(`kafka-ssh`)를 설정하여 변수 우선순위 적용.

### 3.2 Prometheus A (VM 16) 서버 구축
- **버전**: Prometheus v3.0.1 (최신 메이저 버전)
- **설정**: 
  - `proxmox-nodes`: 101~106 노드의 9100 포트 수집.
  - `vm-nodes`: K8s 및 일반 VM의 9100 포트 수집.
  - `process-stats`: 전 서버의 9256 포트 수집.
- **운영**: `systemd`를 통한 서비스 상주화 및 `/var/lib/prometheus` 데이터 영구 저장소 구성.

## 4. [트러블슈팅 기록] 시행착오와 해결

### 4.1 Prometheus v3.0 변경점 대응
- **문제**: 플레이북 실행 중 `consoles` 폴더 복사 실패.
- **원인**: v3.0부터 레거시 콘솔 템플릿이 삭제됨.
- **해결**: 플레이북에서 관련 복사 태스크 및 서비스 실행 플래그 제거.

### 4.2 Systemd 문법 오류 (Backslash)
- **문제**: 서비스 실행 시 `Error parsing command line arguments: unexpected Restart=always`.
- **원인**: `ExecStart` 명령어 끝에 백슬래시(`\`)가 중복되어 `Restart=always` 지시어를 실행 인자로 오인함.
- **해결**: 마지막 인자 줄의 백슬래시를 제거하여 명령어와 지시어를 명확히 분리.

### 4.3 YAML 문법 오류 (Quoting)
- **문제**: `too many colons in address` 에러 발생.
- **원인**: `targets` 리스트 중 `192.168.0.16:9100`에만 싱글 따옴표(`'`)가 누락되어 콜론(`:`)이 특수 문자로 해석됨.
- **해결**: 모든 타겟 주소를 따옴표로 감싸 문자열로 명시하여 해결.

## 5. 검증 및 확인
- **터널링**: 로컬 PC에서 `ssh -L 9090:192.168.0.16:9090`을 통해 접속 환경 구축.
- **데이터 확인**: `Status -> Targets`에서 19개 엔드포인트 모두 **UP** 상태 확인 완료.
- **온도 데이터**: `node_hwmon_temp_celsius` 매트릭을 통해 AMD 라이젠 호스트의 온도 수집 정상 확인.

## 6. 향후 계획
- **Issue #3-12**: K8s 내부 Grafana 설치 및 Prometheus A(VM 16) + Prometheus B(K8s 내부) 통합 대시보드 구축.