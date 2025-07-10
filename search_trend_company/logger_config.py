import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logger(name="idnolab", log_level=logging.INFO):
    """
    로거 설정 함수
    
    Args:
        name (str): 로거 이름
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging.Logger: 설정된 로거 객체
    """
    
    # logs 디렉토리 생성
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 기존 핸들러가 있다면 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 파일 핸들러 설정 (로테이션)
    today = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f"idnolab_{today}.log")
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,  # 최대 5개 백업 파일
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 핸들러를 로거에 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name="idnolab"):
    """
    기존 로거를 가져오거나 새로 생성
    
    Args:
        name (str): 로거 이름
    
    Returns:
        logging.Logger: 로거 객체
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger = setup_logger(name)
    return logger 