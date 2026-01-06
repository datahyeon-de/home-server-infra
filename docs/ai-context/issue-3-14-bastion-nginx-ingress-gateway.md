# Issue #3-14: Bastion Nginx 게이트웨이 구축 및 K8s 서비스 외부 노출 (Ingress)

## 📅 날짜: 2026-01-06
## 👤 참여자: [임성현], Gemini

## 1. 이슈 개요
- **목표**: 외부망(Client)에서 Bastion 서버를 거쳐 내부 VM 서비스 및 K8s 파드 서비스에 도메인 기반으로 안전하게 접속.
- **핵심 원칙**: 
  - Bastion에 Nginx 직접 설치 (Docker 미사용).
  - **투명성(Transparency)**: 클라이언트가 K8s에 직접 접속하는 것과 동일한 헤더 정보 유지.

## 2. 세부 작업 및 기술 결정

### 2.1 Bastion Nginx 설치 및 리버스 프록시 구성
- **설치**: `apt install nginx` 및 `systemctl enable` 등록.
- **L7 프록시 설정**:
  - `proxy_set_header Host $host;`: 원본 도메인 헤더 보존.
  - `proxy_set_header X-Forwarded-Proto $scheme;`: SSL/비SSL 정보 유지.
  - **VM 서비스**: Prometheus A(VM 16), MinIO(VM 14)를 각각 `proxy_pass`로 연결.
  - **K8s 서비스**: 모든 트래픽을 K8s Nginx Ingress Controller의 NodePort(30998)로 집중 전달.

### 2.2 K8s Helm 차트 기반 Ingress 활성화
- **Airflow (v1.15.0)**: `values.yaml`의 `ingress.web` 섹션 수정.
  - `enabled: true`, `hosts: [{name: "airflow.local"}]` 적용.
- **Monitoring Stack**: `kube-prometheus-stack` 내 `prometheus.ingress` 섹션 수정.
  - `prometheus-b.local` 도메인 할당 및 `ImplementationSpecific` 경로 타입 설정.

## 3. [핵심 트러블슈팅] 문제와 해결책

### 3.1 Spark UI 503 Service Unavailable 에러
- **문제**: `http://spark-ui.local/long-test-...` 접속 시 503 에러 발생.
- **진단**: `kubectl describe ingress` 결과, Spark UI의 실제 경로는 `/spark-ui/spark/...`로 설정되어 있으나 클라이언트가 Prefix 없이 접속 시도.
- **해결**: 
  - 브라우저 주소창에 풀 경로(`http://spark-ui.local/spark-ui/spark/.../`) 입력 확인.
  - Spark Operator의 `ui.proxyBase` 설정과 Nginx Ingress의 `rewrite-target` 메커니즘 일치 확인.
  - **결과**: 정상 접속 및 UI 표출 성공.

### 3.2 Helm show values 활용 설정 탐색
- **난관**: 복잡한 차트에서 특정 인그레스 설정 위치를 찾기 어려움.
- **해결**: `awk` 및 `sed` 조합 명령어를 통해 특정 컴포넌트의 블록만 정밀 추출.
  - 명령어: `helm show values ... | awk '/^prometheus:/{p=1} /^alertmanager:/{p=0} p' | awk '/ingress:/{...}'`

## 4. 최종 상태 확인
- **접속 가능 도메인 (Bastion -> Internal)**:
  - VM 영역: `prometheus-a.local`, `minio.local`
  - K8s 영역: `airflow.local`, `grafana.local`, `prometheus-b.local`, `spark-history.local`, `spark-ui.local`
- **인프라 정합성**: `/etc/hosts` 파일 기반의 도메인 매핑 완료 및 외부망에서의 단일 진입점(Bastion) 정상 작동 확인.

## 5. 향후 계획
- **Issue #3-15**: Spark 및 Airflow 작업 로그의 외부 S3(MinIO) 원격 저장소 연동 최적화 및 안정성 검증.