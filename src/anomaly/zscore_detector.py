"""
Z-score 기반 이상 탐지기
통계적 방법을 사용하여 이상을 탐지합니다.
"""
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger


class ZScoreDetector:
    """Z-score 기반 이상 탐지기"""
    
    def __init__(self, threshold: float = 3.0, window_size: int = 100):
        """
        ZScoreDetector 초기화
        
        Args:
            threshold: Z-score 임계값 (기본값: 3.0)
            window_size: 통계 계산용 윈도우 크기
        """
        self.threshold = threshold
        self.window_size = window_size
        self.history: List[float] = []
    
    def fit(self, values: np.ndarray):
        """
        모델 학습 (히스토리 데이터로 통계 계산)
        
        Args:
            values: 학습용 값 배열
        """
        self.history = values.tolist()[-self.window_size:]
        logger.debug(f"Z-score 탐지기 학습 완료: {len(self.history)}개 샘플")
    
    def predict(self, value: float) -> Tuple[bool, float]:
        """
        단일 값에 대한 이상 여부 예측
        
        Args:
            value: 예측할 값
            
        Returns:
            (이상 여부, Z-score)
        """
        if len(self.history) < 2:
            self.history.append(value)
            return False, 0.0
        
        # 통계 계산
        mean = np.mean(self.history)
        std = np.std(self.history)
        
        if std == 0:
            self.history.append(value)
            return False, 0.0
        
        # Z-score 계산
        z_score = abs((value - mean) / std)
        
        # 이상 여부 판단
        is_anomaly = z_score > self.threshold
        
        # 히스토리 업데이트
        self.history.append(value)
        if len(self.history) > self.window_size:
            self.history.pop(0)
        
        return is_anomaly, z_score
    
    def predict_batch(self, values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        배치 값에 대한 이상 여부 예측
        
        Args:
            values: 예측할 값 배열
            
        Returns:
            (이상 여부 배열, Z-score 배열)
        """
        anomalies = np.zeros(len(values), dtype=bool)
        z_scores = np.zeros(len(values))
        
        for i, value in enumerate(values):
            is_anomaly, z_score = self.predict(value)
            anomalies[i] = is_anomaly
            z_scores[i] = z_score
        
        return anomalies, z_scores
    
    def detect(
        self,
        features: Dict[str, Any],
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        특징 딕셔너리로부터 이상 탐지
        
        Args:
            features: 특징 딕셔너리
            feature_names: 탐지할 특징 이름 리스트 (None이면 자동 감지)
            
        Returns:
            탐지 결과 딕셔너리
        """
        if feature_names is None:
            feature_names = [k for k in features.keys() if isinstance(features[k], (int, float))]
        
        results = {
            "is_anomaly": False,
            "anomaly_score": 0.0,
            "details": {}
        }
        
        max_z_score = 0.0
        anomaly_count = 0
        
        for feature_name in feature_names:
            if feature_name not in features:
                continue
            
            value = features[feature_name]
            if not isinstance(value, (int, float)):
                continue
            
            is_anomaly, z_score = self.predict(value)
            
            results["details"][feature_name] = {
                "is_anomaly": is_anomaly,
                "z_score": z_score,
                "value": value
            }
            
            if is_anomaly:
                anomaly_count += 1
            
            max_z_score = max(max_z_score, abs(z_score))
        
        # 전체 이상 여부 판단 (하나라도 이상이면 이상)
        results["is_anomaly"] = anomaly_count > 0
        results["anomaly_score"] = max_z_score / self.threshold  # 정규화된 점수
        
        return results

