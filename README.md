# AIOps Real-time Monitor

실시간 스트리밍 데이터 기반 이상 탐지 및 모니터링 시스템

> **실시간 HTTP API 모니터링 → 전처리 → 특징 추출 → ML 기반 이상 탐지 → 알림 → 대시보드 시각화까지 End-to-End로 수행하는 운영 모니터링 플랫폼**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 목차

- [TL;DR](#tldr)
- [프로젝트 개요](#프로젝트-개요)
- [시스템 아키텍처](#시스템-아키텍처)
- [핵심 기능](#핵심-기능)
- [기술 스택](#기술-스택)
- [역량](#역량)
- [설치 및 실행](#설치-및-실행)
- [프로젝트 구조](#프로젝트-구조)
- [설정](#설정)
- [사용 방법](#사용-방법)

---

## TL;DR

**핵심 요약**:
- **실시간 데이터 수집**: HTTP API 폴링, WebSocket, Socket 기반 스트림 수집
- **이상 탐지**: Isolation Forest, Z-score 기반 ML 이상 탐지 및 HTTP 오류 즉시 감지
- **성능 모니터링**: 응답 시간, RPS, 에러율 실시간 추적
- **리소스 모니터링**: CPU, Memory 사용률 모니터링
- **보안 탐지**: IP 기반 공격 패턴 탐지
- **실시간 대시보드**: Streamlit 기반 모니터링 및 시각화
- **데이터 내보내기**: CSV/JSON 형식으로 데이터 다운로드

---

## 프로젝트 개요

### 목적

서비스 운영 중 발생하는 실시간 신호를 수집하여 이상 징후, 급격한 변화점, 장애 가능성 패턴을 즉시 탐지하는 시스템입니다.

### 이 프로젝트가 해결하는 문제

현업에서는 아래 이유로 실시간 이상 감지가 어렵습니다:

- 데이터가 초당 수백~수천 건씩 들어옴
- 로그 기반 탐지는 반응 속도가 늦음
- 기존 모니터링 도구는 threshold 기반이며 ML 기반 패턴 탐지가 약함
- 장애 전조는 "미세 변화 → 급격한 폭발" 형태로 사람이 실시간 패턴을 보기 어려움

이 프로젝트는 실시간 스트림 데이터를 ML 기반으로 분석하여 이상을 조기 감지합니다.

### 주요 특징

- **실시간 처리**: 초당 수십~수백 건의 스트림 데이터 실시간 처리
- **다중 탐지 방법**: 통계적 방법과 ML 방법을 조합한 하이브리드 탐지
- **즉시 HTTP 오류 감지**: 5xx, 4xx 상태 코드 즉시 탐지 및 알림
- **성능 이상 탐지**: 응답 시간 급증, RPS 급증/급감, 에러율 증가 자동 탐지
- **리소스 이상 탐지**: CPU spike, Memory leak 등 시스템 리소스 이상 탐지
- **보안 패턴 탐지**: 동일 IP 반복 호출, 짧은 주기 반복 요청 등 공격 패턴 탐지

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Real-time Stream                         │
│  (HTTP API / WebSocket / Socket / Mock)                     │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              Stream Collector (Ingest)                      │
│  • HTTP Poller (실제 웹사이트/API 모니터링)                   │
│  • WebSocket Collector                                       │
│  • Socket Collector                                          │
│  • Mock Stream Generator (테스트용)                          │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              Preprocessing & Windowing                       │
│  • Noise 제거, Smoothing, Outlier Clipping                  │
│  • Rolling Window 관리                                       │
│  • Time-window 집계                                          │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              Feature Engineering                            │
│  • RPS (Requests Per Second)                                │
│  • Error Rate                                               │
│  • Response Time Statistics                                 │
│  • Rolling Features (Mean, Std, EMA)                        │
│  • Spike Score                                              │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│         Comprehensive Anomaly Detection                     │
│  • HTTP Error Detection (5xx, 4xx)                         │
│  • Performance Anomalies (Response Time, RPS)              │
│  • Resource Anomalies (CPU, Memory)                        │
│  • Security Patterns (IP-based attacks)                    │
│  • Isolation Forest (ML)                                    │
│  • Z-score Detection                                        │
│  • Change-point Detection                                   │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              Alert System                                   │
│  • Multi-level Alerts (Critical/Warning/Info)              │
│  • Deduplication                                            │
│  • Alert History Management                                 │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│         Real-time Dashboard (Streamlit)                      │
│  • Live Charts (Response Time, CPU Usage)                  │
│  • Real-time Metrics (RPS, Error Rate, Status)              │
│  • Anomaly Alerts Panel                                     │
│  • Data Export (CSV/JSON)                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 핵심 기능

### 1. Real-time Data Ingestion
- HTTP API 폴링: 실제 웹사이트나 API를 주기적으로 호출하여 모니터링
- WebSocket/Socket: 실시간 스트림 데이터 수집
- Mock Stream: 테스트용 데이터 생성

### 2. Streaming Preprocessing
- Noise 제거
- Rolling window smoothing
- Outlier clipping
- Time-window 집계

### 3. Feature Engineering
- RPS (Requests Per Second)
- Error Rate
- Spike score
- Moving average
- EMA (Exponential Moving Average)
- Rolling std / var

### 4. Real-time Anomaly Detection
- **HTTP 오류 탐지**: 5xx, 4xx 상태 코드 즉시 감지
- **성능 이상 탐지**: 응답 시간 급증, RPS 급증/급감, 에러율 증가
- **리소스 이상 탐지**: CPU spike, Memory leak, OOM 경고
- **보안 공격 탐지**: 동일 IP 반복 호출, 짧은 주기 반복 요청
- **ML 기반 탐지**: Isolation Forest, Z-score, Change-point Detection

### 5. Alert System
- 조건 기반 경고
- ML 기반 score 경고
- Multi-level 알림 (Critical/Warning/Info)
- 중복 제거 및 히스토리 관리

### 6. Live Monitoring Dashboard
- Streamlit 실시간 차트
- Anomaly highlight
- Rolling trend plot
- Last events feed
- 데이터 내보내기 (CSV/JSON)

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| 실시간 수집 | Socket, WebSocket, requests |
| 전처리 | Pandas, NumPy |
| 특징 엔지니어링 | NumPy, Rolling Window |
| 이상 탐지 | scikit-learn (Isolation Forest), scipy |
| 대시보드 | Streamlit, Plotly |
| 시스템 모니터링 | psutil |
| 설정 관리 | PyYAML |
| 로깅 | loguru |

---

## 역량

이 프로젝트를 통해 다음 역량을 보여줍니다:

- **실시간 스트림 처리**: 초당 수백 건의 데이터를 실시간으로 처리하는 파이프라인 설계 및 구현
- **ML 기반 이상 탐지**: Isolation Forest, Z-score 등 다양한 ML/통계 방법을 활용한 이상 탐지 시스템 구축
- **End-to-End 시스템 설계**: 데이터 수집부터 시각화까지 전체 파이프라인 설계 및 구현
- **실시간 모니터링 대시보드**: Streamlit을 활용한 실시간 모니터링 대시보드 개발
- **확장 가능한 아키텍처**: 새로운 탐지 방법이나 수집 방식을 쉽게 추가할 수 있는 모듈화된 구조 설계
- **프로덕션 수준 코드**: 예외 처리, 로깅, 설정 관리 등 프로덕션 환경을 고려한 코드 작성

---

## 설치 및 실행

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd AIOps-Realtime-Monitor

# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 대시보드 실행

```bash
# 방법 1: 스크립트 사용
./scripts/run_dashboard.sh

# 방법 2: 직접 실행
streamlit run app/dashboard.py
```

브라우저에서 `http://localhost:8501`로 접속하여 대시보드를 확인할 수 있습니다.

---

## 프로젝트 구조

```
AIOps-Realtime-Monitor/
├── app/
│   ├── dashboard.py            # Streamlit 대시보드 (메인)
│   ├── state_manager.py        # 세션 상태 관리
│   ├── controls_sidebar.py     # 사이드바 UI
│   ├── render_charts.py        # 차트 렌더링
│   ├── render_metrics.py       # 메트릭 렌더링
│   └── render_alerts.py        # 알림 렌더링
│
├── src/
│   ├── ingest/                 # 스트림 수집
│   │   ├── socket_stream.py
│   │   ├── websocket_stream.py
│   │   ├── mock_stream.py
│   │   ├── http_poller.py
│   │   └── ingest_manager.py
│   │
│   ├── processing/             # 전처리 & 윈도우링
│   │   ├── preprocess.py
│   │   └── window_manager.py
│   │
│   ├── feature/                # 특징 추출
│   │   └── feature_engineering.py
│   │
│   ├── anomaly/                # 이상 탐지
│   │   ├── zscore_detector.py
│   │   ├── iforest_detector.py
│   │   ├── changepoint.py
│   │   ├── comprehensive_detector.py
│   │   └── detector_manager.py
│   │
│   ├── alert/
│   │   └── alert_manager.py
│   │
│   └── utils/
│       ├── logger.py
│       └── config.py
│
├── configs/
│   ├── config_stream.yaml
│   ├── config_anomaly.yaml
│   └── config_dashboard.yaml
│
├── scripts/
│   └── run_dashboard.sh
│
├── requirements.txt
├── README.md
└── ANOMALY_DETECTION.md
```

---

## 설정

설정 파일은 `configs/` 디렉토리에 있습니다:

### config_stream.yaml
스트림 수집 설정 (모드, 호스트, 포트 등)

```yaml
stream:
  mode: "http"  # mock, socket, websocket, http
  http:
    urls:
      - "https://www.google.com"
    interval: 1.0
    timeout: 5
```

### config_anomaly.yaml
이상 탐지 설정 (방법, 임계값 등)

```yaml
anomaly:
  method: "hybrid"  # isolation_forest, zscore, iqr, hybrid
  isolation_forest:
    contamination: 0.1
    n_estimators: 100
  zscore:
    threshold: 3.0
```

### config_dashboard.yaml
대시보드 설정 (차트, 알림 등)

---

## 사용 방법

### 기본 사용 흐름

1. **대시보드 실행**
   ```bash
   streamlit run app/dashboard.py
   ```

2. **모니터링 설정**
   - 사이드바에서 수집 모드를 선택 (HTTP 권장)
   - 모니터링할 URL 입력 (예: `https://httpbin.org/status/500`)
   - 필요시 추가 URL 입력

3. **스트림 시작**
   - "시작" 버튼 클릭
   - 실시간 데이터 수집 및 이상 탐지 확인

4. **데이터 확인**
   - 실시간 차트에서 Response Time, CPU Usage 확인
   - 메트릭에서 RPS, Error Rate, Status 확인
   - 알림 패널에서 이상 탐지 결과 확인

5. **데이터 내보내기**
   - 사이드바 또는 메인 영역에서 CSV/JSON 다운로드

### 예시: HTTP 에러 모니터링

```python
# configs/config_stream.yaml에서 설정
stream:
  mode: "http"
  http:
    urls:
      - "https://httpbin.org/status/500"
      - "https://httpbin.org/status/503"
      - "https://httpbin.org/status/404"
    interval: 1.0
```

이 설정으로 여러 엔드포인트를 동시에 모니터링하고, HTTP 에러가 발생하면 즉시 알림을 받을 수 있습니다.

---

## 탐지 가능한 이상 유형

### HTTP/웹 서버 오류
- 5xx 서버 오류 (500, 502, 503, 504 등)
- 4xx 클라이언트 오류 (400, 401, 403, 404, 429 등)

### 성능 이상
- 응답 시간 급증 (평균, P95, P99)
- RPS 급증 (트래픽 폭주)
- RPS 급감 (서비스 다운 전조)
- 에러율 급증

### 리소스 이상
- CPU spike, CPU saturation
- Memory leak, OOM 경고

### 보안 공격 패턴
- 동일 IP 반복 호출
- 짧은 주기 반복 요청
- 특정 엔드포인트 집중 공격

---

## 현재 버전 상태

### 완전 구현됨
- HTTP/웹 오류 탐지
- 성능 이상 탐지 (응답 시간, RPS, 에러율)
- 서버 리소스 이상 탐지 (CPU, Memory)
- 보안 공격 패턴 탐지
- 실시간 대시보드 및 시각화
- 데이터 내보내기 기능

### 향후 확장 가능
- 로그 분석 통합 (Log-AI-Predictor와 통합)
- DB/Redis 모니터링
- Cloud Infra 이벤트 (AWS CloudWatch 등)
- Kubernetes 이벤트
- 알림 연동 (Slack, Email)

---

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

---

## 참고 문서

- [ANOMALY_DETECTION.md](ANOMALY_DETECTION.md) - 이상 탐지 기능 상세 명세
