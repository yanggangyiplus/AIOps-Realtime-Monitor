"""
세션 상태 관리 모듈
Streamlit 세션 상태 초기화 및 관리
"""
import streamlit as st
from collections import deque
from queue import Queue
from src.processing import Preprocessor, WindowManager
from src.feature import FeatureEngineer
from src.anomaly import DetectorManager
from src.anomaly.comprehensive_detector import ComprehensiveAnomalyDetector
from src.alert import AlertManager
from src.utils.config import get_config_loader


def init_session_state():
    """세션 상태 초기화"""
    defaults = {
        "ingest_manager": None,
        "window_manager": WindowManager(window_size=500),
        "preprocessor": Preprocessor(),
        "feature_engineer": FeatureEngineer(),
        "detector_manager": None,
        "comprehensive_detector": ComprehensiveAnomalyDetector(),
        "alert_manager": AlertManager(),
        "is_running": False,
        "data_buffer": deque(maxlen=1000),
        "anomaly_buffer": deque(maxlen=500),
        "processing_thread": None,
        "event_queue": Queue(),
        "anomaly_queue": Queue(),
        "http_urls": ["https://httpbin.org/status/200"],
        "http_interval": 1.0,
        "stream_mode": "http",
        "last_poll_time": 0,
        "poll_counter": 0,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # DetectorManager 초기화
    if st.session_state.detector_manager is None:
        config_loader = get_config_loader()
        anomaly_config = config_loader.get_anomaly_config()
        st.session_state.detector_manager = DetectorManager(anomaly_config)
