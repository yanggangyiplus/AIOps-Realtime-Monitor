"""
설정 파일 로더 모듈
YAML 설정 파일을 로드하고 관리합니다.
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """설정 파일을 로드하고 관리하는 클래스"""
    
    def __init__(self, config_dir: str = None):
        """
        ConfigLoader 초기화
        
        Args:
            config_dir: 설정 파일 디렉토리 경로 (기본값: 프로젝트 루트의 configs/)
        """
        if config_dir is None:
            # 프로젝트 루트 기준으로 configs 디렉토리 찾기
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent
            config_dir = project_root / "configs"
        
        self.config_dir = Path(config_dir)
        self._configs: Dict[str, Dict[str, Any]] = {}
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """
        특정 설정 파일을 로드합니다.
        
        Args:
            config_name: 설정 파일 이름 (확장자 제외, 예: "config_stream")
            
        Returns:
            설정 딕셔너리
        """
        if config_name in self._configs:
            return self._configs[config_name]
        
        config_path = self.config_dir / f"{config_name}.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self._configs[config_name] = config
        return config
    
    def get_stream_config(self) -> Dict[str, Any]:
        """스트림 설정을 반환합니다."""
        return self.load_config("config_stream")
    
    def get_anomaly_config(self) -> Dict[str, Any]:
        """이상 탐지 설정을 반환합니다."""
        return self.load_config("config_anomaly")
    
    def get_dashboard_config(self) -> Dict[str, Any]:
        """대시보드 설정을 반환합니다."""
        return self.load_config("config_dashboard")


# 전역 설정 로더 인스턴스
_config_loader = None


def get_config_loader() -> ConfigLoader:
    """전역 설정 로더 인스턴스를 반환합니다."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader

