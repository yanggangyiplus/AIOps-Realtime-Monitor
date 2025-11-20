"""
사이드바 컨트롤 모듈
Streamlit 사이드바 UI 및 제어 로직
"""
import streamlit as st


def render_sidebar(max_points: int = 500, update_interval: float = 1.0):
    """사이드바 렌더링"""
    with st.sidebar:
        st.header("설정")
        
        # 수집 모드 선택
        render_mode_selection()
        
        # HTTP 모드 설정
        if st.session_state.stream_mode == "http":
            render_http_settings()
        
        st.markdown("---")
        
        # 스트림 제어
        render_stream_controls()
        
        st.markdown("---")
        
        # 상태 표시
        render_status_display()
        
        st.markdown("---")
        
        # 차트 설정
        max_points, update_interval = render_chart_settings()
    
    return max_points, update_interval


def render_mode_selection():
    """수집 모드 선택"""
    st.subheader("수집 모드")
    stream_mode = st.selectbox(
        "모드 선택",
        ["mock", "http"],
        index=1 if st.session_state.stream_mode == "http" else 0,
        disabled=st.session_state.is_running,
        key="mode_select"
    )
    st.session_state.stream_mode = stream_mode


def render_http_settings():
    """HTTP 설정"""
    st.markdown("---")
    st.subheader("HTTP 설정")
    
    # 메인 URL 입력
    main_url = st.text_input(
        "메인 모니터링 URL",
        value=st.session_state.http_urls[0] if st.session_state.http_urls else "https://httpbin.org/status/200",
        disabled=st.session_state.is_running,
        key="main_url_input",
        help="예: https://httpbin.org/status/500"
    )
    
    if main_url and main_url.strip():
        if st.session_state.http_urls and len(st.session_state.http_urls) > 0:
            st.session_state.http_urls[0] = main_url.strip()
        else:
            st.session_state.http_urls = [main_url.strip()]
    
    # 추가 URL 입력
    st.markdown("**추가 URL:**")
    additional_url = st.text_input(
        "URL 입력",
        key="additional_url_input",
        disabled=st.session_state.is_running,
        placeholder="https://httpbin.org/status/503"
    )
    
    col_add1, col_add2 = st.columns(2)
    with col_add1:
        if st.button("추가", key="add_url_btn", disabled=st.session_state.is_running or not additional_url, use_container_width=True):
            url_list = list(st.session_state.http_urls) if isinstance(st.session_state.http_urls, list) else [st.session_state.http_urls]
            url_to_add = additional_url.strip()
            if url_to_add and url_to_add not in url_list:
                url_list.append(url_to_add)
                st.session_state.http_urls = url_list
                st.success(f"추가됨: {url_to_add}")
                st.rerun()
            elif url_to_add in url_list:
                st.warning("이미 존재하는 URL입니다.")
    
    with col_add2:
        if st.button("초기화", key="reset_urls_btn", disabled=st.session_state.is_running, use_container_width=True):
            st.session_state.http_urls = ["https://httpbin.org/status/200"]
            st.info("URL 목록 초기화됨")
            st.rerun()
    
    # URL 목록 표시
    render_url_list()
    
    # 폴링 간격
    st.session_state.http_interval = st.slider(
        "폴링 간격 (초)",
        0.5, 10.0, st.session_state.http_interval,
        disabled=st.session_state.is_running,
        key="interval_slider"
    )


def render_url_list():
    """URL 목록 표시"""
    st.markdown("---")
    st.write("**모니터링 URL 목록:**")
    url_list = list(st.session_state.http_urls) if isinstance(st.session_state.http_urls, list) else [st.session_state.http_urls]
    url_list = [url for url in url_list if url and url.strip()]
    
    if url_list:
        for i, url in enumerate(url_list):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{i+1}. {url}")
            with col2:
                if len(url_list) > 1 and st.button("제거", key=f"remove_{i}", disabled=st.session_state.is_running):
                    url_list.pop(i)
                    st.session_state.http_urls = url_list
                    st.rerun()
    else:
        st.info("URL이 없습니다.")


def render_stream_controls():
    """스트림 제어"""
    col_start, col_stop, col_reset = st.columns(3)
    with col_start:
        if st.button("시작", disabled=st.session_state.is_running, use_container_width=True):
            st.session_state.is_running = True
            st.session_state.last_poll_time = 0
            st.session_state.poll_counter = 0
            st.success("스트림 시작됨")
            st.rerun()
    
    with col_stop:
        if st.button("중지", disabled=not st.session_state.is_running, use_container_width=True):
            st.session_state.is_running = False
            st.info("스트림 중지됨 (데이터는 유지됩니다)")
            st.rerun()
    
    with col_reset:
        if st.button("데이터 초기화", disabled=st.session_state.is_running, use_container_width=True):
            st.session_state.data_buffer.clear()
            st.session_state.anomaly_buffer.clear()
            st.session_state.window_manager.clear()
            st.session_state.poll_counter = 0
            st.warning("데이터가 초기화되었습니다")
            st.rerun()


def render_status_display():
    """상태 표시"""
    st.subheader("상태")
    st.write(f"스트림: {'실행 중' if st.session_state.is_running else '중지됨'}")
    st.write(f"버퍼: {len(st.session_state.data_buffer)}개")
    st.write(f"알림: {len(st.session_state.anomaly_buffer)}개")
    if st.session_state.is_running:
        st.write(f"폴링 횟수: {st.session_state.poll_counter}회")


def render_chart_settings():
    """차트 설정"""
    st.subheader("차트 설정")
    max_points = st.slider("표시 데이터 포인트", 100, 1000, 500, key="max_points_slider")
    update_interval = st.slider("업데이트 간격 (초)", 0.5, 5.0, 1.0, key="update_interval_slider")
    return max_points, update_interval

