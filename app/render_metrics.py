"""
메트릭 렌더링 모듈
RPS, Error Rate, Status, Anomaly Score 등 메트릭 표시
"""
import streamlit as st
import numpy as np


def render_main_metrics(features: dict, data_list: list, anomaly_buffer: list):
    """주요 메트릭 렌더링"""
    col3, col4, col5, col6 = st.columns(4)
    
    with col3:
        if features:
            rps = features.get('rps', 0)
            st.metric("RPS", f"{rps:.2f}", delta=f"{rps:.2f}/sec" if rps > 0 else None)
        else:
            st.metric("RPS", "0")
    
    with col4:
        if features:
            error_rate = features.get('error_rate', 0) * 100
            delta_color = "inverse" if error_rate > 50 else "normal"
            st.metric(
                "Error Rate",
                f"{error_rate:.2f}%",
                delta=f"{error_rate:.1f}%" if error_rate > 0 else None,
                delta_color=delta_color
            )
        else:
            st.metric("Error Rate", "0%")
    
    with col5:
        render_status_metric(data_list)
    
    with col6:
        render_anomaly_score(anomaly_buffer)


def render_status_metric(data_list: list):
    """Status 메트릭 렌더링"""
    if len(data_list) > 0:
        latest_event = data_list[-1]
        status_code = latest_event.get("status_code", 200)
        
        # 타입 체크 및 이전 상태와 비교
        if isinstance(status_code, (int, float)):
            if len(data_list) > 1:
                prev_status = data_list[-2].get("status_code", 200)
                if isinstance(prev_status, (int, float)):
                    delta = status_code - prev_status
                else:
                    delta = None
            else:
                delta = None
            st.metric("Status", int(status_code), delta=int(delta) if delta is not None else None)
        else:
            st.metric("Status", str(status_code))
    else:
        st.metric("Status", "-")


def render_anomaly_score(anomaly_buffer: list):
    """Anomaly Score 메트릭 렌더링"""
    if len(anomaly_buffer) > 0:
        latest_anomaly = anomaly_buffer[-1]
        score = latest_anomaly.get("anomaly_score", latest_anomaly.get("score", 0.0))
        delta_color = "inverse" if score > 0.7 else "normal"
        st.metric(
            "Anomaly Score",
            f"{score:.2f}",
            delta=f"{score:.2f}" if score > 0 else None,
            delta_color=delta_color
        )
    else:
        st.metric("Anomaly Score", "0.00")


def render_statistics(recent_events: list):
    """통계 정보 렌더링"""
    if len(recent_events) == 0:
        return
    
    st.markdown("---")
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        total_requests = len(recent_events)
        st.metric("총 요청 수", total_requests)
    
    with col_stat2:
        error_count = sum(
            1 for e in recent_events
            if isinstance(e.get("status_code"), (int, float)) and e.get("status_code", 200) >= 400
        )
        st.metric("에러 수", error_count)
    
    with col_stat3:
        response_times = [
            e.get("response_time", 0) for e in recent_events
            if isinstance(e.get("response_time"), (int, float))
        ]
        if response_times:
            avg_response_time = np.mean(response_times)
            st.metric("평균 응답시간", f"{avg_response_time:.2f}ms")
        else:
            st.metric("평균 응답시간", "0ms")
    
    with col_stat4:
        response_times = [
            e.get("response_time", 0) for e in recent_events
            if isinstance(e.get("response_time"), (int, float))
        ]
        if response_times:
            max_response_time = max(response_times)
            st.metric("최대 응답시간", f"{max_response_time:.2f}ms")
        else:
            st.metric("최대 응답시간", "0ms")

