# Issue #3-12: K8s Grafana Deployment, Storage Persistence, and Control Plane Metrics Resolution

## 📅 날짜: 2026-01-05
## 👤 참여자: [임성현], Gemini

## 1. 이슈 개요
- **목표**: K8s 클러스터 내부 Grafana 설치, 데이터 영구 보존 설정, K8s 핵심 컴포넌트(Control Plane) 수집 에러 해결, 그리고 외부 VM(Prometheus A) 연동.
- **핵심 난관**: Helm `values.yaml` 설정 시 기본 데이터 소스가 증발하는 현상 및 Control Plane의 `127.0.0.1` 바인딩 이슈 발생.

## 2. 세부 작업 및 기술 결정

### 2.1 스토리지 및 스케줄링 구성
- **노드 배치**: `workload-type: monitoring` 라벨을 가진 `k8s-worker-05` 노드에 모든 모니터링 파드 고정 배치.
- **물리 하드 마운트**: `worker-05`에 256Gi 신규 HDD 추가 후 `/mnt/data/monitoring`에 ext4 포맷 및 마운트 완료.
- **K8s Persistence**: 
  - `manual` StorageClass 기반 256Gi PV 생성.
  - `nodeAffinity` 설정을 통해 `k8s-worker-05` 하드웨어와 강제 바인딩.
  - `storageSpec` 설정 시 `v1` 필드 대신 `volumeClaimTemplate`을 사용하여 PVC 자동 생성 유도.

### 2.2 Grafana 설치 및 접속 환경 (SSH Tunneling Combo)
- **Helm 설치**: `kube-prometheus-stack` (v80.10.0) 기반 설치.
- **Ingress**: `grafana.local` 도메인 및 Nginx Ingress Controller를 통한 NodePort 30998 설정.
- **접속 해결**: 외부망에서 워커 노드 포트로 직접 터널링 시 `Connection refused` 발생. 
  - **해결**: `kubectl port-forward -n monitoring svc/monitoring-stack-grafana 3000:80 --address 0.0.0.0` 실행 후, 로컬 PC에서 `ssh -L 18080:localhost:3000`으로 2단계 터널링 구축하여 접속 성공.

## 3. [핵심 트러블슈팅] 문제와 해결책 (무삭제 기록)

### 3.1 K8s 핵심 컴포넌트 Scraping 실패 (Connection Refused)
- **문제**: `kube-controller-manager`, `kube-scheduler`, `etcd`, `kube-proxy` 타겟이 모두 `Down` 상태.
- **원인**: 컴포넌트들이 보안상 `127.0.0.1`에서만 메트릭을 노출하고 있음.
- **해결**:
  - **Controller/Scheduler**: `/etc/kubernetes/manifests/`의 각 `yaml` 파일에서 `--bind-address=0.0.0.0`으로 수정하여 외부 접근 허용.
  - **etcd**: `--listen-metrics-urls=http://0.0.0.0:2381` 설정 추가.
  - **kube-proxy**: ConfigMap 수정(`metricsBindAddress: 0.0.0.0:10249`) 후 DaemonSet 롤아웃 재시작.
  - **결과**: 모든 Control Plane 타겟 **UP (Green)** 확인.

### 3.2 Helm values.yaml 설정에 의한 데이터 소스 증발 사건
- **문제**: 외부 VM(Prometheus A) 연동을 위해 `values.yaml`의 `additionalDataSources` 섹션을 사용했으나, 설치 후 Grafana UI에서 K8s 내부 Prometheus를 포함한 모든 데이터 소스가 사라지고 `No Data` 발생.
- **원인**: `additionalDataSources` 설정이 차트의 기본 프로비저닝 로직과 충돌하여 기존 설정을 덮어씌움(Overwrite).
- **해결**: 
  - `values.yaml`에서 해당 설정을 삭제하여 기본 데이터 소스 복구.
  - **[최종 해결]**: Grafana에서 직접 Host-VM 프로메테우스 수동으로 추가.
  - 결과: 내부 Prometheus(K8s)와 외부 Prometheus-Host-VM(16번)이 사이좋게 목록에 공존함.

### 3.3 Helm StorageSpec 문법 오류
- **문제**: `Warning: unknown field "spec.storage.v1"` 발생 및 Prometheus 파드 생성 안 됨.
- **해결**: `storageSpec` 구조에서 `v1` 태그를 제거하고 `volumeClaimTemplate` 형식을 준수하여 PVC 바인딩 성공.

## 4. 최종 상태 확인
- **Prometheus Targets**: 마스터 노드 컴포넌트(10257, 10259, 2381) 및 워커 노드 proxy(10249) 포함 전체 타겟 정상 수집.
- **Grafana Data Sources**: 
  - `Prometheus` (Default, 내부 K8s) - 정상 작동.
  - `Prometheus-Host-VM` (외부 16번 VM) - ConfigMap 주입 방식으로 연동 성공.
- **Explore 검증**: `up` 쿼리 및 `node_hwmon_temp_celsius` 쿼리를 통해 물리 서버와 K8s 자원 데이터가 모두 조회됨을 확인.

## 5. 향후 계획
- **Issue #3-13**: 수집된 온도를 기반으로 Proxmox 물리 호스트 부하 대시보드 구축 및 온도 임계치 도달 시 알림 설정.