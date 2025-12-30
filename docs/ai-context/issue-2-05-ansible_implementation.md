# Issue #2-05: Ansible 플레이북 구현 (구조 최적화, 전역 변수 및 프로비저닝 로직 통합)

## 📅 날짜: 2025-12-29
## 👤 참여자: 임성현, Gemini

## 💬 대화 요약
1. **디렉토리 구조 최적화**: 파일 산재를 방지하고 관리 효율을 높이기 위해 `playbooks/[순번]-[작업명]/` 하위 구조와 파일명 숫자 접두어 규칙을 도입함.
2. **전역 변수 통합 및 보안**: Proxmox API, 네트워크, 스토리지 설정을 `group_vars/all.yml`로 단일화하여 유지보수성을 확보하고, 민감 정보(Secret) 관리에 대한 보안 가이드를 수립함.
3. **실제 인증 정보 반영**: 사용자로부터 수령한 실제 Proxmox API 토큰 ID(`datahyeon@pam!ansible_group_token`)와 시크릿을 시스템에 적용함.
4. **프로비저닝 로직 구체화**: 
   - **순차 프로세스**: 템플릿 이동(Migration) -> 클론(Clone) -> 완료 대기(Polling) -> 템플릿 복귀(Return) -> Cloud-init 설정의 5단계 공정 확립.
   - **상태 추적**: API Task UPID를 추적하여 클론 작업이 완전히 종료된 후 다음 단계가 진행되도록 보장함.
5. **Cloud-init 자동화**: 901(Ubuntu) 템플릿에 대해 Bastion의 SSH Key 주입 및 정적 IP 설정을 자동화하여 초기 접속 환경을 구축함.

## 🛠️ 결정된 사항
- **구조적 규칙**:
  - 모든 플레이북은 `playbooks/` 디렉토리 내 폴더별로 관리하며, 실행 순서 파악이 쉽도록 접두어 숫자를 사용한다.
  - 메인 실행 파일은 `01-main.yml`, 세부 태스크는 `tasks/` 폴더 내 `01-process-single-vm.yml` 형식을 따른다.
- **기술적 세부사항**:
  - `community.general.proxmox` 모듈을 주력으로 사용하되, 템플릿 이동(migrate) 등 API 미지원 기능은 `shell` 모듈(`qm` 명령어)로 보완하는 하이브리드 방식을 채택한다.
  - 멱등성 유지를 위해 `vars/vm_list.yml`에서 `existing: false` 상태인 VM만 선별하여 작업을 수행한다.
  - API 인증 시 `api_user` 형식을 `datahyeon@pam!ansible_group_token` 규격으로 고정하여 모든 모듈에서 공통 사용한다.

---

## 📂 최종 디렉토리 구조 (예시)

```text
home-server-infra/
├── docs/..
├── group_vars/
│   └── all.yml
├── vars/
│   └── vm_list.yml
└── playbooks/
    └── 01-provision-vms/
        ├── 01-main.yml
        └── tasks/
            └── 01-process-single-vm.yml
```

---
## 🚀 다음 단계

Playbook 폴더 생성: mkdir -p playbooks/01-provision-vms/tasks

파일 작성: 통합된 로직에 따라 01-main.yml과 01-process-single-vm.yml에 코드를 배치합니다.

K8s 클러스터링 준비: VM 생성이 완료된 후 진행할 playbooks/02-setup-k8s/ 설계를 이어가겠습니다.

---

### 💡 다음 작업 안내

1.  **`playbooks/02-setup-k8s/`**