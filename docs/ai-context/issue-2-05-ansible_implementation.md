# Issue #2-05: Ansible 플레이북 구현 (Global Vars & Provisioning)

## 📅 날짜: 2025-12-29
## 👤 참여자: 임성현, Gemini

## 💬 대화 요약
1. **전역 변수 통합**: Proxmox API, 네트워크, 스토리지 설정을 `group_vars/all.yml`로 단일화하여 유지보수성 확보.
2. **프로비저닝 로직 구체화**: 
   - 템플릿 이동(Migration) -> 클론(Clone) -> 완료 대기(Polling) -> 템플릿 복귀(Return) 프로세스 설계.
   - API Task UPID를 추적하여 안정적인 순차 작업 보장.
3. **Cloud-init 설정**: 901(Ubuntu) 템플릿에 대해 Bastion의 SSH Key 주입 및 정적 IP 설정을 자동화함.

## 🛠️ 결정된 사항
- `community.general.proxmox` 모듈을 주력으로 사용하되, 템플릿 이동 등 API 미지원 기능은 `shell` 모듈(qm command)로 보완한다.
- 모든 신규 VM은 `existing: false` 상태인 것만 선별하여 작업을 수행한다.