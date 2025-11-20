"""
전처리 모듈
데이터 정제, 스무딩, 클리핑 등을 수행합니다.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from loguru import logger


class Preprocessor:
    """데이터 전처리기"""
    
    def __init__(
        self,
        clip_outliers: bool = True,
        smoothing_window: int = 5,
        scaling_method: Optional[str] = None
    ):
        """
        Preprocessor 초기화
        
        Args:
            clip_outliers: 이상치 클리핑 여부
            smoothing_window: 스무딩 윈도우 크기
            scaling_method: 스케일링 방법 (None, 'minmax', 'standard', 'robust')
        """
        self.clip_outliers = clip_outliers
        self.smoothing_window = smoothing_window
        self.scaling_method = scaling_method
        self.scaler_params: Dict[str, Dict[str, float]] = {}
    
    def clip_outlier_values(
        self,
        values: np.ndarray,
        method: str = "iqr",
        multiplier: float = 1.5
    ) -> np.ndarray:
        """
        이상치 클리핑
        
        Args:
            values: 값 배열
            method: 클리핑 방법 ('iqr', 'zscore')
            multiplier: IQR 배수 또는 Z-score 임계값
            
        Returns:
            클리핑된 값 배열
        """
        if len(values) == 0:
            return values
        
        if method == "iqr":
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            lower_bound = q1 - multiplier * iqr
            upper_bound = q3 + multiplier * iqr
            return np.clip(values, lower_bound, upper_bound)
        
        elif method == "zscore":
            mean = np.mean(values)
            std = np.std(values)
            if std == 0:
                return values
            z_scores = np.abs((values - mean) / std)
            mask = z_scores <= multiplier
            # 이상치를 경계값으로 클리핑
            clipped = values.copy()
            clipped[~mask] = np.clip(
                clipped[~mask],
                mean - multiplier * std,
                mean + multiplier * std
            )
            return clipped
        
        return values
    
    def smooth(
        self,
        values: np.ndarray,
        method: str = "moving_average",
        window: Optional[int] = None
    ) -> np.ndarray:
        """
        데이터 스무딩
        
        Args:
            values: 값 배열
            method: 스무딩 방법 ('moving_average', 'ema')
            window: 윈도우 크기 (None이면 기본값 사용)
            
        Returns:
            스무딩된 값 배열
        """
        if len(values) == 0:
            return values
        
        window = window or self.smoothing_window
        
        if method == "moving_average":
            if len(values) < window:
                return values
            
            smoothed = np.convolve(values, np.ones(window) / window, mode='same')
            return smoothed
        
        elif method == "ema":
            if len(values) < 2:
                return values
            
            alpha = 2.0 / (window + 1.0)
            smoothed = np.zeros_like(values)
            smoothed[0] = values[0]
            
            for i in range(1, len(values)):
                smoothed[i] = alpha * values[i] + (1 - alpha) * smoothed[i-1]
            
            return smoothed
        
        return values
    
    def scale(
        self,
        values: np.ndarray,
        field_name: str,
        method: Optional[str] = None
    ) -> np.ndarray:
        """
        데이터 스케일링
        
        Args:
            values: 값 배열
            field_name: 필드 이름 (파라미터 저장용)
            method: 스케일링 방법 (None이면 기본값 사용)
            
        Returns:
            스케일링된 값 배열
        """
        if len(values) == 0:
            return values
        
        method = method or self.scaling_method
        if method is None:
            return values
        
        if method == "minmax":
            min_val = np.min(values)
            max_val = np.max(values)
            if max_val == min_val:
                return np.zeros_like(values)
            
            self.scaler_params[field_name] = {
                "min": float(min_val),
                "max": float(max_val)
            }
            return (values - min_val) / (max_val - min_val)
        
        elif method == "standard":
            mean = np.mean(values)
            std = np.std(values)
            if std == 0:
                return np.ones_like(values) * 0.5
            
            self.scaler_params[field_name] = {
                "mean": float(mean),
                "std": float(std)
            }
            return (values - mean) / std
        
        elif method == "robust":
            median = np.median(values)
            q75 = np.percentile(values, 75)
            q25 = np.percentile(values, 25)
            iqr = q75 - q25
            if iqr == 0:
                return np.zeros_like(values)
            
            self.scaler_params[field_name] = {
                "median": float(median),
                "iqr": float(iqr)
            }
            return (values - median) / iqr
        
        return values
    
    def preprocess_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        단일 이벤트 전처리
        
        Args:
            event: 원본 이벤트
            
        Returns:
            전처리된 이벤트
        """
        processed = event.copy()
        
        # 수치 필드 전처리
        numeric_fields = ["response_time", "cpu_usage", "memory_usage"]
        
        for field in numeric_fields:
            if field in processed:
                value = processed[field]
                if isinstance(value, (int, float)):
                    # 단일 값은 그대로 유지 (윈도우 단위로 처리)
                    processed[f"{field}_original"] = value
                else:
                    # 배열인 경우 전처리 적용
                    values = np.array(value)
                    
                    if self.clip_outliers:
                        values = self.clip_outlier_values(values)
                    
                    if self.smoothing_window > 1:
                        values = self.smooth(values)
                    
                    if self.scaling_method:
                        values = self.scale(values, field)
                    
                    processed[field] = values.tolist()
        
        return processed
    
    def preprocess_batch(
        self,
        events: List[Dict[str, Any]],
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        배치 데이터 전처리
        
        Args:
            events: 이벤트 리스트
            fields: 전처리할 필드 리스트 (None이면 자동 감지)
            
        Returns:
            전처리된 DataFrame
        """
        if not events:
            return pd.DataFrame()
        
        df = pd.DataFrame(events)
        
        if fields is None:
            fields = ["response_time", "cpu_usage", "memory_usage"]
        
        for field in fields:
            if field in df.columns:
                values = df[field].values
                
                # 결측값 처리
                values = np.nan_to_num(values, nan=np.nanmean(values) if not np.all(np.isnan(values)) else 0)
                
                # 이상치 클리핑
                if self.clip_outliers:
                    values = self.clip_outlier_values(values)
                
                # 스무딩
                if self.smoothing_window > 1 and len(values) > self.smoothing_window:
                    values = self.smooth(values)
                
                # 스케일링
                if self.scaling_method:
                    values = self.scale(values, field)
                
                df[field] = values
        
        return df

