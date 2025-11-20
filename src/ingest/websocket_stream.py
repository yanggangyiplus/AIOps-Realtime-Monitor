"""
WebSocket 기반 스트림 수집기
WebSocket을 통해 실시간 데이터를 수집합니다.
"""
import websocket
import json
import threading
import time
from typing import Dict, Any, Iterator, Optional, Callable
from loguru import logger


class WebSocketStreamCollector:
    """WebSocket 기반 스트림 수집기"""
    
    def __init__(
        self,
        url: str = "ws://localhost:8765",
        reconnect_interval: int = 5
    ):
        """
        WebSocketStreamCollector 초기화
        
        Args:
            url: WebSocket 서버 URL
            reconnect_interval: 재연결 시도 간격 (초)
        """
        self.url = url
        self.reconnect_interval = reconnect_interval
        self.ws: Optional[websocket.WebSocketApp] = None
        self.connected = False
        self.event_queue = []
        self.queue_lock = threading.Lock()
        self.should_reconnect = True
    
    def _on_message(self, ws, message):
        """메시지 수신 핸들러"""
        try:
            event = json.loads(message)
            with self.queue_lock:
                self.event_queue.append(event)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 파싱 오류: {e}, 데이터: {message}")
    
    def _on_error(self, ws, error):
        """에러 핸들러"""
        logger.error(f"WebSocket 오류: {error}")
        self.connected = False
    
    def _on_close(self, ws, close_status_code, close_msg):
        """연결 종료 핸들러"""
        logger.info("WebSocket 연결 종료")
        self.connected = False
    
    def _on_open(self, ws):
        """연결 시작 핸들러"""
        logger.info(f"WebSocket 연결 성공: {self.url}")
        self.connected = True
    
    def connect(self) -> bool:
        """
        WebSocket 연결 시도
        
        Returns:
            연결 성공 여부
        """
        try:
            self.ws = websocket.WebSocketApp(
                self.url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # 별도 스레드에서 WebSocket 실행
            self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            self.ws_thread.start()
            
            # 연결 확인 대기
            for _ in range(10):  # 최대 10초 대기
                if self.connected:
                    return True
                time.sleep(1)
            
            logger.error("WebSocket 연결 타임아웃")
            return False
            
        except Exception as e:
            logger.error(f"WebSocket 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """WebSocket 연결 종료"""
        self.should_reconnect = False
        if self.ws:
            self.ws.close()
            self.connected = False
            logger.info("WebSocket 연결 종료")
    
    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        데이터 수집 스트림
        
        Yields:
            수집된 이벤트 딕셔너리
        """
        if not self.connected:
            if not self.connect():
                logger.error("WebSocket 연결이 없습니다.")
                return
        
        while self.should_reconnect:
            # 큐에서 이벤트 가져오기
            with self.queue_lock:
                if self.event_queue:
                    event = self.event_queue.pop(0)
                    yield event
                else:
                    time.sleep(0.1)  # 큐가 비어있으면 잠시 대기
            
            # 연결이 끊어졌고 재연결이 필요한 경우
            if not self.connected and self.should_reconnect:
                logger.info(f"{self.reconnect_interval}초 후 재연결 시도...")
                time.sleep(self.reconnect_interval)
                self.connect()
    
    def __enter__(self):
        """Context manager 진입"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.disconnect()

