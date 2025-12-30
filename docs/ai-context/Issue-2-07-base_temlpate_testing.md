# Issue #2-07: 운영 인프라 배포를 위한 하이브리드 워크플로우 확정

## 1. 이슈 요약
- Proxmox API의 SSH Key 인코딩 정책(HTTP 400) 및 Ubuntu 템플릿의 Cloud-init 드라이브 누락 문제 해결.

## 2. 기술적 해결책 (Hybrid Approach)
- **Life-cycle (API)**: Clone, Migrate, Move Disk, Power On 등 리소스 상태 관리는 속도가 빠른 API 사용.
- **Configuration (CLI)**: 특수문자가 포함된 SSH 키 주입 및 하드웨어 설정(ide2 추가)은 안정성이 높은 `qm` CLI 사용.
- **Optimization**: `move_disk` 작업을 비동기로 던지고 모든 VM 생성이 끝난 후 한꺼번에 Polling하여 전체 소요 시간 단축.

## 3. 검증 결과
- 901(Ubuntu), 902(K8s) 템플릿 모두에서 Cloud-init 설정이 정상적으로 반영됨을 유닛 테스트로 확인 완료.
- 비동기 디스크 이동 중에도 템플릿 원복 및 VM 부팅이 가능함을 확인.

## 4. 트러블슈팅: YAML Syntax Error (Exclude Manual Sync)
- **현상**: 플레이북 실행 시 `mapping values are not allowed in this context` 에러 발생.
- **원인**: `name` 필드 내 콜론(`:`) 사용 시 문자열을 따옴표로 감싸지 않아 YAML 파서가 키-값 쌍으로 오인함.
- **해결**: 모든 `name` 필드에 더블 쿼테이션(`" "`)을 적용하여 문법 오류 해결 및 가독성 확보.
