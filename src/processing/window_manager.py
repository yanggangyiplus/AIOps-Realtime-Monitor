"""
윈도우 관리자
슬라이딩 윈도우를 관리하고 시간 기반 집계를 수행합니다.
"""
from collections import deque
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from loguru import logger


class WindowManager:
    """슬라이딩 윈도우 관리자"""
    
    def __init__(self, window_size: int = 100, max_size: int = 10000):
        """
        WindowManager 초기화
        
        Args:
            window_size: 기본 윈도우 크기
            max_size: 최대 저장 데이터 포인트 수
        """
        self.window_size = window_size
        self.max_size = max_size
        self.data_buffer = deque(maxlen=max_size)
        self.windows: Dict[str, deque] = {}
    
    def add_event(self, event: Dict[str, Any]):
        """
        이벤트 추가
        
        Args:
            event: 추가할 이벤트 딕셔너리
        """
        # 타임스탬프 추가
        if "timestamp" not in event:
            event["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        
        self.data_buffer.append(event)
    
    def get_window(self, window_name: str, size: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        특정 윈도우의 데이터 반환
        
        Args:
            window_name: 윈도우 이름
            size: 윈도우 크기 (None이면 기본값 사용)
            
        Returns:
            윈도우 데이터 리스트
        """
        if window_name not in self.windows:
            self.windows[window_name] = deque(maxlen=size or self.window_size)
        
        return list(self.windows[window_name])
    
    def update_window(self, window_name: str, event: Dict[str, Any], size: Optional[int] = None):
        """
        특정 윈도우에 이벤트 추가
        
        Args:
            window_name: 윈도우 이름
            event: 추가할 이벤트
            size: 윈도우 크기 (None이면 기본값 사용)
        """
        if window_name not in self.windows:
            self.windows[window_name] = deque(maxlen=size or self.window_size)
        
        self.windows[window_name].append(event)
    
    def get_recent_events(self, count: int = None) -> List[Dict[str, Any]]:
        """
        최근 이벤트 반환
        
        Args:
            count: 반환할 이벤트 수 (None이면 전체)
            
        Returns:
            최근 이벤트 리스트
        """
        if count is None:
            return list(self.data_buffer)
        return list(self.data_buffer)[-count:]
    
    def get_time_window(
        self,
        seconds: int,
        field: str = "timestamp",
        format: str = "%Y-%m-%d %H:%M:%S.%f"
    ) -> List[Dict[str, Any]]:
        """
        시간 기반 윈도우 데이터 반환
        
        Args:
            seconds: 시간 윈도우 크기 (초)
            field: 타임스탬프 필드명
            format: 타임스탬프 포맷
            
        Returns:
            시간 윈도우 내의 이벤트 리스트
        """
        if not self.data_buffer:
            return []
        
        # 최신 이벤트의 타임스탬프
        latest_event = self.data_buffer[-1]
        latest_time = datetime.strptime(latest_event[field], format)
        cutoff_time = latest_time.timestamp() - seconds
        
        result = []
        for event in reversed(self.data_buffer):
            event_time = datetime.strptime(event[field], format).timestamp()
            if event_time >= cutoff_time:
                result.insert(0, event)
            else:
                break
        
        return result
    
    def to_dataframe(self, window_name: Optional[str] = None) -> pd.DataFrame:
        """
        윈도우 데이터를 DataFrame으로 변환
        
        Args:
            window_name: 윈도우 이름 (None이면 전체 버퍼)
            
        Returns:
            DataFrame
        """
        if window_name:
            data = self.get_window(window_name)
        else:
            data = list(self.data_buffer)
        
        if not data:
            return pd.DataFrame()
        
        return pd.DataFrame(data)
    
    def clear(self, window_name: Optional[str] = None):
        """
        윈도우 데이터 초기화
        
        Args:
            window_name: 윈도우 이름 (None이면 전체 초기화)
        """
        if window_name:
            if window_name in self.windows:
                self.windows[window_name].clear()
        else:
            self.data_buffer.clear()
            self.windows.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """윈도우 통계 정보 반환"""
        return {
            "buffer_size": len(self.data_buffer),
            "window_count": len(self.windows),
            "windows": {
                name: len(window) for name, window in self.windows.items()
            }
        }

