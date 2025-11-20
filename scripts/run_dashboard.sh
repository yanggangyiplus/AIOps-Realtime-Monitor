#!/bin/bash

# AIOps Real-time Monitor 대시보드 실행 스크립트

# 프로젝트 루트 디렉토리로 이동
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

# 가상환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Streamlit 대시보드 실행
echo "AIOps Real-time Monitor 대시보드를 시작합니다..."
streamlit run app/web/dashboard.py --server.port 8501 --server.address localhost

