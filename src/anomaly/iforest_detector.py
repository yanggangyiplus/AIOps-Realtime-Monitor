"""
Isolation Forest 기반 이상 탐지기
머신러닝 기반 이상 탐지를 수행합니다.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger


class IsolationForestDetector:
    """Isolation Forest 기반 이상 탐지기"""
    
    def __init__(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100,
        max_samples: int = 256
    ):
        """
        IsolationForestDetector 초기화
        
        Args:
            contamination: 이상 비율 추정값 (0.0 ~ 0.5)
            n_estimators: 트리 개수
            max_samples: 각 트리에서 사용할 최대 샘플 수
        """
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.model: Optional[IsolationForest] = None
        self.feature_names: List[str] = []
        self.is_fitted = False
    
    def fit(self, features_list: List[Dict[str, Any]], feature_names: Optional[List[str]] = None):
        """
        모델 학습
        
        Args:
            features_list: 특징 딕셔너리 리스트
            feature_names: 사용할 특징 이름 리스트 (None이면 자동 선택)
        """
        if not features_list:
            logger.warning("학습 데이터가 비어있습니다.")
            return
        
        # 특징 이름 결정
        if feature_names is None:
            # 첫 번째 샘플에서 수치형 특징 추출
            sample = features_list[0]
            feature_names = [
                k for k, v in sample.items()
                if isinstance(v, (int, float)) and k not in ["timestamp", "is_error"]
            ]
        
        self.feature_names = feature_names
        
        # 특징 행렬 생성
        X = []
        for features in features_list:
            row = [features.get(name, 0.0) for name in self.feature_names]
            X.append(row)
        
        X = np.array(X)
        
        if len(X) == 0:
            logger.warning("유효한 특징이 없습니다.")
            return
        
        # 모델 학습
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            max_samples=min(self.max_samples, len(X)),
            random_state=42
        )
        
        self.model.fit(X)
        self.is_fitted = True
        
        logger.info(f"Isolation Forest 학습 완료: {len(X)}개 샘플, {len(self.feature_names)}개 특징")
    
    def predict(self, features: Dict[str, Any]) -> Tuple[bool, float]:
        """
        단일 특징에 대한 이상 여부 예측
        
        Args:
            features: 특징 딕셔너리
            
        Returns:
            (이상 여부, 이상 점수)
        """
        if not self.is_fitted or self.model is None:
            logger.warning("모델이 학습되지 않았습니다.")
            return False, 0.0
        
        # 특징 벡터 생성
        X = np.array([[features.get(name, 0.0) for name in self.feature_names]])
        
        # 예측
        prediction = self.model.predict(X)[0]
        score = self.model.score_samples(X)[0]
        
        # Isolation Forest는 -1이 이상, 1이 정상
        is_anomaly = prediction == -1
        
        # 점수를 0~1 범위로 정규화 (낮을수록 이상)
        anomaly_score = 1.0 / (1.0 + np.exp(score))  # sigmoid 변환
        
        return is_anomaly, anomaly_score
    
    def predict_batch(self, features_list: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """
        배치 특징에 대한 이상 여부 예측
        
        Args:
            features_list: 특징 딕셔너리 리스트
            
        Returns:
            (이상 여부 배열, 이상 점수 배열)
        """
        if not self.is_fitted or self.model is None:
            logger.warning("모델이 학습되지 않았습니다.")
            return np.zeros(len(features_list), dtype=bool), np.zeros(len(features_list))
        
        # 특징 행렬 생성
        X = np.array([
            [features.get(name, 0.0) for name in self.feature_names]
            for features in features_list
        ])
        
        # 예측
        predictions = self.model.predict(X)
        scores = self.model.score_samples(X)
        
        # 이상 여부 변환
        anomalies = predictions == -1
        
        # 점수 정규화
        anomaly_scores = 1.0 / (1.0 + np.exp(scores))
        
        return anomalies, anomaly_scores
    
    def detect(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        특징 딕셔너리로부터 이상 탐지
        
        Args:
            features: 특징 딕셔너리
            
        Returns:
            탐지 결과 딕셔너리
        """
        is_anomaly, anomaly_score = self.predict(features)
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": float(anomaly_score),
            "method": "isolation_forest"
        }

