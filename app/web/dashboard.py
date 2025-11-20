"""
AIOps Real-time Monitor Dashboard
Streamlit 기반 실시간 이상 탐지 대시보드 (리팩토링 버전)
"""
import streamlit as st
import pandas as pd
import time
import requests
from datetime import datetime
import psutil

# 프로젝트 모듈 임포트
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.web.state_manager import init_session_state
from app.web.controls_sidebar import render_sidebar
from app.web.render_charts import plot_response_time, plot_cpu_usage, render_recent_status_codes
from app.web.render_metrics import render_main_metrics, render_statistics
from app.web.render_alerts import render_alerts_panel

from src.processing import Preprocessor, WindowManager
from src.feature import FeatureEngineer
from src.anomaly.comprehensive_detector import ComprehensiveAnomalyDetector
from src.alert import AlertManager

# 페이지 설정
st.set_page_config(
    page_title="AIOps Real-time Monitor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
init_session_state()


def poll_http_urls():
    """HTTP URL들을 폴링하여 데이터 수집 (메인 스레드에서 실행)"""
    if not st.session_state.is_running or st.session_state.stream_mode != "http":
        return
    
    current_time = time.time()
    # 폴링 간격 체크
    if current_time - st.session_state.last_poll_time < st.session_state.http_interval:
        return
    
    st.session_state.last_poll_time = current_time
    
    urls = st.session_state.http_urls if isinstance(st.session_state.http_urls, list) else [st.session_state.http_urls]
    urls = [url for url in urls if url and url.strip()]
    
    if not urls:
        return
    
    for url in urls:
        try:
            start_time = time.time()
            response = requests.get(url, timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            # 시스템 메트릭
            cpu_usage = psutil.cpu_percent(interval=None)
            memory_usage = psutil.virtual_memory().percent
            
            event = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "endpoint": url,
                "status_code": response.status_code,
                "response_time": response_time,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "method": "GET"
            }
            
            # 데이터 버퍼에 추가
            st.session_state.data_buffer.append(event)
            st.session_state.window_manager.add_event(event)
            
            # 이상 탐지
            recent_events = st.session_state.window_manager.get_recent_events(count=100)
            if len(recent_events) >= 1:
                comprehensive_result = st.session_state.comprehensive_detector.detect(event, recent_events)
                
                if comprehensive_result.get("is_anomaly", False):
                    alert = st.session_state.alert_manager.create_alert(comprehensive_result, event)
                    if alert:
                        st.session_state.anomaly_buffer.append({
                            "timestamp": alert.timestamp,
                            "level": alert.level,
                            "message": alert.message,
                            "score": comprehensive_result.get("anomaly_score", 0.0),
                            "is_anomaly": True,
                            "anomaly_type": comprehensive_result.get("anomaly_type", "unknown"),
                            "severity": comprehensive_result.get("severity", "warning")
                        })
            
            st.session_state.poll_counter += 1
            
        except Exception as e:
            # 에러 이벤트 생성
            error_event = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "endpoint": url,
                "status_code": 0,
                "response_time": 0.0,
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "error": str(e)
            }
            st.session_state.data_buffer.append(error_event)


def render_test_section():
    """테스트 섹션 렌더링"""
    st.markdown("---")
    st.subheader("테스트")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Mock 데이터 추가", use_container_width=True):
            test_event = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "endpoint": "/test",
                "status_code": 200,
                "response_time": 100.0,
                "cpu_usage": 50.0,
                "memory_usage": 60.0
            }
            st.session_state.data_buffer.append(test_event)
            st.session_state.window_manager.add_event(test_event)
            st.success("테스트 데이터 추가됨")
            st.rerun()
    
    with col2:
        if st.button("HTTP 테스트", use_container_width=True):
            try:
                test_url = st.session_state.http_urls[0] if st.session_state.http_urls else "https://httpbin.org/status/200"
                response = requests.get(test_url, timeout=5)
                test_event = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "endpoint": test_url,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds() * 1000,
                    "cpu_usage": 50.0,
                    "memory_usage": 60.0
                }
                st.session_state.data_buffer.append(test_event)
                st.session_state.window_manager.add_event(test_event)
                st.success(f"HTTP 테스트 성공: 상태 {response.status_code}")
                st.rerun()
            except Exception as e:
                st.error(f"HTTP 테스트 실패: {e}")


def render_data_export():
    """데이터 내보내기 섹션 렌더링"""
    if len(st.session_state.data_buffer) == 0:
        return
    
    st.markdown("---")
    st.subheader("💾 데이터 내보내기")
    
    export_col1, export_col2, export_col3 = st.columns(3)
    
    with export_col1:
        df_all = pd.DataFrame(list(st.session_state.data_buffer))
        csv_all = df_all.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 전체 데이터 (CSV)",
            data=csv_all,
            file_name=f"aiops_full_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
            help="수집된 모든 데이터를 CSV로 다운로드",
            key="main_csv_download"
        )
    
    with export_col2:
        import json
        json_all = json.dumps(list(st.session_state.data_buffer), indent=2, ensure_ascii=False, default=str)
        st.download_button(
            label="📥 전체 데이터 (JSON)",
            data=json_all.encode('utf-8'),
            file_name=f"aiops_full_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
            help="수집된 모든 데이터를 JSON으로 다운로드",
            key="main_json_download"
        )
    
    with export_col3:
        if st.button("📊 통계 리포트 생성", use_container_width=True):
            stats_report = {
                "생성 시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "총 데이터 포인트": len(st.session_state.data_buffer),
                "모니터링 URL": st.session_state.http_urls if isinstance(st.session_state.http_urls, list) else [st.session_state.http_urls],
                "통계": {}
            }
            
            recent_events = list(st.session_state.data_buffer)[-100:]
            if recent_events:
                import numpy as np
                stats_report["통계"] = {
                    "총 요청 수": len(recent_events),
                    "에러 수": sum(1 for e in recent_events if isinstance(e.get("status_code"), (int, float)) and e.get("status_code", 200) >= 400),
                    "평균 응답시간": float(np.mean([e.get("response_time", 0) for e in recent_events if isinstance(e.get("response_time"), (int, float))])),
                    "최대 응답시간": float(max([e.get("response_time", 0) for e in recent_events if isinstance(e.get("response_time"), (int, float))], default=0)),
                    "최소 응답시간": float(min([e.get("response_time", 0) for e in recent_events if isinstance(e.get("response_time"), (int, float))], default=0))
                }
                
                status_counts = {}
                for e in recent_events:
                    status = e.get("status_code", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                stats_report["통계"]["상태 코드별 분포"] = status_counts
            
            import json
            report_json = json.dumps(stats_report, indent=2, ensure_ascii=False, default=str)
            st.download_button(
                label="📥 통계 리포트 다운로드",
                data=report_json.encode('utf-8'),
                file_name=f"aiops_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
                key="main_report_download"
            )
    
    # 이상 탐지 결과 다운로드
    if len(st.session_state.anomaly_buffer) > 0:
        st.markdown("**🚨 이상 탐지 결과:**")
        anomaly_col1, anomaly_col2 = st.columns(2)
        
        with anomaly_col1:
            anomaly_df = pd.DataFrame(list(st.session_state.anomaly_buffer))
            anomaly_csv = anomaly_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 이상 탐지 결과 (CSV)",
                data=anomaly_csv,
                file_name=f"aiops_anomalies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="main_anomaly_csv_download"
            )
        
        with anomaly_col2:
            import json
            anomaly_json = json.dumps(list(st.session_state.anomaly_buffer), indent=2, ensure_ascii=False, default=str)
            st.download_button(
                label="📥 이상 탐지 결과 (JSON)",
                data=anomaly_json.encode('utf-8'),
                file_name=f"aiops_anomalies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
                key="main_anomaly_json_download"
            )


def main():
    """메인 대시보드 함수"""
    st.title("🔍 AIOps Real-time Monitor")
    st.markdown("---")
    
    # 사이드바 렌더링
    max_points, update_interval = render_sidebar()
    
    # HTTP 폴링 실행
    if st.session_state.is_running and st.session_state.stream_mode == "http":
        poll_http_urls()
    
    # 메인 영역
    if not st.session_state.is_running:
        # 스트림이 중지되었지만 데이터가 있으면 표시
        if len(st.session_state.data_buffer) == 0:
            st.info("사이드바에서 '시작' 버튼을 클릭하여 모니터링을 시작하세요")
            render_test_section()
            return
        
        # 스트림이 중지되었지만 데이터가 있으면 표시
        st.info("스트림이 중지되었습니다. 기존 데이터가 표시됩니다. 새로 시작하려면 '시작' 버튼을 클릭하세요.")
    
    # 데이터가 없는 경우 (스트림 실행 중일 때만)
    if len(st.session_state.data_buffer) == 0 and st.session_state.is_running:
        st.warning("데이터가 수집되지 않고 있습니다. 잠시 기다려주세요...")
        time.sleep(update_interval)
        st.rerun()
        return
    
    # 데이터가 없고 스트림도 중지된 경우
    if len(st.session_state.data_buffer) == 0:
        return
    
    # 데이터 준비 (한 번만 계산)
    data_list = list(st.session_state.data_buffer)
    recent_events_100 = data_list[-100:] if len(data_list) >= 100 else data_list
    recent_events_10 = data_list[-10:] if len(data_list) >= 10 else data_list
    
    # DataFrame 변환 (한 번만)
    df = pd.DataFrame(data_list[-max_points:])
    
    # 특징 추출 (한 번만)
    features = None
    if len(recent_events_100) >= 1:
        features = st.session_state.feature_engineer.extract_features(recent_events_100)
    
    # 실시간 차트
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Response Time & Status")
        fig_response = plot_response_time(df, max_points)
        if fig_response:
            st.plotly_chart(fig_response, use_container_width=True)
            render_recent_status_codes(recent_events_10)
    
    with col2:
        st.subheader("CPU Usage")
        fig_cpu = plot_cpu_usage(df)
        if fig_cpu:
            st.plotly_chart(fig_cpu, use_container_width=True)
    
    # 메트릭 렌더링
    render_main_metrics(features, data_list, list(st.session_state.anomaly_buffer))
    
    # 통계 정보
    render_statistics(recent_events_100)
    
    # 데이터 내보내기
    render_data_export()
    
    st.markdown("---")
    
    # 알림 패널
    render_alerts_panel(data_list, list(st.session_state.anomaly_buffer))
    
    # 자동 새로고침 (스트림이 실행 중일 때만)
    if st.session_state.is_running:
        time.sleep(update_interval)
        st.rerun()


if __name__ == "__main__":
    main()

