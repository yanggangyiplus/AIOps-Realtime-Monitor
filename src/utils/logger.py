"""
로깅 유틸리티 모듈
통일된 로깅 인터페이스를 제공합니다.
"""
import sys
from loguru import logger
from pathlib import Path


def setup_logger(
    log_level: str = "INFO",
    log_file: str = None,
    rotation: str = "10 MB",
    retention: str = "7 days"
):
    """
    로거를 설정합니다.
    
    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (None이면 파일 로깅 비활성화)
        rotation: 로그 파일 회전 크기
        retention: 로그 파일 보관 기간
    """
    # 기본 로거 제거
    logger.remove()
    
    # 콘솔 출력 설정
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # 파일 출력 설정 (선택적)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            rotation=rotation,
            retention=retention,
            encoding="utf-8"
        )
    
    return logger


# 기본 로거 설정
setup_logger()

