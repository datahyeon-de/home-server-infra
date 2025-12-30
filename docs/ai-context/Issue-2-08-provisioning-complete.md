# Issue #2-08: 인프라 프로비저닝 완료 및 인벤토리 현행화 검증

## 1. 이슈 개요
- **목표**: 하이브리드(API + CLI) 프로비저닝 플레이북을 통해 전체 VM 배포를 완료하고, 수동 생성된 자원을 인벤토리와 동기화함.
- **결과**: `playbooks/01-provision-vms/01-main.yml` 실행을 통해 모든 VM의 `existing: true` 상태 확보.

## 2. 주요 성과 (Accomplishments)
- **전체 배포 완료**: 
  - Ubuntu 서비스 노드(104-106): MinIO, Postgres, Prometheus용 VM 준비 완료.
- **하이브리드 로직 검증**: 
  - `qm` CLI를 통한 Cloud-init(SSH Key, IP) 주입의 안정성 확보.
  - API 기반의 비동기 `move_disk`를 통해 성능 최적화 달성.
- **상태 동기화(State Sync)**: 수동 생성된 VM을 API로 감지하여 `vm_list.yml`에 자동으로 반영하는 로직 성공.
- **확장성 확보**: 향후 데이터 유입량 증가 시 Proxmox API를 통해 즉시 Worker 노드를 증설할 수 있는 워크플로우 확립.

## 3. 현재 인프라 상태 (Current State)
- **Storage**: 모든 VM 디스크가 NFS(Linked Clone)에서 각 노드의 Local LVM으로 이동 완료 혹은 이동 중.
- **Network**: 모든 노드에 정적 IP 할당 및 Cloud-init 적용 완료.
- **Inventory**: `vars/vm_list.yml` 내 모든 항목이 `existing: true`로 업데이트됨.

## 4. 다음 단계 (Next Steps)
1. **Kubernetes 클러스터 구성**:
   - Master 노드(300)에서 `kubeadm init` 수행 및 CNI(Calico/Cilium) 설치.
   - Worker 노드(301-305) 클러스터 조인(Join).
2. **Kafka 클러스터 상태 점검**:
   - 이미 구축된 3-Node Kafka 클러스터(101-103)의 헬스체크 및 토픽 생성 테스트.
3. **공통 서비스 배포**:
   - MinIO(Object Storage) 및 PostgreSQL(Data Warehouse) 설정 자동화.
4. **모니터링 스택 활성화**:
   - Prometheus & Grafana를 통한 6대 Mini-PC 자원 모니터링 시작.
