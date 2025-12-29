# Issue #2: Proxmox Provisioning 자동화 API 전환 및 스토리지 최적화

## 1. 배경 및 문제 정의
- **CLI 권한 에러**: Ansible `shell` 모듈을 통한 `qm` 명령어 실행 시, 비대화형(Non-interactive) 셸의 PATH 미인식 및 `sudo` 보안 정책(`secure_path`)으로 인해 `rc: 127` 에러 지속 발생.
- **스토리지 병목**: NFS에서 로컬 스토리지로 Full Clone 시 1Gbps 네트워크 대역폭 한계로 인해 VM 1대당 수 분의 대기 시간 발생 및 인프라 전체 부하 증가.

## 2. 해결 과정 (Tiki-Taka 요약)
1. **CLI 트래블슈팅**: 심볼릭 링크 생성, `become` 권한 조정 등을 시도했으나 Proxmox 호스트의 보안 설정과 충돌 확인.
2. **API 전략 선회**: SSH 의존성을 제거하기 위해 Proxmox REST API(`uri` 모듈)를 사용하여 원격 노드 제어 방식으로 전면 개편.
3. **스토리지 전략 수정**: 
   - 초기: NFS ➔ Local (Full Clone) - **느림**
   - 최종: NFS ➔ NFS (Linked Clone) ➔ Local (Move Disk) - **빠름 & 효율적**



## 3. 최종 확정 아키텍처: Linked Clone + Background Move Disk
관리의 편의성(NFS 중앙 관리)과 실행 성능(Local LVM)을 모두 확보하기 위해 다음과 같은 비동기 로직을 확정함.

### 🚀 프로비저닝 워크플로우
1. **Check**: 타겟 노드에 해당 VMID 존재 여부 확인 (API GET).
2. **Migrate**: 1번 노드(Golden Image 상주)에서 타겟 노드로 템플릿 마이그레이션.
3. **Linked Clone**: NFS 스토리지 내에서 즉시 링크드 클론 생성 (1초 소요).
4. **Move Disk (핵심)**: NFS 링크를 로컬 LVM으로 비동기 이동 명령 후 작업 ID(UPID) 기록.
5. **Template Return**: 다음 작업을 위해 템플릿을 즉시 1번 노드로 복귀.
6. **Config & Boot**: Cloud-init 설정(IP, SSH Key) 주입 및 VM 부팅 (디스크 이동 중에도 부팅 가능).
7. **Final Polling**: 모든 VM 루프 종료 후, 기록된 모든 UPID의 성공 여부를 최종 확인.
8. **Inventory Sync**: 성공한 VM에 대해 `vm_list.yml`의 `existing` 필드를 `true`로 업데이트.



## 4. 기술적 결정 사항 (Decision Records)
- **API Token 사용**: 유저 패스워드 대신 API Token(PVEAPIToken)을 사용하여 보안 강화.
- **Idempotency(멱등성)**: VM 존재 여부 확인 단계를 추가하여 중복 생성 방지.
- **Background Processing**: `move_disk`를 비동기로 처리하여 Ansible이 대기하지 않고 다음 VM 생성을 이어가도록 최적화.

## 5. 결론 및 향후 과제
- 본 이슈를 통해 SSH/Sudo 이슈를 원천 차단하고, 네트워크 대역폭을 효율적으로 사용하는 인프라 자동화 기틀을 마련함.
- 향후 노드 확장 시에도 NFS 중앙 템플릿만 유지하면 즉시 대응 가능.
- **다음 단계**: 생성된 Playbook 테스트 진행.