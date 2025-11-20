"""
Change-point 탐지 모듈
급격한 변화점을 탐지합니다.
"""
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger


class ChangePointDetector:
    """Change-point 탐지기"""
    
    def __init__(
        self,
        sensitivity: float = 0.3,
        min_change: float = 0.2,
        window_size: int = 50
    ):
        """
        ChangePointDetector 초기화
        
        Args:
            sensitivity: 민감도 (0.0 ~ 1.0, 높을수록 민감)
            min_change: 최소 변화 비율 (0.0 ~ 1.0)
            window_size: 비교 윈도우 크기
        """
        self.sensitivity = sensitivity
        self.min_change = min_change
        self.window_size = window_size
        self.history: List[float] = []
    
    def detect_spike(
        self,
        values: np.ndarray,
        threshold_multiplier: Optional[float] = None
    ) -> Tuple[bool, int]:
        """
        급격한 증가(Spike) 탐지
        
        Args:
            values: 값 배열
            threshold_multiplier: 임계값 배수 (None이면 sensitivity 기반)
            
        Returns:
            (탐지 여부, 변화점 인덱스)
        """
        if len(values) < self.window_size * 2:
            return False, -1
        
        threshold_multiplier = threshold_multiplier or (1.0 + self.sensitivity)
        
        # 이전 윈도우와 현재 윈도우 비교
        prev_window = values[:self.window_size]
        current_window = values[-self.window_size:]
        
        prev_mean = np.mean(prev_window)
        current_mean = np.mean(current_window)
        
        if prev_mean == 0:
            return False, -1
        
        change_ratio = (current_mean - prev_mean) / prev_mean
        
        if change_ratio > self.min_change and current_mean > prev_mean * threshold_multiplier:
            # 변화점 위치 찾기
            change_idx = len(values) - self.window_size
            return True, change_idx
        
        return False, -1
    
    def detect_drop(
        self,
        values: np.ndarray,
        threshold_multiplier: Optional[float] = None
    ) -> Tuple[bool, int]:
        """
        급격한 감소(Drop) 탐지
        
        Args:
            values: 값 배열
            threshold_multiplier: 임계값 배수 (None이면 sensitivity 기반)
            
        Returns:
            (탐지 여부, 변화점 인덱스)
        """
        if len(values) < self.window_size * 2:
            return False, -1
        
        threshold_multiplier = threshold_multiplier or (1.0 - self.sensitivity)
        
        # 이전 윈도우와 현재 윈도우 비교
        prev_window = values[:self.window_size]
        current_window = values[-self.window_size:]
        
        prev_mean = np.mean(prev_window)
        current_mean = np.mean(current_window)
        
        if prev_mean == 0:
            return False, -1
        
        change_ratio = abs((current_mean - prev_mean) / prev_mean)
        
        if change_ratio > self.min_change and current_mean < prev_mean * threshold_multiplier:
            # 변화점 위치 찾기
            change_idx = len(values) - self.window_size
            return True, change_idx
        
        return False, -1
    
    def detect_pattern_shift(
        self,
        values: np.ndarray
    ) -> Tuple[bool, int]:
        """
        패턴 변화 탐지 (평균과 분산 모두 고려)
        
        Args:
            values: 값 배열
            
        Returns:
            (탐지 여부, 변화점 인덱스)
        """
        if len(values) < self.window_size * 2:
            return False, -1
        
        # 이전 윈도우와 현재 윈도우 비교
        prev_window = values[:self.window_size]
        current_window = values[-self.window_size:]
        
        prev_mean = np.mean(prev_window)
        prev_std = np.std(prev_window)
        current_mean = np.mean(current_window)
        current_std = np.std(current_window)
        
        # 평균 변화
        mean_change = abs(current_mean - prev_mean) / (prev_mean + 1e-10)
        
        # 분산 변화
        std_change = abs(current_std - prev_std) / (prev_std + 1e-10)
        
        # 종합 변화 점수
        total_change = (mean_change + std_change) / 2.0
        
        if total_change > self.min_change:
            change_idx = len(values) - self.window_size
            return True, change_idx
        
        return False, -1
    
    def detect_smoothed_delta(
        self,
        values: np.ndarray,
        smoothing_window: int = 10
    ) -> Tuple[bool, int]:
        """
        스무딩된 델타 기반 변화점 탐지
        
        Args:
            values: 값 배열
            smoothing_window: 스무딩 윈도우 크기
            
        Returns:
            (탐지 여부, 변화점 인덱스)
        """
        if len(values) < smoothing_window * 2:
            return False, -1
        
        # 이동 평균 계산
        smoothed = np.convolve(values, np.ones(smoothing_window) / smoothing_window, mode='same')
        
        # 델타 계산
        deltas = np.diff(smoothed)
        
        if len(deltas) == 0:
            return False, -1
        
        # 델타의 평균과 표준편차
        delta_mean = np.mean(np.abs(deltas))
        delta_std = np.std(np.abs(deltas))
        
        # 임계값
        threshold = delta_mean + self.sensitivity * delta_std
        
        # 임계값을 넘는 델타 찾기
        large_deltas = np.where(np.abs(deltas) > threshold)[0]
        
        if len(large_deltas) > 0:
            # 가장 최근의 큰 변화점
            change_idx = large_deltas[-1]
            return True, change_idx
        
        return False, -1
    
    def detect(
        self,
        feature_values: Dict[str, List[float]],
        method: str = "auto"
    ) -> Dict[str, Any]:
        """
        특징 값들로부터 변화점 탐지
        
        Args:
            feature_values: 특징별 값 리스트 딕셔너리
            method: 탐지 방법 ('spike', 'drop', 'pattern_shift', 'smoothed_delta', 'auto')
            
        Returns:
            탐지 결과 딕셔너리
        """
        results = {
            "has_changepoint": False,
            "changepoint_type": None,
            "changepoint_idx": -1,
            "details": {}
        }
        
        for feature_name, values in feature_values.items():
            if len(values) < self.window_size * 2:
                continue
            
            values_array = np.array(values)
            
            if method == "auto" or method == "spike":
                detected, idx = self.detect_spike(values_array)
                if detected:
                    results["has_changepoint"] = True
                    results["changepoint_type"] = "spike"
                    results["changepoint_idx"] = max(results["changepoint_idx"], idx)
                    results["details"][feature_name] = {
                        "type": "spike",
                        "idx": idx
                    }
                    continue
            
            if method == "auto" or method == "drop":
                detected, idx = self.detect_drop(values_array)
                if detected:
                    results["has_changepoint"] = True
                    results["changepoint_type"] = "drop"
                    results["changepoint_idx"] = max(results["changepoint_idx"], idx)
                    results["details"][feature_name] = {
                        "type": "drop",
                        "idx": idx
                    }
                    continue
            
            if method == "pattern_shift":
                detected, idx = self.detect_pattern_shift(values_array)
                if detected:
                    results["has_changepoint"] = True
                    results["changepoint_type"] = "pattern_shift"
                    results["changepoint_idx"] = max(results["changepoint_idx"], idx)
                    results["details"][feature_name] = {
                        "type": "pattern_shift",
                        "idx": idx
                    }
            
            if method == "smoothed_delta":
                detected, idx = self.detect_smoothed_delta(values_array)
                if detected:
                    results["has_changepoint"] = True
                    results["changepoint_type"] = "smoothed_delta"
                    results["changepoint_idx"] = max(results["changepoint_idx"], idx)
                    results["details"][feature_name] = {
                        "type": "smoothed_delta",
                        "idx": idx
                    }
        
        return results

