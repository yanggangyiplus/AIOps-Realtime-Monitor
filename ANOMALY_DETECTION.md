# 이상 탐지 기능 명세서

## 탐지 가능한 이상 유형

### 1. HTTP/웹 서버 오류

#### 5xx 서버 오류 (Critical)
- 500 Internal Server Error
- 501 Not Implemented
- 502 Bad Gateway
- 503 Service Unavailable
- 504 Gateway Timeout
- 505 HTTP Version Not Supported

**탐지 방법**: HTTP 상태 코드 즉시 감지, Anomaly Score: 1.0

#### 4xx 클라이언트 오류 (Warning)
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found
- 408 Request Timeout
- 429 Too Many Requests (Rate Limit)

**탐지 방법**: HTTP 상태 코드 즉시 감지, Anomaly Score: 0.5-0.7

---

### 2. 성능·트래픽 기반 이상

#### 응답 속도(Response Time) 이상
- **평균 응답시간 급증**
  - 탐지: 최근 평균이 과거 평균의 2배 이상
  - Anomaly Score: 증가 비율 기반
  
- **P95, P99 지연 급증**
  - 탐지: P99가 평균의 3배 이상
  - Anomaly Score: 0.9 (Critical)

- **특정 API만 지연 발생**
  - 탐지: 엔드포인트별 통계 추적

#### 트래픽 이상
- **RPS 증가 (트래픽 폭주)**
  - 탐지: 최근 RPS가 과거 평균의 2배 이상
  - Anomaly Score: 증가 비율 기반

- **RPS 급감 (서비스 다운 전조)**
  - 탐지: 최근 RPS가 과거 평균의 30% 이하
  - Anomaly Score: 0.8 (Critical)

- **특정 시간대의 비정상 급등/급락**
  - 탐지: 시간 윈도우 기반 변화점 탐지

#### 에러율(Error Rate) 이상
- 5xx 비율 증가
- 4xx 비율 증가
- 특정 endpoint에서만 에러 증가
  - 탐지: 엔드포인트별 에러율 추적

---

### 3. 서버 리소스 기반 이상

#### CPU 관련 이상
- **CPU spike (갑작스러운 급등)**
  - 탐지: 최근 평균이 과거 평균의 1.5배 이상, 70% 초과
  - Anomaly Score: (현재 CPU - 70) / 30

- **100% 고정 사용**
  - 탐지: CPU 사용률 95% 이상
  - Anomaly Score: 1.0 (Critical)

- **system CPU > 50% 유지**
  - 탐지: 지속적인 높은 CPU 사용률

#### 메모리 이상
- **Memory leak (지속 증가)**
  - 탐지: 최근 평균이 과거 평균의 1.2배 이상, 80% 초과
  - Anomaly Score: (현재 메모리 - 80) / 20

- **OOM 임박 경고**
  - 탐지: 메모리 사용률 95% 이상
  - Anomaly Score: 1.0 (Critical)

---

### 4. 네트워크 기반 이상

#### 연결 지연·타임아웃
- Connection timeout
  - 탐지: HTTP 요청 타임아웃 (408 상태 코드)
  
- Read timeout
  - 탐지: 응답 시간이 타임아웃 임계값 초과

---

### 5. 보안·이상 트래픽 감지

#### 공격 패턴
- **동일 IP 반복 호출**
  - 탐지: 동일 IP에서 50회 이상 요청
  - Anomaly Score: 요청 수 / 100

- **짧은 주기의 반복 요청**
  - 탐지: 10초 내 10회 이상 (초당 5회 이상)
  - Anomaly Score: RPS / 10

- **특정 엔드포인트 집중 공격**
  - 탐지: 최근 50개 요청 중 특정 엔드포인트가 30개 이상
  - Anomaly Score: 요청 비율

- **DDoS 공격(트래픽 폭주)**
  - 탐지: RPS 급증과 IP 기반 공격 패턴 조합

---

## 현재 구현 상태 요약

### 완전 구현됨 (즉시 사용 가능)
1. HTTP/웹 오류 (5xx, 4xx)
2. 성능 이상 (응답 시간, RPS, 에러율)
3. 서버 리소스 이상 (CPU, Memory)
4. 보안 공격 패턴 (IP 기반, 반복 요청)

### 향후 추가 가능
5. 네트워크 이상 (일부 구현, 확장 필요)
6. 애플리케이션 레벨 오류 (로그 분석 필요)
7. DB/Redis 관련 오류 (메트릭 수집 필요)
8. Cloud Infra 이벤트 (API 연동 필요)
9. Kubernetes 이벤트 (API 연동 필요)
10. 사용자 경험 기반 오류 (이벤트 추적 필요)

---

## 사용 방법

### 기본 사용
1. 대시보드에서 HTTP 모드 선택
2. 모니터링할 URL 입력
3. 스트림 시작

### 탐지되는 이상
- HTTP 에러 상태 코드는 즉시 탐지 및 알림
- 성능 이상은 최소 3개 샘플 후 탐지 시작
- 리소스 이상은 실시간 모니터링
- 보안 공격 패턴은 IP 기반 추적

---

## 확장 방법

### 로그 분석 통합
Log-AI-Predictor와 통합하여 애플리케이션 레벨 오류 탐지

### DB/Redis 모니터링 추가
메트릭 수집 모듈 추가하여 DB/Redis 이상 탐지

### Cloud/K8s 연동
API 연동을 통한 인프라 레벨 이벤트 탐지
