"""
Mock 스트림 생성기
테스트 및 데모용으로 실시간 데이터를 시뮬레이션합니다.
"""
import time
import random
from datetime import datetime
from typing import Dict, Any, Iterator, Optional
from loguru import logger


class MockStreamGenerator:
    """Mock 데이터 스트림 생성기"""
    
    def __init__(
        self,
        events_per_second: int = 10,
        anomaly_probability: float = 0.05,
        duration: int = 0
    ):
        """
        MockStreamGenerator 초기화
        
        Args:
            events_per_second: 초당 생성할 이벤트 수
            anomaly_probability: 이상 발생 확률 (0.0 ~ 1.0)
            duration: 시뮬레이션 지속 시간 (초, 0이면 무한)
        """
        self.events_per_second = events_per_second
        self.anomaly_probability = anomaly_probability
        self.duration = duration
        self.start_time = None
        self.event_count = 0
        
        # 엔드포인트 목록
        self.endpoints = [
            "/api/users",
            "/api/products",
            "/api/orders",
            "/api/payments",
            "/api/auth",
            "/api/search",
            "/api/recommendations"
        ]
        
        # 정상 범위 설정
        self.normal_ranges = {
            "response_time": (50, 200),  # ms
            "cpu_usage": (20, 60),  # %
            "memory_usage": (30, 70),  # %
        }
    
    def _generate_normal_event(self) -> Dict[str, Any]:
        """정상 이벤트 생성"""
        endpoint = random.choice(self.endpoints)
        status_code = random.choices(
            [200, 201, 400, 404, 500],
            weights=[70, 5, 10, 10, 5]
        )[0]
        
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "endpoint": endpoint,
            "status_code": status_code,
            "response_time": random.uniform(*self.normal_ranges["response_time"]),
            "cpu_usage": random.uniform(*self.normal_ranges["cpu_usage"]),
            "memory_usage": random.uniform(*self.normal_ranges["memory_usage"]),
        }
    
    def _generate_anomaly_event(self) -> Dict[str, Any]:
        """이상 이벤트 생성"""
        endpoint = random.choice(self.endpoints)
        
        # 이상 패턴: 급격한 증가 또는 감소
        anomaly_type = random.choice(["spike", "drop", "error_spike"])
        
        if anomaly_type == "spike":
            return {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "endpoint": endpoint,
                "status_code": 200,
                "response_time": random.uniform(1000, 5000),  # 급격한 증가
                "cpu_usage": random.uniform(80, 95),
                "memory_usage": random.uniform(85, 95),
            }
        elif anomaly_type == "drop":
            return {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "endpoint": endpoint,
                "status_code": 200,
                "response_time": random.uniform(10, 30),  # 급격한 감소
                "cpu_usage": random.uniform(5, 15),
                "memory_usage": random.uniform(10, 20),
            }
        else:  # error_spike
            return {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "endpoint": endpoint,
                "status_code": random.choice([500, 503, 504]),
                "response_time": random.uniform(3000, 10000),
                "cpu_usage": random.uniform(70, 90),
                "memory_usage": random.uniform(75, 90),
            }
    
    def generate(self) -> Iterator[Dict[str, Any]]:
        """
        이벤트 스트림 생성
        
        Yields:
            이벤트 딕셔너리
        """
        self.start_time = time.time()
        interval = 1.0 / self.events_per_second
        
        logger.info(f"Mock 스트림 시작: {self.events_per_second} events/sec")
        
        while True:
            # 지속 시간 체크
            if self.duration > 0:
                elapsed = time.time() - self.start_time
                if elapsed >= self.duration:
                    logger.info(f"Mock 스트림 종료: {self.event_count}개 이벤트 생성")
                    break
            
            # 이상 또는 정상 이벤트 생성
            if random.random() < self.anomaly_probability:
                event = self._generate_anomaly_event()
                event["is_anomaly"] = True
            else:
                event = self._generate_normal_event()
                event["is_anomaly"] = False
            
            self.event_count += 1
            yield event
            
            # 다음 이벤트까지 대기
            time.sleep(interval)
    
    def get_stats(self) -> Dict[str, Any]:
        """현재 통계 정보 반환"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        return {
            "event_count": self.event_count,
            "elapsed_time": elapsed,
            "events_per_second": self.event_count / elapsed if elapsed > 0 else 0
        }

