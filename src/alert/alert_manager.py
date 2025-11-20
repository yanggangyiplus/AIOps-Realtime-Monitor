"""
알림 관리자
이상 탐지 결과를 기반으로 알림을 생성하고 관리합니다.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque
from loguru import logger


class Alert:
    """알림 클래스"""
    
    def __init__(
        self,
        level: str,
        message: str,
        details: Dict[str, Any],
        timestamp: Optional[str] = None
    ):
        """
        Alert 초기화
        
        Args:
            level: 알림 레벨 ('info', 'warning', 'critical')
            message: 알림 메시지
            details: 상세 정보 딕셔너리
            timestamp: 타임스탬프 (None이면 현재 시간)
        """
        self.level = level
        self.message = message
        self.details = details
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        self.acknowledged = False
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "level": self.level,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "acknowledged": self.acknowledged
        }


class AlertManager:
    """알림 관리자"""
    
    def __init__(
        self,
        max_alerts: int = 1000,
        alert_threshold: float = 0.7,
        deduplication_window: int = 60
    ):
        """
        AlertManager 초기화
        
        Args:
            max_alerts: 최대 알림 수
            alert_threshold: 알림 생성 임계값 (0.0 ~ 1.0)
            deduplication_window: 중복 제거 윈도우 (초)
        """
        self.max_alerts = max_alerts
        self.alert_threshold = alert_threshold
        self.deduplication_window = deduplication_window
        
        # 알림 저장소
        self.alerts: deque = deque(maxlen=max_alerts)
        
        # 중복 제거용 (최근 알림 해시)
        self.recent_alert_hashes: deque = deque(maxlen=100)
    
    def _generate_alert_hash(self, message: str, details: Dict[str, Any]) -> str:
        """
        알림 해시 생성 (중복 제거용)
        
        Args:
            message: 알림 메시지
            details: 상세 정보
            
        Returns:
            해시 문자열
        """
        # 간단한 해시 생성
        key_parts = [message]
        if "is_anomaly" in details:
            key_parts.append(str(details["is_anomaly"]))
        if "anomaly_score" in details:
            key_parts.append(f"{details['anomaly_score']:.2f}")
        
        return "|".join(key_parts)
    
    def _is_duplicate(self, alert_hash: str) -> bool:
        """
        중복 알림 여부 확인
        
        Args:
            alert_hash: 알림 해시
            
        Returns:
            중복 여부
        """
        return alert_hash in self.recent_alert_hashes
    
    def _determine_level(self, anomaly_score: float, is_anomaly: bool) -> str:
        """
        알림 레벨 결정
        
        Args:
            anomaly_score: 이상 점수
            is_anomaly: 이상 여부
            
        Returns:
            알림 레벨
        """
        if not is_anomaly:
            return "info"
        
        if anomaly_score >= 0.9:
            return "critical"
        elif anomaly_score >= 0.7:
            return "warning"
        else:
            return "info"
    
    def create_alert(
        self,
        detection_result: Dict[str, Any],
        event: Optional[Dict[str, Any]] = None
    ) -> Optional[Alert]:
        """
        탐지 결과로부터 알림 생성
        
        Args:
            detection_result: 이상 탐지 결과
            event: 원본 이벤트 (선택적)
            
        Returns:
            생성된 Alert 객체 (생성되지 않으면 None)
        """
        is_anomaly = detection_result.get("is_anomaly", False)
        anomaly_score = detection_result.get("anomaly_score", 0.0)
        
        # HTTP 에러 상태 코드는 즉시 알림 생성 (임계값 무시)
        is_http_error = False
        if event:
            status_code = event.get("status_code", 200)
            if isinstance(status_code, (int, float)) and status_code >= 400:
                is_http_error = True
                # HTTP 에러는 항상 이상으로 처리
                is_anomaly = True
                anomaly_score = 1.0 if status_code >= 500 else 0.8
        
        # 임계값 체크 (HTTP 에러는 제외)
        if not is_http_error and (not is_anomaly or anomaly_score < self.alert_threshold):
            return None
        
        # 알림 메시지 생성
        message = self._generate_message(detection_result, event)
        
        # 알림 레벨 결정
        level = self._determine_level(anomaly_score, is_anomaly)
        
        # 상세 정보 구성
        details = {
            "anomaly_score": anomaly_score,
            "is_anomaly": is_anomaly,
            "method": detection_result.get("method", "unknown"),
            "detection_details": detection_result.get("details", {})
        }
        
        if event:
            details["event"] = {
                "endpoint": event.get("endpoint", "unknown"),
                "status_code": event.get("status_code", "unknown"),
                "timestamp": event.get("timestamp", "unknown")
            }
        
        # 중복 체크
        alert_hash = self._generate_alert_hash(message, details)
        if self._is_duplicate(alert_hash):
            logger.debug(f"중복 알림 무시: {message}")
            return None
        
        # 알림 생성
        alert = Alert(level=level, message=message, details=details)
        
        # 알림 저장
        self.alerts.append(alert)
        self.recent_alert_hashes.append(alert_hash)
        
        logger.info(f"알림 생성: [{level.upper()}] {message}")
        
        return alert
    
    def _generate_message(
        self,
        detection_result: Dict[str, Any],
        event: Optional[Dict[str, Any]]
    ) -> str:
        """
        알림 메시지 생성
        
        Args:
            detection_result: 탐지 결과
            event: 원본 이벤트
            
        Returns:
            알림 메시지
        """
        anomaly_score = detection_result.get("anomaly_score", 0.0)
        method = detection_result.get("method", "unknown")
        
        # HTTP 에러 상태 코드 처리
        if event:
            status_code = event.get("status_code", 200)
            if isinstance(status_code, (int, float)) and status_code >= 400:
                endpoint = event.get("endpoint", "unknown")
                status_messages = {
                    400: "Bad Request",
                    401: "Unauthorized",
                    403: "Forbidden",
                    404: "Not Found",
                    408: "Request Timeout",
                    418: "I'm a teapot",
                    500: "Internal Server Error",
                    502: "Bad Gateway",
                    503: "Service Unavailable",
                    504: "Gateway Timeout"
                }
                status_msg = status_messages.get(status_code, f"HTTP {status_code}")
                return f"[{endpoint}] HTTP 에러 발생: {status_code} {status_msg}"
        
        base_message = f"이상 탐지됨 (점수: {anomaly_score:.2f}, 방법: {method})"
        
        if event:
            endpoint = event.get("endpoint", "unknown")
            status_code = event.get("status_code", "unknown")
            base_message = f"[{endpoint}] {base_message} (상태: {status_code})"
        
        # Change-point 정보 추가
        details = detection_result.get("details", {})
        if "changepoint" in details:
            cp_info = details["changepoint"]
            if cp_info.get("has_changepoint", False):
                cp_type = cp_info.get("changepoint_type", "unknown")
                base_message += f" | 변화점: {cp_type}"
        
        return base_message
    
    def get_recent_alerts(
        self,
        count: int = 50,
        level: Optional[str] = None
    ) -> List[Alert]:
        """
        최근 알림 조회
        
        Args:
            count: 반환할 알림 수
            level: 필터링할 레벨 (None이면 전체)
            
        Returns:
            알림 리스트
        """
        alerts = list(self.alerts)
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts[-count:]
    
    def acknowledge_alert(self, alert_index: int):
        """
        알림 확인 처리
        
        Args:
            alert_index: 알림 인덱스 (최신부터 역순)
        """
        alerts_list = list(self.alerts)
        if 0 <= alert_index < len(alerts_list):
            alerts_list[-(alert_index + 1)].acknowledged = True
            logger.info(f"알림 확인 처리: 인덱스 {alert_index}")
    
    def get_stats(self) -> Dict[str, Any]:
        """알림 통계 정보 반환"""
        alerts_list = list(self.alerts)
        
        level_counts = {}
        for alert in alerts_list:
            level_counts[alert.level] = level_counts.get(alert.level, 0) + 1
        
        return {
            "total_alerts": len(alerts_list),
            "level_counts": level_counts,
            "unacknowledged": sum(1 for a in alerts_list if not a.acknowledged),
            "alert_threshold": self.alert_threshold
        }
    
    def clear_alerts(self, level: Optional[str] = None):
        """
        알림 초기화
        
        Args:
            level: 초기화할 레벨 (None이면 전체)
        """
        if level:
            self.alerts = deque(
                [a for a in self.alerts if a.level != level],
                maxlen=self.max_alerts
            )
        else:
            self.alerts.clear()
        
        logger.info(f"알림 초기화: {level or '전체'}")

