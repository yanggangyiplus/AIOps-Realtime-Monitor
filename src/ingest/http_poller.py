"""
HTTP API 폴링 수집기
실제 웹사이트나 API를 주기적으로 호출하여 모니터링합니다.
"""
import time
import requests
from datetime import datetime
from typing import Dict, Any, Iterator, List, Optional
from loguru import logger
import psutil
import os


class HTTPPoller:
    """HTTP API 폴링 수집기"""
    
    def __init__(
        self,
        urls: List[str],
        interval: float = 1.0,
        timeout: int = 5,
        headers: Optional[Dict[str, str]] = None,
        method: str = "GET"
    ):
        """
        HTTPPoller 초기화
        
        Args:
            urls: 모니터링할 URL 리스트
            interval: 폴링 간격 (초)
            timeout: 요청 타임아웃 (초)
            headers: HTTP 헤더 딕셔너리
            method: HTTP 메서드 (GET, POST 등)
        """
        self.urls = urls if isinstance(urls, list) else [urls]
        self.interval = interval
        self.timeout = timeout
        self.headers = headers or {}
        self.method = method.upper()
        self.session = requests.Session()
        self.request_count = 0
        
        # 기본 헤더 설정
        if "User-Agent" not in self.headers:
            self.headers["User-Agent"] = "AIOps-Monitor/1.0"
    
    def _get_system_metrics(self) -> Dict[str, float]:
        """
        시스템 메트릭 수집 (CPU, Memory)
        
        Returns:
            시스템 메트릭 딕셔너리
        """
        try:
            # 전체 시스템 메트릭 수집
            system_cpu = psutil.cpu_percent(interval=None)  # interval=None으로 즉시 반환
            system_memory = psutil.virtual_memory().percent
            
            # 프로세스 메트릭 (선택적)
            try:
                process = psutil.Process(os.getpid())
                process_cpu = process.cpu_percent(interval=None)
                memory_info = process.memory_info()
                process_memory_mb = memory_info.rss / (1024 * 1024)  # MB
            except:
                process_cpu = 0.0
                process_memory_mb = 0.0
            
            return {
                "cpu_usage": float(system_cpu),
                "memory_usage": float(system_memory),
                "process_cpu": float(process_cpu),
                "process_memory_mb": float(process_memory_mb)
            }
        except Exception as e:
            logger.warning(f"시스템 메트릭 수집 실패: {e}")
            # 기본값 반환
            return {
                "cpu_usage": 20.0,  # 기본값 설정
                "memory_usage": 50.0,
                "process_cpu": 0.0,
                "process_memory_mb": 0.0
            }
    
    def _poll_url(self, url: str) -> Dict[str, Any]:
        """
        단일 URL 폴링
        
        Args:
            url: 폴링할 URL
            
        Returns:
            이벤트 딕셔너리
        """
        start_time = time.time()
        status_code = None
        response_time = None
        error_message = None
        
        try:
            # HTTP 요청
            if self.method == "GET":
                response = self.session.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout
                )
            elif self.method == "POST":
                response = self.session.post(
                    url,
                    headers=self.headers,
                    timeout=self.timeout
                )
            else:
                response = self.session.request(
                    self.method,
                    url,
                    headers=self.headers,
                    timeout=self.timeout
                )
            
            response_time = (time.time() - start_time) * 1000  # ms로 변환
            status_code = response.status_code
            
            # 응답 크기 (선택적)
            response_size = len(response.content)
            
        except requests.exceptions.Timeout:
            response_time = self.timeout * 1000
            status_code = 408  # Request Timeout
            error_message = "Request timeout"
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            status_code = 0  # Connection failed
            error_message = "Connection error"
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            status_code = 500
            error_message = str(e)
        
        # 시스템 메트릭 수집
        system_metrics = self._get_system_metrics()
        
        # 이벤트 생성
        event = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "endpoint": url,
            "status_code": status_code,
            "response_time": response_time or 0.0,
            "cpu_usage": system_metrics["cpu_usage"],
            "memory_usage": system_metrics["memory_usage"],
            "method": self.method
        }
        
        if error_message:
            event["error"] = error_message
        
        if "response_size" in locals():
            event["response_size"] = response_size
        
        self.request_count += 1
        
        return event
    
    def poll(self) -> Iterator[Dict[str, Any]]:
        """
        URL들을 순차적으로 폴링
        
        Yields:
            이벤트 딕셔너리
        """
        logger.info(f"HTTP 폴링 시작: {len(self.urls)}개 URL, 간격: {self.interval}초")
        logger.info(f"URL 목록: {self.urls}")
        
        try:
            while True:
                for url in self.urls:
                    try:
                        logger.debug(f"URL 폴링 시작: {url}")
                        event = self._poll_url(url)
                        logger.info(f"이벤트 생성 완료: {event.get('endpoint', 'unknown')}, 상태: {event.get('status_code', 'unknown')}")
                        yield event
                    except Exception as e:
                        logger.error(f"URL 폴링 중 오류 ({url}): {e}")
                        # 오류 이벤트 생성
                        error_event = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                            "endpoint": url,
                            "status_code": 0,
                            "response_time": 0.0,
                            "cpu_usage": 0.0,
                            "memory_usage": 0.0,
                            "method": self.method,
                            "error": str(e)
                        }
                        yield error_event
                    
                    # 간격만큼 대기
                    time.sleep(self.interval)
        except Exception as e:
            logger.error(f"HTTP 폴링 루프 중 치명적 오류: {e}")
            logger.exception(e)
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """폴링 통계 정보 반환"""
        return {
            "request_count": self.request_count,
            "urls": self.urls,
            "interval": self.interval
        }
    
    def __enter__(self):
        """Context manager 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.session.close()

