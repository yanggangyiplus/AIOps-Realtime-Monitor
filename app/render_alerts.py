"""
알림 렌더링 모듈
알림 패널 UI 렌더링
"""
import streamlit as st


def render_alerts_panel(data_list: list, anomaly_buffer: list):
    """알림 패널 렌더링"""
    st.subheader("🚨 최근 알림")
    
    # HTTP 에러 알림
    render_http_errors(data_list)
    
    # ML 기반 이상 탐지 알림
    render_ml_anomalies(anomaly_buffer)
    
    # 정상 상태 표시
    if len(data_list) > 0:
        recent_events_20 = data_list[-20:] if len(data_list) >= 20 else data_list
        has_errors = any(
            isinstance(e.get("status_code"), (int, float)) and e.get("status_code", 200) >= 400
            for e in recent_events_20
        )
        has_anomalies = len([a for a in anomaly_buffer if a.get("is_anomaly", False)]) > 0
        
        if not has_errors and not has_anomalies:
            st.success("현재 모든 시스템이 정상 작동 중입니다")


def render_http_errors(data_list: list):
    """HTTP 에러 알림 렌더링"""
    if len(data_list) == 0:
        return
    
    recent_events_20 = data_list[-20:] if len(data_list) >= 20 else data_list
    error_events = [
        e for e in recent_events_20
        if isinstance(e.get("status_code"), (int, float)) and e.get("status_code", 200) >= 400
    ]
    
    if error_events:
        st.warning(f"최근 {len(error_events)}개의 HTTP 에러가 탐지되었습니다")
        
        # 상태 코드별 메시지
        status_messages = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            408: "Request Timeout",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout"
        }
        
        # 최근 에러 이벤트 표시
        for event in reversed(error_events[-5:]):  # 최근 5개만
            status_code = event.get("status_code", 0)
            endpoint = event.get("endpoint", "unknown")
            timestamp = event.get("timestamp", "unknown")
            status_msg = status_messages.get(status_code, f"HTTP {status_code}")
            severity = "CRITICAL" if status_code >= 500 else "WARNING"
            
            with st.container():
                st.markdown(f"**{severity}** - HTTP {status_code} {status_msg}")
                st.caption(f"Endpoint: {endpoint}")
                st.caption(f"Time: {timestamp}")
                st.markdown("---")


def render_ml_anomalies(anomaly_buffer: list):
    """ML 기반 이상 탐지 알림 렌더링"""
    if len(anomaly_buffer) == 0:
        return
    
    recent_anomalies = anomaly_buffer[-20:] if len(anomaly_buffer) >= 20 else anomaly_buffer
    anomaly_list = [a for a in recent_anomalies if a.get("is_anomaly", False)]
    
    if anomaly_list:
        st.markdown("**ML 기반 이상 탐지:**")
        for anomaly in reversed(anomaly_list[-5:]):  # 최근 5개만
            severity = anomaly.get("severity", anomaly.get("level", "info"))
            anomaly_type = anomaly.get("anomaly_type", "unknown")
            message = anomaly.get("message", f"{anomaly_type} 이상 탐지")
            score = anomaly.get("score", anomaly.get("anomaly_score", 0.0))
            
            st.markdown(f"**{severity.upper()}** - {message} (점수: {score:.2f})")
            st.caption(f"시간: {anomaly.get('timestamp', 'unknown')} | 유형: {anomaly_type}")
            st.markdown("---")

