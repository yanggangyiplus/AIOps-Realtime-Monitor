"""
Socket 기반 스트림 수집기
TCP Socket을 통해 실시간 데이터를 수집합니다.
"""
import socket
import json
from typing import Dict, Any, Iterator, Optional
from loguru import logger


class SocketStreamCollector:
    """Socket 기반 스트림 수집기"""
    
    def __init__(self, host: str = "localhost", port: int = 8888, buffer_size: int = 1024):
        """
        SocketStreamCollector 초기화
        
        Args:
            host: 서버 호스트 주소
            port: 서버 포트 번호
            buffer_size: 수신 버퍼 크기
        """
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.socket: Optional[socket.socket] = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        Socket 연결 시도
        
        Returns:
            연결 성공 여부
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.port))
            self.connected = True
            logger.info(f"Socket 연결 성공: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Socket 연결 실패: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Socket 연결 종료"""
        if self.socket:
            try:
                self.socket.close()
                logger.info("Socket 연결 종료")
            except Exception as e:
                logger.error(f"Socket 종료 중 오류: {e}")
            finally:
                self.socket = None
                self.connected = False
    
    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        데이터 수집 스트림
        
        Yields:
            수집된 이벤트 딕셔너리
        """
        if not self.connected:
            if not self.connect():
                logger.error("Socket 연결이 없습니다.")
                return
        
        buffer = ""
        
        while self.connected:
            try:
                # 데이터 수신
                data = self.socket.recv(self.buffer_size).decode('utf-8')
                
                if not data:
                    logger.warning("연결이 끊어졌습니다.")
                    break
                
                buffer += data
                
                # 완전한 JSON 메시지 추출 (줄바꿈으로 구분)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line:
                        try:
                            event = json.loads(line)
                            yield event
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON 파싱 오류: {e}, 데이터: {line}")
                            
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"데이터 수집 중 오류: {e}")
                break
    
    def __enter__(self):
        """Context manager 진입"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.disconnect()

