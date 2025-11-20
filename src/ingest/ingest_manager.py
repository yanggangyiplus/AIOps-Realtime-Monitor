"""
스트림 수집 관리자
다양한 수집 방식을 통합 관리합니다.
"""
from typing import Dict, Any, Iterator, Optional
from loguru import logger

from .mock_stream import MockStreamGenerator
from .socket_stream import SocketStreamCollector
from .websocket_stream import WebSocketStreamCollector
from .http_poller import HTTPPoller
from ..utils.config import get_config_loader


class IngestManager:
    """스트림 수집 관리자"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        IngestManager 초기화
        
        Args:
            config: 스트림 설정 딕셔너리 (None이면 설정 파일에서 로드)
        """
        if config is None:
            config_loader = get_config_loader()
            config = config_loader.get_stream_config()
        
        self.config = config
        self.stream_config = config.get("stream", {})
        self.mode = self.stream_config.get("mode", "mock")
        self.collector = None
    
    def _create_collector(self):
        """설정에 따라 적절한 수집기 생성"""
        if self.mode == "mock":
            mock_config = self.stream_config.get("mock", {})
            self.collector = MockStreamGenerator(
                events_per_second=mock_config.get("events_per_second", 10),
                anomaly_probability=mock_config.get("anomaly_probability", 0.05),
                duration=mock_config.get("duration", 0)
            )
            logger.info(f"Mock 스트림 수집기 생성: {mock_config}")
            
        elif self.mode == "socket":
            socket_config = self.stream_config.get("socket", {})
            self.collector = SocketStreamCollector(
                host=socket_config.get("host", "localhost"),
                port=socket_config.get("port", 8888),
                buffer_size=socket_config.get("buffer_size", 1024)
            )
            logger.info(f"Socket 스트림 수집기 생성: {socket_config}")
            
        elif self.mode == "websocket":
            ws_config = self.stream_config.get("websocket", {})
            self.collector = WebSocketStreamCollector(
                url=ws_config.get("url", "ws://localhost:8765"),
                reconnect_interval=ws_config.get("reconnect_interval", 5)
            )
            logger.info(f"WebSocket 스트림 수집기 생성: {ws_config}")
            
        elif self.mode == "http":
            http_config = self.stream_config.get("http", {})
            urls = http_config.get("urls", ["https://www.google.com"])
            if isinstance(urls, str):
                urls = [urls]
            
            self.collector = HTTPPoller(
                urls=urls,
                interval=http_config.get("interval", 1.0),
                timeout=http_config.get("timeout", 5),
                headers=http_config.get("headers", {}),
                method=http_config.get("method", "GET")
            )
            logger.info(f"HTTP 폴링 수집기 생성: {len(urls)}개 URL")
            
        else:
            raise ValueError(f"지원하지 않는 수집 모드: {self.mode}")
    
    def start(self) -> Iterator[Dict[str, Any]]:
        """
        스트림 수집 시작
        
        Returns:
            이벤트 스트림 Iterator
        """
        if self.collector is None:
            self._create_collector()
        
        logger.info(f"스트림 수집 시작 (모드: {self.mode})")
        
        if self.mode == "mock":
            return self.collector.generate()
        elif self.mode == "http":
            return self.collector.poll()
        else:
            return self.collector.collect()
    
    def stop(self):
        """스트림 수집 중지"""
        if self.collector:
            if hasattr(self.collector, 'disconnect'):
                self.collector.disconnect()
            logger.info("스트림 수집 중지")
    
    def get_stats(self) -> Dict[str, Any]:
        """수집 통계 정보 반환"""
        if self.collector and hasattr(self.collector, 'get_stats'):
            return self.collector.get_stats()
        return {}

