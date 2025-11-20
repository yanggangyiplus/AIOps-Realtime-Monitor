# AIOps Real-time Monitor

실시간 스트리밍 데이터 기반 이상 탐지 및 모니터링 시스템

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 프로젝트 미리보기

*Streamlit 대시보드 화면 - 실시간 메트릭 모니터링 및 이상 탐지*

## 핵심 성과 요약

| 항목 | 성과 |
|:---:|:---:|
| **처리 속도** | 초당 수백 건의 데이터 실시간 처리 |
| **탐지 방법** | ML 기반 이상 탐지 (Isolation Forest, Z-score) |
| **지원 소스** | HTTP API, WebSocket, Socket, Mock Stream |
| **대시보드** | Streamlit 기반 실시간 모니터링 UI |
| **구현 범위** | 수집부터 시각화까지 End-to-End 구현 |

## 문제 정의 & 해결 목적

서비스 운영 중 발생하는 장애는 대부분 사전 신호가 있습니다. 응답 시간 증가, 5xx 에러 증가, 특정 IP의 급증 등이 그 예입니다. 하지만 이러한 신호를 실시간으로 감지하고 대응하는 것은 쉽지 않습니다.

기존 모니터링 도구들은 주로 threshold 기반으로 동작하며, ML 기반 패턴 탐지가 약합니다. 또한 로그 기반 분석은 반응 속도가 느려서 장애가 발생한 후에야 알 수 있는 경우가 많습니다.

이 프로젝트는 실시간 스트림 데이터를 ML 기반으로 분석하여 이상을 조기 감지하는 시스템입니다. HTTP API를 실시간으로 모니터링하고, 이상 징후를 즉시 탐지하여 장애 발생 전에 대응할 수 있도록 합니다.

## 프로젝트 개요

### 목적
실시간 스트림 데이터를 ML 기반으로 분석하여 이상을 조기 감지하는 시스템을 구축합니다. 초당 수백 건의 데이터를 실시간으로 처리하여 HTTP 오류, 성능 이상, 리소스 이상을 즉시 탐지합니다.

### 주요 특징
- 실시간 이상 탐지: 초당 수백 건의 데이터를 실시간으로 처리
- ML 기반 패턴 분석: 단순 threshold가 아닌 Isolation Forest, Z-score 등 ML/통계 방법 활용
- 운영 관점의 문제 해결: 장애 예방, 즉시 알림, 성능 모니터링, 리소스 관리
- 확장 가능한 아키텍처: 모듈화된 구조로 새로운 탐지 방법이나 수집 방식을 쉽게 추가 가능

## 시스템 아키텍처

### 전체 시스템 구조

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
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│         Comprehensive Anomaly Detection                     │
│  • HTTP Error Detection (5xx, 4xx)                         │
│  • Performance Anomalies (Response Time, RPS)                │
│  • Resource Anomalies (CPU, Memory)                        │
│  • Security Patterns (IP-based attacks)                     │
│  • Isolation Forest (ML)                                    │
│  • Z-score Detection                                        │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              Alert System                                   │
│  • Multi-level Alerts (Critical/Warning/Info)              │
│  • Deduplication                                            │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│         Real-time Dashboard (Streamlit)                      │
│  • Live Charts (Response Time, CPU Usage)                   │
│  • Real-time Metrics (RPS, Error Rate, Status)             │
│  • Anomaly Alerts Panel                                     │
│  • Data Export (CSV/JSON)                                   │
└─────────────────────────────────────────────────────────────┘
```

## 모델/기술 스택

| 영역 | 기술 | 선택 이유 |
|------|------|----------|
| **실시간 수집** | Socket, WebSocket, requests | 다양한 소스에서 실시간 데이터 수집 지원 |
| **전처리** | Pandas, NumPy | 데이터 처리 및 변환에 표준 라이브러리 사용 |
| **특징 엔지니어링** | NumPy, Rolling Window | 시계열 데이터의 통계적 특징 추출 |
| **이상 탐지** | scikit-learn (Isolation Forest), scipy | Isolation Forest는 빠르고 효과적인 이상 탐지 알고리즘, Z-score는 통계적 이상치 탐지에 적합 |
| **대시보드** | Streamlit, Plotly | Streamlit은 빠른 프로토타이핑에 적합, Plotly는 인터랙티브 시각화 제공 |
| **시스템 모니터링** | psutil | 시스템 리소스 모니터링에 표준 라이브러리 사용 |
| **설정 관리** | PyYAML | 설정 파일 관리를 위한 표준 포맷 |
| **로깅** | loguru | 구조화된 로깅 및 디버깅 지원 |

## 실험 결과

### 탐지 가능한 이상 유형

| 이상 유형 | 탐지 방법 | 정확도 |
|----------|----------|--------|
| **HTTP/웹 서버 오류** | 5xx/4xx 상태 코드 즉시 감지 | 100% (규칙 기반) |
| **성능 이상** | 응답 시간 급증, RPS 급증/급감 | Isolation Forest 기반 |
| **리소스 이상** | CPU spike, Memory leak | Z-score 기반 |
| **보안 공격 패턴** | 동일 IP 반복 호출 | 규칙 기반 + 통계적 분석 |

### 핵심 성능 지표

- **실시간 처리**: 초당 수백 건의 데이터 처리 가능
- **탐지 지연**: 이상 발생 후 수초 내 탐지
- **대시보드 업데이트**: 1초 간격 실시간 업데이트

## 핵심 기술 설명

### Isolation Forest 선택 이유

Isolation Forest는 규칙 기반 없이도 비정상 포인트를 빠르게 분리합니다. 실시간 예측에 매우 적합하며 속도가 빠릅니다. 정상 패턴 학습에 매우 강하며, 장애 발생 전 패턴의 "미세한 변화"를 에러로 잘 포착합니다.

### Z-score Detection 선택 이유

Z-score는 분포 기반 이상치 탐지를 위한 통계적 방법입니다. 급격한 변화 감지에 적합하며, 처리 속도가 빠릅니다. 실시간 모니터링에 적합한 알고리즘입니다.

### 아키텍처 설계 원칙

- **모듈화**: 각 컴포넌트가 독립적으로 동작하도록 설계
- **확장성**: 새로운 탐지 방법이나 수집 방식을 쉽게 추가 가능
- **실시간 처리**: 스트림 데이터를 지연 없이 처리

## 실행 방법

### Quick Start

```bash
# 저장소 클론
git clone <repository-url>
cd AIOps-Realtime-Monitor

# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 대시보드 실행
streamlit run app/web/dashboard.py
```

브라우저에서 `http://localhost:8501`로 접속하여 대시보드를 확인할 수 있습니다.

### 상세 설치 가이드

1. **환경 설정**
```bash
# 저장소 클론
git clone <repository-url>
cd AIOps-Realtime-Monitor

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

2. **설정 파일 구성**
   - `configs/config_stream.yaml`: 스트림 수집 설정
   - `configs/config_anomaly.yaml`: 이상 탐지 설정
   - `configs/config_dashboard.yaml`: 대시보드 설정

3. **대시보드 실행**
```bash
# 방법 1: 스크립트 사용
./scripts/run_dashboard.sh

# 방법 2: 직접 실행
streamlit run app/web/dashboard.py
```

## 사용 시나리오 (Use Cases)

### 1. 웹 서비스 실시간 모니터링
**시나리오**: 운영 중인 웹 서비스의 HTTP API를 실시간으로 모니터링  
**해결책**: HTTP Poller로 주기적으로 API 호출, 응답 시간 및 상태 코드 모니터링  
**효과**: 장애 발생 전 징후를 조기 감지하여 사전 대응 가능

### 2. 마이크로서비스 성능 모니터링
**시나리오**: 여러 마이크로서비스의 성능을 통합 모니터링  
**해결책**: 각 서비스의 메트릭을 수집하여 통합 대시보드에서 모니터링  
**효과**: 서비스 간 의존성 문제를 조기 발견

### 3. 보안 공격 탐지
**시나리오**: DDoS 공격이나 비정상적인 트래픽 패턴 탐지  
**해결책**: IP 기반 통계 분석 및 이상 패턴 탐지  
**효과**: 보안 위협을 사전에 차단

### 4. 리소스 관리
**시나리오**: 서버의 CPU, Memory 사용량 모니터링  
**해결책**: 시스템 리소스를 실시간으로 모니터링하여 이상 징후 탐지  
**효과**: 리소스 부족으로 인한 장애를 사전 예방

## 한계 & 개선 방향

### 현재 한계

- **로그 분석 통합**: 현재는 실시간 스트림만 지원, 로그 파일 분석은 미지원
- **DB/Redis 모니터링**: 데이터베이스 및 캐시 모니터링 기능 미지원
- **Cloud Infra 이벤트**: AWS CloudWatch 등 클라우드 인프라 이벤트 연동 미지원
- **Kubernetes 이벤트**: 쿠버네티스 환경 모니터링 미지원
- **알림 연동**: Slack, Email 등 외부 알림 시스템 연동 미지원

### 개선 방향

- **로그 분석 통합**: 로그 파일을 실시간으로 분석하는 기능 추가
- **DB/Redis 모니터링**: 데이터베이스 및 캐시 메트릭 수집 기능 추가
- **Cloud Infra 연동**: AWS CloudWatch, Azure Monitor 등 클라우드 모니터링 서비스 연동
- **Kubernetes 지원**: 쿠버네티스 환경에서의 메트릭 수집 및 모니터링 지원
- **알림 시스템**: Slack, Email, PagerDuty 등 외부 알림 시스템 연동
- **분산 처리**: 대규모 데이터 처리를 위한 분산 아키텍처 설계

## 개인 기여도

이 프로젝트는 **개인 프로젝트**로, 모든 작업을 직접 수행했습니다.

### 시스템 설계
- 전체 아키텍처 설계: 수집부터 시각화까지 End-to-End 파이프라인 설계
- 모듈화된 구조: 각 컴포넌트가 독립적으로 동작하도록 설계
- 확장 가능한 구조: 새로운 탐지 방법이나 수집 방식을 쉽게 추가 가능하도록 설계

### 데이터 수집 구현
- HTTP Poller: 실제 웹사이트/API 모니터링 기능 구현
- WebSocket Collector: WebSocket 스트림 수집 기능 구현
- Socket Collector: Socket 기반 스트림 수집 기능 구현
- Mock Stream Generator: 테스트용 데이터 생성 기능 구현

### 이상 탐지 구현
- Isolation Forest: ML 기반 이상 탐지 알고리즘 구현
- Z-score Detection: 통계적 이상치 탐지 알고리즘 구현
- HTTP Error Detection: 5xx/4xx 상태 코드 즉시 감지 기능 구현
- Performance Anomaly Detection: 응답 시간, RPS 이상 탐지 기능 구현
- Resource Anomaly Detection: CPU, Memory 이상 탐지 기능 구현
- Security Pattern Detection: IP 기반 공격 패턴 탐지 기능 구현

### 대시보드 개발
- Streamlit UI: 실시간 모니터링 대시보드 구현
- Live Charts: 응답 시간, CPU 사용량 등 실시간 차트 구현
- Metrics Display: RPS, Error Rate, Status 등 메트릭 표시 기능 구현
- Alert Panel: 이상 탐지 결과 표시 패널 구현
- Data Export: CSV/JSON 데이터 내보내기 기능 구현

### 전처리 및 특징 엔지니어링
- Preprocessing Pipeline: Noise 제거, Smoothing, Outlier Clipping 구현
- Windowing: Rolling Window 관리 및 Time-window 집계 구현
- Feature Engineering: RPS, Error Rate, Response Time Statistics 등 특징 추출 구현

### 문서화
- README: 프로젝트 설명 및 사용 가이드 작성
- 코드 주석: 주요 함수 및 클래스에 한국어 주석 추가
- 설정 가이드: 설정 파일 구성 방법 문서화

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

## 라이선스 & 작성자

이 프로젝트는 MIT 라이선스를 따릅니다.

**작성자**: yanggangyi

- GitHub: [@yanggangyiplus](https://github.com/yanggangyiplus)

## 참고 문서

- [ANOMALY_DETECTION.md](ANOMALY_DETECTION.md) - 이상 탐지 기능 상세 명세
