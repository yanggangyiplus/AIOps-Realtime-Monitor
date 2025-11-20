"""
특징 엔지니어링 모듈
실시간 스트림 데이터로부터 통계적 특징을 추출합니다.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger


class FeatureEngineer:
    """특징 엔지니어링 클래스"""
    
    def __init__(self, window_size: int = 100):
        """
        FeatureEngineer 초기화
        
        Args:
            window_size: 롤링 윈도우 크기
        """
        self.window_size = window_size
    
    def calculate_rps(self, events: List[Dict[str, Any]], time_window: int = 1) -> float:
        """
        초당 요청 수 (RPS) 계산
        
        Args:
            events: 이벤트 리스트
            time_window: 시간 윈도우 (초)
            
        Returns:
            RPS 값
        """
        if not events:
            return 0.0
        
        if len(events) < 2:
            return 1.0
        
        # 타임스탬프 추출 및 정렬
        timestamps = []
        for event in events:
            try:
                ts_str = event.get("timestamp", "")
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f")
                timestamps.append(ts.timestamp())
            except:
                continue
        
        if len(timestamps) < 2:
            return len(events) / time_window
        
        # 시간 범위 계산
        time_span = max(timestamps) - min(timestamps)
        if time_span == 0:
            return len(events) / time_window
        
        # RPS 계산
        rps = len(events) / max(time_span, time_window)
        return rps
    
    def calculate_error_rate(self, events: List[Dict[str, Any]]) -> float:
        """
        에러 비율 계산
        
        Args:
            events: 이벤트 리스트
            
        Returns:
            에러 비율 (0.0 ~ 1.0)
        """
        if not events:
            return 0.0
        
        error_count = 0
        total_count = 0
        
        for event in events:
            status_code = event.get("status_code", 200)
            if isinstance(status_code, (int, float)):
                total_count += 1
                if status_code >= 400:
                    error_count += 1
        
        if total_count == 0:
            return 0.0
        
        return error_count / total_count
    
    def calculate_moving_average(
        self,
        values: np.ndarray,
        window: Optional[int] = None
    ) -> np.ndarray:
        """
        이동 평균 계산
        
        Args:
            values: 값 배열
            window: 윈도우 크기 (None이면 기본값 사용)
            
        Returns:
            이동 평균 배열
        """
        window = window or self.window_size
        
        if len(values) < window:
            return np.full(len(values), np.mean(values))
        
        return np.convolve(values, np.ones(window) / window, mode='same')
    
    def calculate_ema(
        self,
        values: np.ndarray,
        alpha: Optional[float] = None,
        window: Optional[int] = None
    ) -> np.ndarray:
        """
        지수 이동 평균 (EMA) 계산
        
        Args:
            values: 값 배열
            alpha: 스무딩 팩터 (None이면 window 기반 계산)
            window: 윈도우 크기 (alpha가 None일 때 사용)
            
        Returns:
            EMA 배열
        """
        if len(values) == 0:
            return values
        
        if alpha is None:
            window = window or self.window_size
            alpha = 2.0 / (window + 1.0)
        
        ema = np.zeros_like(values)
        ema[0] = values[0]
        
        for i in range(1, len(values)):
            ema[i] = alpha * values[i] + (1 - alpha) * ema[i-1]
        
        return ema
    
    def calculate_rolling_stats(
        self,
        values: np.ndarray,
        window: Optional[int] = None
    ) -> Dict[str, np.ndarray]:
        """
        롤링 통계 계산
        
        Args:
            values: 값 배열
            window: 윈도우 크기 (None이면 기본값 사용)
            
        Returns:
            통계 딕셔너리 (mean, std, min, max, var)
        """
        window = window or self.window_size
        
        if len(values) < window:
            return {
                "mean": np.full(len(values), np.mean(values)),
                "std": np.full(len(values), np.std(values)),
                "min": np.full(len(values), np.min(values)),
                "max": np.full(len(values), np.max(values)),
                "var": np.full(len(values), np.var(values))
            }
        
        df = pd.Series(values)
        
        return {
            "mean": df.rolling(window=window, center=True).mean().fillna(df.mean()).values,
            "std": df.rolling(window=window, center=True).std().fillna(df.std()).values,
            "min": df.rolling(window=window, center=True).min().fillna(df.min()).values,
            "max": df.rolling(window=window, center=True).max().fillna(df.max()).values,
            "var": df.rolling(window=window, center=True).var().fillna(df.var()).values
        }
    
    def calculate_spike_score(
        self,
        values: np.ndarray,
        window: Optional[int] = None
    ) -> np.ndarray:
        """
        스파이크 점수 계산 (현재 값이 평균 대비 얼마나 높은지)
        
        Args:
            values: 값 배열
            window: 윈도우 크기 (None이면 기본값 사용)
            
        Returns:
            스파이크 점수 배열
        """
        window = window or self.window_size
        
        if len(values) < 2:
            return np.zeros_like(values)
        
        rolling_stats = self.calculate_rolling_stats(values, window)
        mean = rolling_stats["mean"]
        std = rolling_stats["std"]
        
        # Z-score 기반 스파이크 점수
        spike_scores = np.zeros_like(values)
        for i in range(len(values)):
            if std[i] > 0:
                spike_scores[i] = (values[i] - mean[i]) / std[i]
            else:
                spike_scores[i] = 0.0
        
        return spike_scores
    
    def extract_features(
        self,
        events: List[Dict[str, Any]],
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        이벤트 리스트로부터 특징 추출
        
        Args:
            events: 이벤트 리스트
            fields: 특징을 추출할 필드 리스트 (None이면 자동 감지)
            
        Returns:
            특징 딕셔너리
        """
        if not events:
            return {}
        
        if fields is None:
            fields = ["response_time", "cpu_usage", "memory_usage"]
        
        features = {}
        
        # 기본 통계 특징
        features["rps"] = self.calculate_rps(events)
        features["error_rate"] = self.calculate_error_rate(events)
        features["event_count"] = len(events)
        
        # 수치 필드별 특징 추출
        for field in fields:
            if field not in events[0]:
                continue
            
            values = np.array([e.get(field, 0) for e in events if isinstance(e.get(field), (int, float))])
            
            if len(values) == 0:
                continue
            
            # 기본 통계
            features[f"{field}_mean"] = float(np.mean(values))
            features[f"{field}_std"] = float(np.std(values))
            features[f"{field}_min"] = float(np.min(values))
            features[f"{field}_max"] = float(np.max(values))
            features[f"{field}_median"] = float(np.median(values))
            
            # 롤링 통계 (최근 값 기준)
            if len(values) >= 2:
                rolling_stats = self.calculate_rolling_stats(values)
                features[f"{field}_rolling_mean"] = float(rolling_stats["mean"][-1])
                features[f"{field}_rolling_std"] = float(rolling_stats["std"][-1])
                
                # 스파이크 점수
                spike_scores = self.calculate_spike_score(values)
                features[f"{field}_spike_score"] = float(spike_scores[-1])
                
                # EMA
                ema = self.calculate_ema(values)
                features[f"{field}_ema"] = float(ema[-1])
        
        return features
    
    def extract_single_event_features(
        self,
        event: Dict[str, Any],
        historical_events: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        단일 이벤트의 특징 추출 (히스토리 기반)
        
        Args:
            event: 현재 이벤트
            historical_events: 히스토리 이벤트 리스트 (없으면 기본값 사용)
            
        Returns:
            특징 딕셔너리
        """
        features = {}
        
        # 기본 필드 복사
        for key in ["timestamp", "endpoint", "status_code"]:
            if key in event:
                features[key] = event[key]
        
        # 수치 필드
        numeric_fields = ["response_time", "cpu_usage", "memory_usage"]
        
        if historical_events:
            # 히스토리 기반 특징 추출
            hist_features = self.extract_features(historical_events)
            
            # 현재 값과 히스토리 비교
            for field in numeric_fields:
                if field in event and isinstance(event[field], (int, float)):
                    current_value = event[field]
                    hist_mean = hist_features.get(f"{field}_mean", current_value)
                    hist_std = hist_features.get(f"{field}_std", 1.0)
                    
                    features[field] = current_value
                    features[f"{field}_zscore"] = (current_value - hist_mean) / hist_std if hist_std > 0 else 0.0
                    features[f"{field}_deviation"] = current_value - hist_mean
        else:
            # 히스토리가 없으면 기본값만
            for field in numeric_fields:
                if field in event:
                    features[field] = event[field]
        
        # 에러 여부
        status_code = event.get("status_code", 200)
        features["is_error"] = 1 if isinstance(status_code, (int, float)) and status_code >= 400 else 0
        
        return features

