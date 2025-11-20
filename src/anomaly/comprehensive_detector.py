"""
포괄적인 이상 탐지 시스템
모든 유형의 이상을 탐지하는 통합 탐지기입니다.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import numpy as np
from loguru import logger

from .zscore_detector import ZScoreDetector
from .iforest_detector import IsolationForestDetector
from .changepoint import ChangePointDetector


class ComprehensiveAnomalyDetector:
    """
    포괄적인 이상 탐지 시스템
    HTTP 오류, 성능 이상, 리소스 이상, 네트워크 이상, 보안 공격 등을 탐지합니다.
    """
    
    def __init__(self):
        """ComprehensiveAnomalyDetector 초기화"""
        # 기본 탐지기들
        self.zscore_detector = ZScoreDetector(threshold=3.0)
        self.iforest_detector = IsolationForestDetector()
        self.changepoint_detector = ChangePointDetector()
        
        # 히스토리 데이터 저장
        self.response_time_history = deque(maxlen=1000)
        self.status_code_history = deque(maxlen=1000)
        self.rps_history = deque(maxlen=100)
        self.error_rate_history = deque(maxlen=100)
        self.cpu_history = deque(maxlen=500)
        self.memory_history = deque(maxlen=500)
        
        # 통계 정보
        self.endpoint_stats = defaultdict(lambda: {
            "count": 0,
            "error_count": 0,
            "response_times": deque(maxlen=100),
            "last_seen": None
        })
        
        # IP 기반 추적 (보안 탐지용)
        self.ip_requests = defaultdict(lambda: {
            "count": 0,
            "endpoints": set(),
            "user_agents": set(),
            "last_seen": None,
            "requests": deque(maxlen=100)
        })
        
        # 이상 패턴 저장
        self.anomaly_patterns = []
    
    def detect_http_errors(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        HTTP 오류 탐지 (5xx, 4xx)
        
        Args:
            event: 이벤트 딕셔너리
            
        Returns:
            탐지 결과 또는 None
        """
        status_code = event.get("status_code", 200)
        
        if not isinstance(status_code, (int, float)):
            return None
        
        # 5xx 서버 오류 (Critical)
        if status_code >= 500:
            error_type = {
                500: "Internal Server Error",
                501: "Not Implemented",
                502: "Bad Gateway",
                503: "Service Unavailable",
                504: "Gateway Timeout",
                505: "HTTP Version Not Supported"
            }.get(status_code, f"Server Error {status_code}")
            
            return {
                "is_anomaly": True,
                "anomaly_score": 1.0,
                "anomaly_type": "http_server_error",
                "severity": "critical",
                "status_code": status_code,
                "error_message": error_type,
                "endpoint": event.get("endpoint", "unknown"),
                "timestamp": event.get("timestamp", "")
            }
        
        # 4xx 클라이언트 오류 (Warning)
        elif status_code >= 400:
            error_type = {
                400: "Bad Request",
                401: "Unauthorized",
                403: "Forbidden",
                404: "Not Found",
                408: "Request Timeout",
                429: "Too Many Requests"
            }.get(status_code, f"Client Error {status_code}")
            
            return {
                "is_anomaly": True,
                "anomaly_score": 0.7 if status_code == 429 else 0.5,
                "anomaly_type": "http_client_error",
                "severity": "warning",
                "status_code": status_code,
                "error_message": error_type,
                "endpoint": event.get("endpoint", "unknown"),
                "timestamp": event.get("timestamp", "")
            }
        
        return None
    
    def detect_performance_anomalies(
        self,
        event: Dict[str, Any],
        recent_events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        성능 이상 탐지 (응답 시간, RPS, 에러율)
        
        Args:
            event: 현재 이벤트
            recent_events: 최근 이벤트 리스트
            
        Returns:
            탐지 결과 리스트
        """
        anomalies = []
        
        # 응답 시간 이상 탐지
        response_time = event.get("response_time", 0)
        if response_time > 0:
            self.response_time_history.append(response_time)
            
            if len(self.response_time_history) >= 10:
                # 평균 응답 시간 급증
                recent_avg = np.mean(list(self.response_time_history)[-10:])
                historical_avg = np.mean(list(self.response_time_history)[:-10]) if len(self.response_time_history) > 10 else recent_avg
                
                if historical_avg > 0 and recent_avg > historical_avg * 2:
                    anomalies.append({
                        "is_anomaly": True,
                        "anomaly_score": min(1.0, (recent_avg / historical_avg - 1) * 0.5),
                        "anomaly_type": "response_time_spike",
                        "severity": "warning",
                        "current_avg": recent_avg,
                        "historical_avg": historical_avg,
                        "increase_ratio": recent_avg / historical_avg
                    })
                
                # P95, P99 지연 급증
                if len(self.response_time_history) >= 20:
                    p95 = np.percentile(list(self.response_time_history), 95)
                    p99 = np.percentile(list(self.response_time_history), 99)
                    
                    if p99 > historical_avg * 3:
                        anomalies.append({
                            "is_anomaly": True,
                            "anomaly_score": 0.9,
                            "anomaly_type": "p99_latency_spike",
                            "severity": "critical",
                            "p99": p99,
                            "p95": p95,
                            "avg": historical_avg
                        })
        
        # RPS 이상 탐지
        if len(recent_events) >= 10:
            # 시간 윈도우 계산 (최근 10개 이벤트)
            timestamps = [e.get("timestamp", "") for e in recent_events[-10:]]
            if len(timestamps) >= 2:
                try:
                    time_span = (
                        datetime.strptime(timestamps[-1], "%Y-%m-%d %H:%M:%S.%f") -
                        datetime.strptime(timestamps[0], "%Y-%m-%d %H:%M:%S.%f")
                    ).total_seconds()
                    
                    if time_span > 0:
                        current_rps = len(recent_events[-10:]) / time_span
                        self.rps_history.append(current_rps)
                        
                        if len(self.rps_history) >= 5:
                            recent_rps_avg = np.mean(list(self.rps_history)[-3:])
                            historical_rps_avg = np.mean(list(self.rps_history)[:-3])
                            
                            # RPS 급증 (트래픽 폭주)
                            if historical_rps_avg > 0 and recent_rps_avg > historical_rps_avg * 2:
                                anomalies.append({
                                    "is_anomaly": True,
                                    "anomaly_score": min(1.0, (recent_rps_avg / historical_rps_avg - 1) * 0.3),
                                    "anomaly_type": "rps_spike",
                                    "severity": "warning",
                                    "current_rps": recent_rps_avg,
                                    "historical_rps": historical_rps_avg
                                })
                            
                            # RPS 급감 (서비스 다운 전조)
                            elif historical_rps_avg > 0 and recent_rps_avg < historical_rps_avg * 0.3:
                                anomalies.append({
                                    "is_anomaly": True,
                                    "anomaly_score": 0.8,
                                    "anomaly_type": "rps_drop",
                                    "severity": "critical",
                                    "current_rps": recent_rps_avg,
                                    "historical_rps": historical_rps_avg
                                })
                except:
                    pass
        
        # 에러율 이상 탐지
        if len(recent_events) >= 10:
            error_count = sum(1 for e in recent_events if isinstance(e.get("status_code"), (int, float)) and e.get("status_code", 200) >= 400)
            current_error_rate = error_count / len(recent_events)
            self.error_rate_history.append(current_error_rate)
            
            if len(self.error_rate_history) >= 5:
                recent_error_rate = np.mean(list(self.error_rate_history)[-3:])
                historical_error_rate = np.mean(list(self.error_rate_history)[:-3])
                
                # 에러율 급증
                if historical_error_rate < 0.1 and recent_error_rate > 0.2:
                    anomalies.append({
                        "is_anomaly": True,
                        "anomaly_score": min(1.0, recent_error_rate * 2),
                        "anomaly_type": "error_rate_spike",
                        "severity": "critical" if recent_error_rate > 0.5 else "warning",
                        "current_error_rate": recent_error_rate,
                        "historical_error_rate": historical_error_rate
                    })
        
        return anomalies
    
    def detect_resource_anomalies(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        서버 리소스 이상 탐지 (CPU, Memory, Disk)
        
        Args:
            event: 이벤트 딕셔너리
            
        Returns:
            탐지 결과 리스트
        """
        anomalies = []
        
        # CPU 이상 탐지
        cpu_usage = event.get("cpu_usage", 0)
        if isinstance(cpu_usage, (int, float)) and cpu_usage > 0:
            self.cpu_history.append(cpu_usage)
            
            # CPU spike (갑작스러운 급등)
            if len(self.cpu_history) >= 5:
                recent_cpu = list(self.cpu_history)[-3:]
                historical_cpu = list(self.cpu_history)[:-3]
                
                if historical_cpu:
                    recent_avg = np.mean(recent_cpu)
                    historical_avg = np.mean(historical_cpu)
                    
                    if recent_avg > historical_avg * 1.5 and recent_avg > 70:
                        anomalies.append({
                            "is_anomaly": True,
                            "anomaly_score": min(1.0, (recent_avg - 70) / 30),
                            "anomaly_type": "cpu_spike",
                            "severity": "warning" if recent_avg < 90 else "critical",
                            "current_cpu": recent_avg,
                            "historical_cpu": historical_avg
                        })
                    
                    # CPU 100% 고정
                    if recent_avg >= 95:
                        anomalies.append({
                            "is_anomaly": True,
                            "anomaly_score": 1.0,
                            "anomaly_type": "cpu_saturated",
                            "severity": "critical",
                            "cpu_usage": recent_avg
                        })
        
        # Memory 이상 탐지
        memory_usage = event.get("memory_usage", 0)
        if isinstance(memory_usage, (int, float)) and memory_usage > 0:
            self.memory_history.append(memory_usage)
            
            if len(self.memory_history) >= 10:
                recent_memory = list(self.memory_history)[-5:]
                historical_memory = list(self.memory_history)[:-5]
                
                if historical_memory:
                    recent_avg = np.mean(recent_memory)
                    historical_avg = np.mean(historical_memory)
                    
                    # Memory leak (지속 증가)
                    if recent_avg > historical_avg * 1.2 and recent_avg > 80:
                        anomalies.append({
                            "is_anomaly": True,
                            "anomaly_score": min(1.0, (recent_avg - 80) / 20),
                            "anomaly_type": "memory_leak",
                            "severity": "warning" if recent_avg < 90 else "critical",
                            "current_memory": recent_avg,
                            "historical_memory": historical_avg
                        })
                    
                    # OOM 임박 경고
                    if recent_avg >= 95:
                        anomalies.append({
                            "is_anomaly": True,
                            "anomaly_score": 1.0,
                            "anomaly_type": "oom_imminent",
                            "severity": "critical",
                            "memory_usage": recent_avg
                        })
        
        return anomalies
    
    def detect_security_anomalies(
        self,
        event: Dict[str, Any],
        recent_events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        보안 공격 패턴 탐지
        
        Args:
            event: 현재 이벤트
            recent_events: 최근 이벤트 리스트
            
        Returns:
            탐지 결과 리스트
        """
        anomalies = []
        
        # IP 기반 추적
        ip = event.get("ip", event.get("remote_addr", "unknown"))
        endpoint = event.get("endpoint", "unknown")
        user_agent = event.get("user_agent", "unknown")
        
        if ip != "unknown":
            ip_data = self.ip_requests[ip]
            ip_data["count"] += 1
            ip_data["endpoints"].add(endpoint)
            ip_data["user_agents"].add(user_agent)
            ip_data["last_seen"] = datetime.now()
            ip_data["requests"].append(event)
            
            # 동일 IP 반복 호출 (Brute-force, DDoS 의심)
            if ip_data["count"] > 50:  # 짧은 시간 내 50회 이상
                anomalies.append({
                    "is_anomaly": True,
                    "anomaly_score": min(1.0, ip_data["count"] / 100),
                    "anomaly_type": "suspicious_ip_activity",
                    "severity": "warning",
                    "ip": ip,
                    "request_count": ip_data["count"],
                    "endpoints_accessed": len(ip_data["endpoints"]),
                    "description": "동일 IP에서 과도한 요청 감지"
                })
            
            # 짧은 주기의 반복 요청
            if len(ip_data["requests"]) >= 10:
                timestamps = [r.get("timestamp", "") for r in list(ip_data["requests"])[-10:]]
                try:
                    time_span = (
                        datetime.strptime(timestamps[-1], "%Y-%m-%d %H:%M:%S.%f") -
                        datetime.strptime(timestamps[0], "%Y-%m-%d %H:%M:%S.%f")
                    ).total_seconds()
                    
                    if time_span > 0 and time_span < 10:  # 10초 내 10회 이상
                        rps = 10 / time_span
                        if rps > 5:  # 초당 5회 이상
                            anomalies.append({
                                "is_anomaly": True,
                                "anomaly_score": min(1.0, rps / 10),
                                "anomaly_type": "rapid_request_pattern",
                                "severity": "warning",
                                "ip": ip,
                                "rps": rps,
                                "description": "짧은 주기 반복 요청 패턴"
                            })
                except:
                    pass
        
        # 특정 엔드포인트 집중 공격
        endpoint_counts = defaultdict(int)
        for e in recent_events[-50:]:
            endpoint_counts[e.get("endpoint", "unknown")] += 1
        
        for ep, count in endpoint_counts.items():
            if count > 30:  # 최근 50개 중 30개 이상
                anomalies.append({
                    "is_anomaly": True,
                    "anomaly_score": min(1.0, count / 50),
                    "anomaly_type": "endpoint_attack",
                    "severity": "warning",
                    "endpoint": ep,
                    "request_count": count,
                    "description": "특정 엔드포인트 집중 공격 의심"
                })
        
        return anomalies
    
    def detect(self, event: Dict[str, Any], recent_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        종합 이상 탐지
        
        Args:
            event: 현재 이벤트
            recent_events: 최근 이벤트 리스트
            
        Returns:
            종합 탐지 결과
        """
        all_anomalies = []
        
        # 1. HTTP 오류 탐지
        http_error = self.detect_http_errors(event)
        if http_error:
            all_anomalies.append(http_error)
        
        # 2. 성능 이상 탐지
        performance_anomalies = self.detect_performance_anomalies(event, recent_events)
        all_anomalies.extend(performance_anomalies)
        
        # 3. 리소스 이상 탐지
        resource_anomalies = self.detect_resource_anomalies(event)
        all_anomalies.extend(resource_anomalies)
        
        # 4. 보안 이상 탐지
        security_anomalies = self.detect_security_anomalies(event, recent_events)
        all_anomalies.extend(security_anomalies)
        
        # 종합 결과
        if all_anomalies:
            # 가장 심각한 이상 선택
            critical_anomalies = [a for a in all_anomalies if a.get("severity") == "critical"]
            if critical_anomalies:
                max_score_anomaly = max(critical_anomalies, key=lambda x: x.get("anomaly_score", 0))
            else:
                max_score_anomaly = max(all_anomalies, key=lambda x: x.get("anomaly_score", 0))
            
            return {
                "is_anomaly": True,
                "anomaly_score": max_score_anomaly.get("anomaly_score", 0.0),
                "anomaly_type": max_score_anomaly.get("anomaly_type", "unknown"),
                "severity": max_score_anomaly.get("severity", "warning"),
                "details": max_score_anomaly,
                "all_anomalies": all_anomalies,
                "anomaly_count": len(all_anomalies)
            }
        
        return {
            "is_anomaly": False,
            "anomaly_score": 0.0,
            "anomaly_type": "normal",
            "severity": "info"
        }

