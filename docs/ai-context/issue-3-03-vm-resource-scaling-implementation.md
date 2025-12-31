# Issue #3-03: 고가용성 데이터 플랫폼을 위한 자원 조정 플레이북 구현

## 📅 날짜: 2025-12-31
## 👤 참여자: 임성현, Gemini

## 1. 이슈 개요
- **목표**: 인프라 위에 올라갈 Kafka, Spark, K8s 노드들의 사양을 플랫폼 설계안(Issue #3-01)에 맞춰 자동 조정하고, 안정적인 서비스 전환을 위한 셧다운/부팅 로직을 구현함.
- **결과**: `02-modify-vm-resources` 플레이북 완성 및 유닛 테스트(`kvm-test`)를 통한 안정성 검증 완료.

## 2. 주요 성과 및 대화 요약
- **[공식 모듈 도입]**: 기존 `uri` 모듈의 SSH 키 URL 인코딩 문제를 해결하기 위해 `community.proxmox.proxmox_kvm` 공식 모듈을 도입하여 인코딩 지옥을 해결함.
- **[안전한 라이프사이클 구현]**: 자원 수정 시 발생할 수 있는 데이터 오염을 방지하기 위해 `Shutdown -> Wait(until) -> Update -> Start` 로직을 체인 형태로 구성함.
- **[대화 요약]**: 
    - 1) `qm` CLI와 API 중 자원 수정에 더 유리한 방식 논의 (API + 공식 모듈 승리)
    - 2) Cloud-init 드라이브 부재 시 자원 수정 오류 해결 방안 도출 (URI로 드라이브 선 생성 후 모듈로 데이터 주입)
    - 3) 비동기 셧다운 대기를 위한 `until` 문 활용 방안 합의

## 3. 기술적 의사결정 및 트러블슈팅
- **기술적 선택: Hybrid Provisioning**:
    - 하드웨어 생성(Clone, Cloud-init Drive 추가)은 응답이 명확한 **API(URI 모듈)**를 사용.
    - 복잡한 데이터 주입(SSH Keys, Network Config, CPU/Mem Throttling)은 **Ansible 전용 모듈**을 사용하여 가독성과 안정성 확보.
- **트러블슈팅: 셧다운 타임아웃 해결**:
    - `community.proxmox.proxmox_kvm`의 `timeout` 파라미터가 간혹 무시되는 문제를 해결하기 위해, API `/status/shutdown` 호출 후 `/status/current`를 `until` 문으로 폴링하여 `stopped` 상태를 확정적으로 확인하는 로직 적용.

## 4. 결론 및 향후 계획
- **결론**: 플랫폼 운영에 필요한 핵심 자원 가변성(Scalability) 확보 완료. 모든 VM이 설계된 CPU/Memory 사양으로 정상 구동됨을 확인함.
- **차기 과제**: 
    - **Spark Operator 설치 준비**: K8s 노드별 역할(Master/Worker)에 따른 **Node Labeling/Tagging** 작업 진행.
    - K8s 클러스터 내 Spark 구동을 위한 최적의 스케줄링 환경 조성.