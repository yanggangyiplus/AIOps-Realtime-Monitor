"""
이상 탐지 관리자
여러 탐지 방법을 통합 관리하고 조합합니다.
"""
from typing import Dict, Any, List, Optional
from loguru import logger

from .zscore_detector import ZScoreDetector
from .iforest_detector import IsolationForestDetector
from .changepoint import ChangePointDetector
from ..utils.config import get_config_loader


class DetectorManager:
    """이상 탐지 관리자"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        DetectorManager 초기화
        
        Args:
            config: 이상 탐지 설정 딕셔너리 (None이면 설정 파일에서 로드)
        """
        if config is None:
            config_loader = get_config_loader()
            config = config_loader.get_anomaly_config()
        
        self.config = config
        self.anomaly_config = config.get("anomaly", {})
        self.method = self.anomaly_config.get("method", "hybrid")
        
        # 탐지기 초기화
        self.detectors = {}
        self._initialize_detectors()
        
        # 특징 이름
        self.feature_names = self.anomaly_config.get("features", [])
        
        # 학습 데이터 저장
        self.training_data: List[Dict[str, Any]] = []
        self.min_training_samples = 50
    
    def _initialize_detectors(self):
        """설정에 따라 탐지기 초기화"""
        # Z-score 탐지기
        zscore_config = self.anomaly_config.get("zscore", {})
        self.detectors["zscore"] = ZScoreDetector(
            threshold=zscore_config.get("threshold", 3.0),
            window_size=zscore_config.get("window_size", 100)
        )
        
        # Isolation Forest 탐지기
        iforest_config = self.anomaly_config.get("isolation_forest", {})
        self.detectors["isolation_forest"] = IsolationForestDetector(
            contamination=iforest_config.get("contamination", 0.1),
            n_estimators=iforest_config.get("n_estimators", 100),
            max_samples=iforest_config.get("max_samples", 256)
        )
        
        # Change-point 탐지기
        changepoint_config = self.anomaly_config.get("changepoint", {})
        if changepoint_config.get("enabled", True):
            self.detectors["changepoint"] = ChangePointDetector(
                sensitivity=changepoint_config.get("sensitivity", 0.3),
                min_change=changepoint_config.get("min_change", 0.2),
                window_size=50
            )
    
    def add_training_data(self, features: Dict[str, Any]):
        """
        학습 데이터 추가
        
        Args:
            features: 특징 딕셔너리
        """
        self.training_data.append(features.copy())
        
        # 최소 샘플 수에 도달하면 학습
        if len(self.training_data) >= self.min_training_samples:
            if not self.detectors["isolation_forest"].is_fitted:
                self._train_detectors()
    
    def _train_detectors(self):
        """탐지기 학습"""
        if len(self.training_data) < self.min_training_samples:
            logger.warning(f"학습 데이터가 부족합니다: {len(self.training_data)}/{self.min_training_samples}")
            return
        
        # Isolation Forest 학습
        if "isolation_forest" in self.detectors:
            try:
                self.detectors["isolation_forest"].fit(
                    self.training_data,
                    feature_names=self.feature_names if self.feature_names else None
                )
                logger.info("Isolation Forest 학습 완료")
            except Exception as e:
                logger.error(f"Isolation Forest 학습 실패: {e}")
        
        # Z-score 탐지기는 실시간으로 학습되므로 별도 학습 불필요
        
        logger.info(f"탐지기 학습 완료: {len(self.training_data)}개 샘플")
    
    def detect(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        특징으로부터 이상 탐지
        
        Args:
            features: 특징 딕셔너리
            
        Returns:
            탐지 결과 딕셔너리
        """
        # 학습 데이터 추가
        self.add_training_data(features)
        
        results = {
            "is_anomaly": False,
            "anomaly_score": 0.0,
            "method": self.method,
            "details": {}
        }
        
        if self.method == "zscore":
            zscore_result = self.detectors["zscore"].detect(features, self.feature_names)
            results["is_anomaly"] = zscore_result["is_anomaly"]
            results["anomaly_score"] = zscore_result["anomaly_score"]
            results["details"]["zscore"] = zscore_result
        
        elif self.method == "isolation_forest":
            if self.detectors["isolation_forest"].is_fitted:
                iforest_result = self.detectors["isolation_forest"].detect(features)
                results["is_anomaly"] = iforest_result["is_anomaly"]
                results["anomaly_score"] = iforest_result["anomaly_score"]
                results["details"]["isolation_forest"] = iforest_result
            else:
                logger.warning("Isolation Forest가 아직 학습되지 않았습니다.")
        
        elif self.method == "hybrid":
            # Z-score와 Isolation Forest 조합
            zscore_result = self.detectors["zscore"].detect(features, self.feature_names)
            
            iforest_result = None
            if self.detectors["isolation_forest"].is_fitted:
                iforest_result = self.detectors["isolation_forest"].detect(features)
            
            # 조합 로직: 둘 중 하나라도 이상이면 이상
            is_anomaly = zscore_result["is_anomaly"]
            anomaly_score = zscore_result["anomaly_score"]
            
            if iforest_result:
                is_anomaly = is_anomaly or iforest_result["is_anomaly"]
                anomaly_score = max(anomaly_score, iforest_result["anomaly_score"])
            
            results["is_anomaly"] = is_anomaly
            results["anomaly_score"] = anomaly_score
            results["details"]["zscore"] = zscore_result
            if iforest_result:
                results["details"]["isolation_forest"] = iforest_result
        
        # Change-point 탐지 (별도로 수행)
        if "changepoint" in self.detectors:
            # 히스토리 데이터로부터 변화점 탐지
            if len(self.training_data) >= 100:
                # 최근 데이터 추출
                recent_features = self.training_data[-100:]
                
                # 특징별 값 리스트 생성
                feature_values = {}
                for feature_name in self.feature_names:
                    if feature_name in recent_features[0]:
                        feature_values[feature_name] = [
                            f.get(feature_name, 0.0) for f in recent_features
                        ]
                
                if feature_values:
                    changepoint_result = self.detectors["changepoint"].detect(feature_values)
                    results["details"]["changepoint"] = changepoint_result
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """탐지기 통계 정보 반환"""
        return {
            "method": self.method,
            "training_samples": len(self.training_data),
            "detectors": {
                name: {
                    "fitted": detector.is_fitted if hasattr(detector, "is_fitted") else True
                }
                for name, detector in self.detectors.items()
            }
        }

