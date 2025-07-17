"""
Core logging setup for GreekSTT ASR Service
Simple logging configuration for academic use
"""
import logging
from app.core.config import config


def setup_basic_logging():
    """
    Setup basic logging configuration for academic research
    """
    log_level = config.LOG_LEVEL
    
    log_format = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        force=True
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"ASR Service logging initialized: Level={log_level}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Simple logger factory for academic use
    """
    return logging.getLogger(name)


logger = setup_basic_logging()