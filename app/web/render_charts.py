"""
차트 렌더링 모듈
Plotly 차트 생성 및 렌더링 함수들
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def plot_response_time(df: pd.DataFrame, max_points: int = 500):
    """Response Time 차트 생성"""
    if "response_time" not in df.columns or len(df) == 0:
        return None
    
    fig = go.Figure()
    
    # 정상 데이터
    if "status_code" in df.columns:
        normal_mask = df["status_code"].apply(lambda x: isinstance(x, (int, float)) and x < 400)
    else:
        normal_mask = pd.Series([True] * len(df))
    
    if normal_mask.any():
        fig.add_trace(go.Scatter(
            x=df[normal_mask].index,
            y=df[normal_mask]["response_time"],
            mode='lines+markers',
            name='정상',
            line=dict(color='blue', width=1),
            marker=dict(size=4)
        ))
    
    # 에러 데이터
    if "status_code" in df.columns:
        error_mask = df["status_code"].apply(lambda x: isinstance(x, (int, float)) and x >= 400)
    else:
        error_mask = pd.Series([False] * len(df))
    
    if error_mask.any():
        fig.add_trace(go.Scatter(
            x=df[error_mask].index,
            y=df[error_mask]["response_time"],
            mode='markers',
            name='에러',
            marker=dict(color='red', size=12, symbol='x', line=dict(width=2, color='darkred')),
            text=df[error_mask]["status_code"].astype(str) if "status_code" in df.columns else None,
            hovertemplate='Status: %{text}<br>Response Time: %{y:.2f} ms<extra></extra>'
        ))
    
    fig.update_layout(
        height=300,
        xaxis_title="Time",
        yaxis_title="Response Time (ms)",
        showlegend=True,
        hovermode='x unified'
    )
    
    return fig


def plot_cpu_usage(df: pd.DataFrame):
    """CPU Usage 차트 생성"""
    if "cpu_usage" not in df.columns or len(df) == 0:
        return None
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["cpu_usage"],
        mode='lines',
        name='CPU Usage',
        line=dict(color='green', width=1)
    ))
    fig.update_layout(
        height=300,
        xaxis_title="Time",
        yaxis_title="CPU Usage (%)",
        showlegend=True
    )
    
    return fig


def render_recent_status_codes(recent_events: list, max_display: int = 5):
    """최근 상태 코드 표시"""
    if not recent_events:
        return
    
    st.caption("**최근 상태 코드:**")
    status_display = []
    for event in reversed(recent_events[-max_display:]):
        status = event.get("status_code", "-")
        endpoint = event.get("endpoint", "unknown")
        status_display.append(f"{status} - {endpoint[:50]}")
    st.text("\n".join(status_display))

